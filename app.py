import requests
from bs4 import BeautifulSoup
from flask import Flask, redirect, render_template, request, url_for

app = Flask(__name__, static_folder="statics")
links = []


@app.route("/")
def home():
    sorted_links = sorted(links, key=lambda link: link["name"].lower())
    return render_template("index.html", links=sorted_links)


def fetch_link_metadata(url):
    """Fetch Open Graph metadata and use fallbacks when it is unavailable."""
    metadata = {
        "title": "Not Available",
        "description": "Not Available",
        "image_url": "Not Available",
    }
    try:
        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=5)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
    except requests.RequestException:
        return metadata

    for field, property_name in (("title", "og:title"), ("description", "og:description"), ("image_url", "og:image")):
        tag = soup.find("meta", property=property_name)
        content = tag.get("content", "").strip() if tag else ""
        metadata[field] = content or "Not Available"
    return metadata


@app.post("/add")
def add_link():
    link_url = request.form["url"]
    links.append({
        "name": request.form["name"],
        "url": link_url,
        **fetch_link_metadata(link_url),
    })
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
            link.update(fetch_link_metadata(link["url"]))
            break
    return redirect(url_for("home"))


@app.route("/about")
def about():
    return render_template("about.html")


if __name__ == "__main__":
    app.run(debug=True)
