from flask import Flask, render_template, request
import requests
import os
from dotenv import load_dotenv
from flask_caching import Cache

load_dotenv()

app = Flask(__name__ )

app.config["CACHE_TYPE"] = "RedisCache"
app.config["CACHE_REDIS_URL"] = os.getenv("REDIS_URL", "redis://localhost:6379/0")
app.config["CACHE_DEFAULT_TIMEOUT"] = 3600

cache = Cache(app)

DISCOGS_TOKEN = os.getenv('DISCOGS_TOKEN')
RELEASES_PER_PAGE = 24

HEADERS = {
    "User-Agent": "VinylFinder/1.0 +https://example.com",
    "Authorization": f"Discogs token={DISCOGS_TOKEN}"
}

@cache.memoize(timeout=3600)
def search_artist(artist_name):
    url = "https://api.discogs.com/database/search"
    params = {
        "q": artist_name,
        "type": "artist"
    }

    response = requests.get(url, headers=HEADERS, params=params)

    if response.status_code != 200:
        return None

    data = response.json()
    results = data.get("results", [])

    if not results:
        return None
    
    return results[0]  # returns the first matching result

@cache.memoize(timeout=3600)
def get_artist_releases(artist_id, page=1, per_page=RELEASES_PER_PAGE):
    url = f"https://api.discogs.com/artists/{artist_id}/releases"
    params = {
        "sort": "year",
        "sort_order": "asc",
        "page": page,
        "per_page": per_page
    }

    response = requests.get(url, headers=HEADERS, params=params)

    if response.status_code != 200:
        return [], {
            "page": page,
            "pages": 1,
            "items": 0,
            "per_page": per_page
        }

    data = response.json()
    pagination = data.get("pagination", {})

    return data.get("releases", []), {
        "page": pagination.get("page", page),
        "pages": pagination.get("pages", 1),
        "items": pagination.get("items", 0),
        "per_page": pagination.get("per_page", per_page)
    }

@app.route("/")
def home():
    return render_template("home.html")

@app.route("/search")
def search():
    artist_name = request.args.get("artist")
    page = request.args.get("page", 1, type=int)

    if page < 1:
        page = 1

    if not artist_name:
        return render_template("results.html", artist=None, releases=[], error="Voer een artiest in.")
    
    artist = search_artist(artist_name)

    if not artist:
        return render_template("results.html", artist=None, releases=[], error="Artiest niet gevonden.")
    
    artist_id = artist.get("id")
    releases, pagination = get_artist_releases(artist_id, page, RELEASES_PER_PAGE)

    current_page = pagination.get("page", page)
    total_pages = pagination.get("pages", 1)
    page_numbers = range(
        max(1, current_page - 2),
        min(total_pages, current_page + 2) + 1
    )

    return render_template(
        "results.html",
        artist=artist,
        artist_name=artist_name,
        releases=releases,
        pagination=pagination,
        page_numbers=page_numbers,
        error=None
    )

if __name__ == "__main__":
    app.run(debug=True, port=5001)
