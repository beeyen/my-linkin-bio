# my-linkin-bio

## Project Overview

`my-linkin-bio` is a Flask application for managing and displaying a personal collection of links as styled link cards. Link metadata is fetched from each URL when a link is added or edited.

Application routes are organized in the `main` Flask Blueprint and registered by the application factory in `app.py`.

## Features

- View links sorted alphabetically by name at `/`.
- Check application health and server time at `/health`.
- Add links with a name and URL using the home page form.
- Validate submitted URLs and show a warning when a URL is invalid.
- Block duplicate site names and show a warning when a duplicate link is submitted.
- Edit or delete existing links from the home page.
- Fetch Open Graph titles, descriptions, and images for link cards.
- Show a warning and visual indicator when link metadata cannot be retrieved.
- View project information at `/about`.
- View contact information and an email address at `/contact`.
- Browse 10 quick food recipes at `/recipes`.
- Render custom styled pages for 404 and 500 errors.

### Routes

- `GET /` — Display the link collection and link management form.
- `GET /health` — Return a JSON health status and current server time.
- `POST /add` — Add a link.
- `POST /edit` — Update a link.
- `POST /delete` — Delete a link.
- `GET /about` — Display information about the project.
- `GET /contact` — Display a short contact message and email address.
- `GET /recipes` — Display 10 recipes with ingredients, timing, and instructions.

## Setup

1. Create and activate a virtual environment:

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

2. Install the dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Create the local environment file and replace the placeholder secret:

   ```bash
   cp .env.example .env
   ```

   `SECRET_KEY` is required for secure Flask sessions and flash messages. The app uses a development fallback when it is not set, but deployed environments should always provide a real secret.

4. Export the environment variables and start the development server:

   ```bash
   set -a
   source .env
   set +a
   python3 app.py
   ```

5. Open [http://127.0.0.1:5000](http://127.0.0.1:5000) in a browser.

## Dependencies

- Flask 3.1.3 — Web application framework.
- Gunicorn 26.2.0 — Production WSGI server.
- Requests 2.34.2 — Fetches metadata from link URLs.
- Beautiful Soup 4.15.0 — Parses Open Graph metadata from fetched pages.
