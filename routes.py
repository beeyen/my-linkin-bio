from datetime import datetime
import logging

import requests
from bs4 import BeautifulSoup
from flask import Blueprint, current_app, flash, jsonify, redirect, render_template, request, url_for

from utils import is_duplicate_site_name, is_valid_url

logger = logging.getLogger(__name__)
main_blueprint = Blueprint("main", __name__)
links = []


@main_blueprint.get("/")
def home():
    sorted_links = sorted(links, key=lambda link: link["name"].lower())
    return render_template("index.html", links=sorted_links)


@main_blueprint.get("/recipes")
def recipes():
    """Display the collection of quick food recipes."""
    return render_template(
        "with-skills/recipes.html",
        recipes=current_app.config["RECIPES"],
        recipe_filters=current_app.config["RECIPE_FILTERS"],
        recipe_labels=current_app.config["RECIPE_LABELS"],
    )


@main_blueprint.get("/health")
def health_check():
    """Return the application health status and current server time."""
    return jsonify({"status": current_app.config["LABELS"]["health_ok"], "server_time": datetime.now().astimezone().isoformat()}), 200


def fetch_link_metadata(url):
    """Fetch Open Graph metadata and use fallbacks when it is unavailable."""
    labels = current_app.config["LABELS"]
    metadata = {"title": labels["not_available"], "description": labels["not_available"], "image_url": labels["not_available"]}
    try:
        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=5)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
    except requests.RequestException as error:
        logger.warning("Failed to fetch metadata for URL %s: %s", url, error)
        return metadata

    for field, property_name in (("title", "og:title"), ("description", "og:description"), ("image_url", "og:image")):
        tag = soup.find("meta", property=property_name)
        content = tag.get("content", "").strip() if tag else ""
        metadata[field] = content or labels["not_available"]
    return metadata


@main_blueprint.post("/add")
def add_link():
    labels = current_app.config["LABELS"]
    site_name = request.form["name"].strip()
    link_url = request.form["url"].strip()
    if not is_valid_url(link_url):
        logger.warning("Rejected invalid URL submitted for site %s: %s", site_name, link_url)
        flash(labels["invalid_url_warning"], "warning")
        return redirect(url_for("main.home"))
    if is_duplicate_site_name(site_name, links):
        logger.warning("A link with the site name %s already exists", site_name)
        flash(labels["duplicate_name_warning"].format(site_name=site_name), "warning")
        return redirect(url_for("main.home"))
    metadata = fetch_link_metadata(link_url)
    metadata_unavailable = all(value == labels["not_available"] for value in metadata.values())
    if metadata_unavailable:
        logger.warning("Metadata could not be retrieved for URL %s", link_url)
        flash(labels["metadata_warning"], "warning")
    links.append({"name": site_name, "url": link_url, "metadata_unavailable": metadata_unavailable, **metadata})
    logger.info("Successfully added link %s (%s)", site_name, link_url)
    return redirect(url_for("main.home"))


@main_blueprint.post("/delete")
def delete_link():
    link_url = request.form["url"]
    for link in links:
        if link["url"] == link_url:
            links.remove(link)
            break
    return redirect(url_for("main.home"))


@main_blueprint.post("/edit")
def edit_link():
    labels = current_app.config["LABELS"]
    original_url = request.form["original_url"]
    site_name = request.form["name"].strip()
    link_url = request.form["url"].strip()
    if not is_valid_url(link_url):
        logger.warning("Rejected invalid edited URL for site %s: %s", site_name, link_url)
        flash(labels["invalid_url_warning"], "warning")
        return redirect(url_for("main.home"))
    for link in links:
        if link["url"] == original_url:
            link["name"] = site_name
            link["url"] = link_url
            metadata = fetch_link_metadata(link["url"])
            link["metadata_unavailable"] = all(value == labels["not_available"] for value in metadata.values())
            link.update(metadata)
            break
    return redirect(url_for("main.home"))


@main_blueprint.get("/about")
def about():
    return render_template("about.html")


@main_blueprint.get("/contact")
def contact():
    return render_template("contact.html")
