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


def _database_search(params, limit=12):
    url = "https://api.discogs.com/database/search"
    params = {
        **params,
        "per_page": min(limit, 25),
    }

    response = requests.get(url, headers=_headers(), params=params)

    if response.status_code != 200:
        return []

    return response.json().get("results", [])[:limit]


def _tag_results(results, role):
    tagged_results = []

    for result in results:
        tagged_result = result.copy()
        tagged_result["role"] = role
        tagged_results.append(tagged_result)

    return tagged_results


def _unique_results(results, limit):
    unique = {}

    for result in results:
        result_id = result.get("id")

        if result_id is None:
            continue

        key = f"{result.get('type')}:{result_id}"

        if key not in unique:
            unique[key] = result

    return list(unique.values())[:limit]


@cache.memoize(timeout=3600)
def search_catalog(query, limit=24):
    album_matches = _tag_results(
        _database_search(
            {
                "q": query,
                "type": "master",
                "format": "Album",
            },
            limit=12,
        ),
        "Album match",
    )
    release_matches = _tag_results(
        _database_search(
            {
                "q": query,
                "type": "release",
            },
            limit=8,
        ),
        "Catalog match",
    )
    song_matches = _tag_results(
        _database_search(
            {
                "track": query,
                "type": "release",
            },
            limit=12,
        ),
        "Song match",
    )

    return _unique_results(
        album_matches + song_matches + release_matches,
        limit,
    )


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


@cache.memoize(timeout=3600)
def get_release_details(release_id, release_type="release"):
    endpoint = "masters" if release_type == "master" else "releases"
    url = f"https://api.discogs.com/{endpoint}/{release_id}"

    response = requests.get(url, headers=_headers())

    if response.status_code != 200:
        return {}

    data = response.json()
    images = data.get("images", [])
    artists = [
        artist.get("name")
        for artist in data.get("artists", [])
        if artist.get("name")
    ]

    return {
        "id": release_id,
        "title": data.get("title"),
        "year": data.get("year"),
        "type": release_type,
        "thumb": images[0].get("uri150", "") if images else "",
        "artists": artists,
        "genres": data.get("genres", []),
        "styles": data.get("styles", []),
    }


@cache.memoize(timeout=3600)
def search_album_recommendations(artist=None, genre=None, style=None, limit=12):
    url = "https://api.discogs.com/database/search"
    params = {
        "type": "master",
        "format": "Album",
        "per_page": min(limit, 25),
    }

    if artist:
        params["artist"] = artist

    if genre:
        params["genre"] = genre

    if style:
        params["style"] = style

    response = requests.get(url, headers=_headers(), params=params)

    if response.status_code != 200:
        return []

    return response.json().get("results", [])[:limit]
