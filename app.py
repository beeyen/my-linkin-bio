from flask import Flask, redirect, render_template, request, url_for

app = Flask(__name__)
links = []


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


@app.route("/about")
def about():
    return render_template("about.html")


if __name__ == "__main__":
    app.run(debug=True)
