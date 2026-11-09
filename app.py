import json
import logging
import os
from pathlib import Path

from flask import Flask, render_template

from routes import main_blueprint

logging.basicConfig(level=logging.INFO)


def load_configuration():
    """Load labels and page names from the project configuration file."""
    configuration_path = Path(__file__).with_name("constants.json")
    with configuration_path.open(encoding="utf-8") as configuration_file:
        return json.load(configuration_file)


def create_app():
    """Create and configure the Flask application."""
    configuration = load_configuration()
    app = Flask(__name__, static_folder="statics")
    # Use the documented environment secret in deployed environments, with a local-only fallback.
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-key")
    app.config["LABELS"] = configuration["LABELS"]
    app.config["PAGE_NAMES"] = configuration["PAGE_NAMES"]
    app.config["RECIPES"] = configuration["RECIPES"]
    app.config["RECIPE_FILTERS"] = configuration["RECIPE_FILTERS"]
    app.config["RECIPE_LABELS"] = configuration["RECIPE_LABELS"]
    app.register_blueprint(main_blueprint)

    @app.errorhandler(404)
    def page_not_found(error):
        """Render the custom page for routes that do not exist."""
        return render_template("404.html"), 404

    @app.errorhandler(500)
    def internal_server_error(error):
        """Render the custom page for unexpected application errors."""
        return render_template("500.html"), 500

    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=True)
