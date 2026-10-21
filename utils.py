import re


def is_valid_url(value):
    """Return whether a value matches the application's URL format."""
    url_pattern = (
        r"((http|https)://)(www\.)?"
        r"[a-zA-Z0-9@:%._\+~#?&//=]{2,256}\."
        r"[a-z]{2,6}\b([-a-zA-Z0-9@:%._\+~#?&//=]*)"
    )
    return re.match(url_pattern, value) is not None


def is_duplicate_site_name(site_name, links):
    """Return whether a site name already exists, ignoring case."""
    normalized_name = site_name.strip().casefold()
    return any(link["name"].strip().casefold() == normalized_name for link in links)
