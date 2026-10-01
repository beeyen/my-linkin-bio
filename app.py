from flask import Flask, redirect, render_template, request, url_for

app = Flask(__name__, static_folder="statics")
links = [
    {"name": "LinkedIn", "url": "https://www.linkedin.com/"},
    {"name": "GitHub", "url": "https://github.com/"},
    {"name": "AT&T", "url": "https://www.att.com/"},
]


@app.route("/")
def home():
    sorted_links = sorted(links, key=lambda link: link["name"].lower())
    return render_template("index.html", links=sorted_links)


@app.post("/add")
def add_link():
    links.append({
        "name": request.form["name"],
        "url": request.form["url"],
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
            break
    return redirect(url_for("home"))


@app.route("/about")
def about():
    return render_template("about.html")


if __name__ == "__main__":
    app.run(debug=True)
