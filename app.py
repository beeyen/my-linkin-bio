from datetime import datetime
import json
import logging
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from flask import Flask, flash, jsonify, redirect, render_template, request, url_for
from utils import is_duplicate_site_name, is_valid_url

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

configuration_path = Path(__file__).with_name("constants.json")
with configuration_path.open(encoding="utf-8") as configuration_file:
    configuration = json.load(configuration_file)

LABELS = configuration["LABELS"]
PAGE_NAMES = configuration["PAGE_NAMES"]

app = Flask(__name__, static_folder="statics")
app.config["SECRET_KEY"] = "dev-secret-key"
app.config["LABELS"] = LABELS
app.config["PAGE_NAMES"] = PAGE_NAMES
links = []


@app.route("/")
def home():
    sorted_links = sorted(links, key=lambda link: link["name"].lower())
    return render_template("index.html", links=sorted_links)


@app.get("/health")
def health_check():
    """Return the application health status and current server time."""
    return jsonify({
        "status": LABELS["health_ok"],
        "server_time": datetime.now().astimezone().isoformat(),
    }), 200


def fetch_link_metadata(url):
    """Fetch Open Graph metadata and use fallbacks when it is unavailable."""
    metadata = {
        "title": LABELS["not_available"],
        "description": LABELS["not_available"],
        "image_url": LABELS["not_available"],
    }
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
        metadata[field] = content or LABELS["not_available"]
    return metadata


@app.post("/add")
def add_link():
    site_name = request.form["name"].strip()
    link_url = request.form["url"].strip()
    if not is_valid_url(link_url):
        logger.warning("Rejected invalid URL submitted for site %s: %s", site_name, link_url)
        flash(LABELS["invalid_url_warning"], "warning")
        return redirect(url_for("home"))

    if is_duplicate_site_name(site_name, links):
        logger.warning("A link with the site name %s already exists", site_name)
        flash(LABELS["duplicate_name_warning"].format(site_name=site_name), "warning")
        return redirect(url_for("home"))

    metadata = fetch_link_metadata(link_url)
    metadata_unavailable = all(value == LABELS["not_available"] for value in metadata.values())
    if metadata_unavailable:
        logger.warning("Metadata could not be retrieved for URL %s", link_url)
        flash(LABELS["metadata_warning"], "warning")

    links.append({
        "name": site_name,
        "url": link_url,
        "metadata_unavailable": metadata_unavailable,
        **metadata,
    })
    logger.info("Successfully added link %s (%s)", site_name, link_url)
    return redirect(url_for("home"))


@app.post("/delete")
def delete_link():
    link_url = request.form["url"]
    for link in links:
        if link["url"] == link_url:
            links.remove(link)
            break
    return redirect(url_for("home"))


@app.post("/edit")
def edit_link():
    original_url = request.form["original_url"]
    for link in links:
        if link["url"] == original_url:
            link["name"] = request.form["name"]
            link["url"] = request.form["url"]
            metadata = fetch_link_metadata(link["url"])
            link["metadata_unavailable"] = all(value == LABELS["not_available"] for value in metadata.values())
            link.update(metadata)
            break
    return redirect(url_for("home"))


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/contact")
def contact():
    return render_template("contact.html")


@app.errorhandler(404)
def page_not_found(error):
    """Render the custom page for routes that do not exist."""
    return render_template("404.html"), 404


@app.errorhandler(500)
def internal_server_error(error):
    """Render the custom page for unexpected application errors."""
    return render_template("500.html"), 500


if __name__ == "__main__":
    app.run(debug=True)
