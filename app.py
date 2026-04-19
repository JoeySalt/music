from flask import Flask, render_template, request
import requests
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__ )

DISCOGS_TOKEN = os.getenv('DISCOGS_TOKEN')

HEADERS = {
    "User-Agent": "VinylFinder/1.0 +https://example.com",
    "Authorization": f"Discogs token={DISCOGS_TOKEN}"
}

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

def get_artist_releases(artist_id):
    url = f"https://api.discogs.com/artists/{artist_id}/releases"
    params = {
        "sort": "year",
        "sort_order": "asc"
    }

    response = requests.get(url, headers=HEADERS, params=params)

    if response.status_code != 200:
        return []
    
    data = response.json()
    return data.get("releases", [])

@app.route("/")
def home():
    return render_template("home.html")

@app.route("/search")
def search():
    artist_name = request.args.get("artist")

    if not artist_name:
        return render_template("results.html", artist=None, releases=[], error="Voer een artiest in.")
    
    artist = search_artist(artist_name)

    if not artist:
        return render_template("results.html", artist=None, releases=[], error="Artiest niet gevonden.")
    
    artist_id = artist.get("id")
    releases = get_artist_releases(artist_id)

    return render_template("results.html", artist=artist, releases=releases, error=None)

if __name__ == "__main__":
    app.run(debug=True, port=5001)
