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

RECIPES = [
    {
        "name": "Creamy Tomato Pasta",
        "emoji": "🍝",
        "time": "25 min",
        "description": "A cozy weeknight pasta with a silky tomato cream sauce.",
        "ingredients": ["200g pasta", "1 cup tomato passata", "1/2 cup cream", "2 garlic cloves", "Parmesan"],
        "instructions": "Cook the pasta. Sauté garlic, add passata and cream, then toss with pasta and Parmesan.",
    },
    {
        "name": "Avocado Toast",
        "emoji": "🥑",
        "time": "10 min",
        "description": "Crispy toast topped with bright, creamy avocado and a poached egg.",
        "ingredients": ["2 slices sourdough", "1 ripe avocado", "2 eggs", "Lemon juice", "Chili flakes"],
        "instructions": "Toast the bread and mash avocado with lemon and salt. Top with a poached egg and chili flakes.",
    },
    {
        "name": "Honey Garlic Chicken",
        "emoji": "🍗",
        "time": "30 min",
        "description": "Golden chicken thighs glazed with a sweet and savory garlic sauce.",
        "ingredients": ["4 chicken thighs", "3 garlic cloves", "2 tbsp honey", "2 tbsp soy sauce", "Sesame seeds"],
        "instructions": "Sear chicken until golden. Simmer with garlic, honey, and soy sauce until cooked through.",
    },
    {
        "name": "Rainbow Grain Bowl",
        "emoji": "🥗",
        "time": "20 min",
        "description": "A colorful, nourishing bowl with roasted vegetables and lemon tahini.",
        "ingredients": ["1 cup cooked quinoa", "Roasted sweet potato", "Cucumber", "Chickpeas", "Tahini dressing"],
        "instructions": "Arrange quinoa, vegetables, and chickpeas in a bowl. Drizzle with lemon tahini dressing.",
    },
    {
        "name": "Miso Ramen",
        "emoji": "🍜",
        "time": "20 min",
        "description": "A fast, warming ramen bowl packed with umami flavor.",
        "ingredients": ["2 ramen portions", "3 cups vegetable broth", "2 tbsp miso", "Mushrooms", "Soft-boiled egg"],
        "instructions": "Simmer broth with mushrooms and miso. Cook noodles separately, then combine and top with egg.",
    },
    {
        "name": "Berry Yogurt Parfait",
        "emoji": "🫐",
        "time": "5 min",
        "description": "A bright breakfast layered with creamy yogurt, fruit, and crunchy granola.",
        "ingredients": ["1 cup Greek yogurt", "1/2 cup berries", "1/4 cup granola", "1 tsp honey", "Mint"],
        "instructions": "Layer yogurt, berries, and granola in a glass. Finish with honey and fresh mint.",
    },
    {
        "name": "Crispy Fish Tacos",
        "emoji": "🌮",
        "time": "35 min",
        "description": "Crunchy fish tacos finished with lime slaw and a cool crema.",
        "ingredients": ["400g white fish", "8 tortillas", "Cabbage slaw", "Lime", "Sour cream"],
        "instructions": "Season and pan-fry the fish until crisp. Fill warm tortillas with fish, slaw, lime, and crema.",
    },
    {
        "name": "Mushroom Risotto",
        "emoji": "🍄",
        "time": "40 min",
        "description": "Creamy Arborio rice with earthy mushrooms and fresh herbs.",
        "ingredients": ["1 cup Arborio rice", "250g mushrooms", "4 cups stock", "1/2 onion", "Butter and Parmesan"],
        "instructions": "Sauté onion and rice, then add warm stock one ladle at a time. Fold in mushrooms, butter, and Parmesan.",
    },
    {
        "name": "Green Goddess Salad",
        "emoji": "🥬",
        "time": "15 min",
        "description": "A crisp chopped salad with herbs and a creamy green dressing.",
        "ingredients": ["Romaine lettuce", "Cucumber", "Avocado", "Fresh herbs", "Lemon yogurt dressing"],
        "instructions": "Chop the vegetables and herbs. Toss with avocado and lemon yogurt dressing just before serving.",
    },
    {
        "name": "Chocolate Chip Cookies",
        "emoji": "🍪",
        "time": "25 min",
        "description": "Soft-centered cookies with crisp edges and plenty of chocolate chips.",
        "ingredients": ["115g butter", "1/2 cup brown sugar", "1 egg", "1 cup flour", "Chocolate chips"],
        "instructions": "Cream butter and sugar, mix in egg and flour, then fold in chips. Bake scoops at 180°C for 10–12 minutes.",
    },
]


@app.route("/")
def home():
    sorted_links = sorted(links, key=lambda link: link["name"].lower())
    return render_template("index.html", links=sorted_links)


@app.route("/recipes")
def recipes():
    """Display the collection of quick food recipes."""
    return render_template("with-skills/recipes.html", recipes=RECIPES)


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
