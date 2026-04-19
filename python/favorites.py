import json

from flask import current_app


def _favorites_file():
    return current_app.config["FAVORITES_FILE"]


def load_favorites():
    favorites_file = _favorites_file()

    if not favorites_file.exists():
        return []

    with favorites_file.open("r", encoding="utf-8") as file:
        return json.load(file)


def save_favorites(favorites):
    favorites_file = _favorites_file()

    with favorites_file.open("w", encoding="utf-8") as file:
        json.dump(favorites, file, indent=4)


def get_favorite_ids():
    return {str(favorite["id"]) for favorite in load_favorites()}


def toggle_favorite(album):
    release_id = str(album["id"])
    favorites = load_favorites()

    already_favorite = any(str(favorite["id"]) == release_id for favorite in favorites)

    if already_favorite:
        favorites = [
            favorite for favorite in favorites
            if str(favorite["id"]) != release_id
        ]
    else:
        favorites.append(album)

    save_favorites(favorites)
