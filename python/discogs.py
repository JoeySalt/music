import requests
from flask import current_app

from .extensions import cache


def _headers():
    token = current_app.config["DISCOGS_TOKEN"]
    return {
        "User-Agent": current_app.config["DISCOGS_USER_AGENT"],
        "Authorization": f"Discogs token={token}",
    }


@cache.memoize(timeout=3600)
def search_artist(artist_name):
    url = "https://api.discogs.com/database/search"
    params = {
        "q": artist_name,
        "type": "artist",
    }

    response = requests.get(url, headers=_headers(), params=params)

    if response.status_code != 200:
        return None

    results = response.json().get("results", [])

    if not results:
        return None

    return results[0]


@cache.memoize(timeout=3600)
def get_artist_releases(artist_id, page=1, per_page=None):
    if per_page is None:
        per_page = current_app.config["RELEASES_PER_PAGE"]

    url = f"https://api.discogs.com/artists/{artist_id}/releases"
    params = {
        "sort": "year",
        "sort_order": "asc",
        "page": page,
        "per_page": per_page,
    }

    response = requests.get(url, headers=_headers(), params=params)

    if response.status_code != 200:
        return [], {
            "page": page,
            "pages": 1,
            "items": 0,
            "per_page": per_page,
        }

    data = response.json()
    pagination = data.get("pagination", {})

    return data.get("releases", []), {
        "page": pagination.get("page", page),
        "pages": pagination.get("pages", 1),
        "items": pagination.get("items", 0),
        "per_page": pagination.get("per_page", per_page),
    }
