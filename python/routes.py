from flask import redirect, render_template, request, url_for

from .discogs import get_artist_releases, search_artist, search_catalog
from .favorites import get_favorite_ids, load_favorites, toggle_favorite
from .recommendations import recommendations_from_favorites, recommendations_from_search


def register_routes(app):
    @app.route("/")
    def home():
        return render_template("home.html")

    @app.route("/favorites")
    def favorites():
        favorites_list = load_favorites()

        return render_template(
            "favorites.html",
            favorites=favorites_list,
            recommendations=recommendations_from_favorites(favorites_list),
            favorite_ids=get_favorite_ids(),
        )

    @app.route("/search")
    def search():
        search_query = request.args.get("q") or request.args.get("artist")
        page = request.args.get("page", 1, type=int)

        if page < 1:
            page = 1

        if not search_query:
            return render_template(
                "results.html",
                artist=None,
                catalog_results=[],
                releases=[],
                recommendations=[],
                favorite_ids=get_favorite_ids(),
                error="Voer een artiest, album of song in.",
            )

        artist = search_artist(search_query)
        catalog_results = search_catalog(
            search_query,
            app.config["RELEASES_PER_PAGE"],
        )

        if not artist and not catalog_results:
            return render_template(
                "results.html",
                artist=None,
                catalog_results=[],
                releases=[],
                recommendations=[],
                favorite_ids=get_favorite_ids(),
                search_query=search_query,
                error="Geen artiest, album of song gevonden.",
            )

        releases = []
        pagination = None
        page_numbers = []

        if artist:
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

        favorites_list = load_favorites()
        recommendation_seeds = catalog_results + releases

        return render_template(
            "results.html",
            artist=artist,
            search_query=search_query,
            catalog_results=catalog_results,
            releases=releases,
            pagination=pagination,
            page_numbers=page_numbers,
            favorite_ids={str(favorite["id"]) for favorite in favorites_list},
            recommendations=recommendations_from_search(
                favorites_list,
                recommendation_seeds,
                artist,
            ),
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
            "artist_id": request.form.get("artist_id"),
            "artist_title": request.form.get("artist_title"),
        }

        toggle_favorite(album)

        return redirect(request.referrer or url_for("home"))
