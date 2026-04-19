from flask import redirect, render_template, request, url_for

from .discogs import get_artist_releases, search_artist
from .favorites import get_favorite_ids, load_favorites, toggle_favorite


def register_routes(app):
    @app.route("/")
    def home():
        return render_template("home.html")

    @app.route("/favorites")
    def favorites():
        return render_template("favorites.html", favorites=load_favorites())

    @app.route("/search")
    def search():
        artist_name = request.args.get("artist")
        page = request.args.get("page", 1, type=int)

        if page < 1:
            page = 1

        if not artist_name:
            return render_template(
                "results.html",
                artist=None,
                releases=[],
                error="Voer een artiest in.",
            )

        artist = search_artist(artist_name)

        if not artist:
            return render_template(
                "results.html",
                artist=None,
                releases=[],
                error="Artiest niet gevonden.",
            )

        artist_id = artist.get("id")
        releases, pagination = get_artist_releases(
            artist_id,
            page,
            app.config["RELEASES_PER_PAGE"],
        )

        current_page = pagination.get("page", page)
        total_pages = pagination.get("pages", 1)
        page_numbers = range(
            max(1, current_page - 2),
            min(total_pages, current_page + 2) + 1,
        )

        return render_template(
            "results.html",
            artist=artist,
            artist_name=artist_name,
            releases=releases,
            pagination=pagination,
            page_numbers=page_numbers,
            favorite_ids=get_favorite_ids(),
            error=None,
        )

    @app.route("/favorite/toggle", endpoint="toggle_favorite", methods=["POST"])
    def favorite_toggle():
        release_id = request.form.get("release_id")

        album = {
            "id": int(release_id),
            "title": request.form.get("title"),
            "year": request.form.get("year"),
            "type": request.form.get("type"),
            "role": request.form.get("role"),
            "thumb": request.form.get("thumb"),
        }

        toggle_favorite(album)

        return redirect(request.referrer or url_for("home"))
