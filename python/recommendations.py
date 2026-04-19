from collections import Counter

from .discogs import get_release_details, search_album_recommendations


def _safe_int(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _as_list(value):
    if not value:
        return []

    if isinstance(value, list):
        return [item for item in value if item]

    return [value]


def _normalize_album(album, fallback_artist=None, role="Recommended"):
    fallback_artist = fallback_artist or {}

    title = album.get("title") or "Untitled"
    artist_title = album.get("artist_title")
    if not artist_title and fallback_artist:
        artist_title = fallback_artist.get("title")
    if not artist_title and " - " in title:
        artist_title = title.split(" - ", 1)[0]

    return {
        "id": album.get("id"),
        "title": title,
        "year": album.get("year") or "",
        "type": album.get("type") or "master",
        "role": album.get("role") or role,
        "thumb": album.get("thumb") or album.get("cover_image") or "",
        "artist_id": album.get("artist_id") or fallback_artist.get("id"),
        "artist_title": artist_title,
        "genres": _as_list(album.get("genres") or album.get("genre")),
        "styles": _as_list(album.get("styles") or album.get("style")),
    }


def _favorite_profile(favorites):
    profile = {
        "favorite_ids": {str(favorite.get("id")) for favorite in favorites},
        "years": [],
        "types": Counter(),
        "artists": Counter(),
        "genres": Counter(),
        "styles": Counter(),
    }

    for favorite in favorites[:10]:
        year = _safe_int(favorite.get("year"))
        if year:
            profile["years"].append(year)

        if favorite.get("type"):
            profile["types"][favorite["type"]] += 1

        if favorite.get("artist_title"):
            profile["artists"][favorite["artist_title"]] += 1

        details = get_release_details(
            favorite.get("id"),
            favorite.get("type") or "release",
        )

        for artist in details.get("artists", []):
            profile["artists"][artist] += 1

        for genre in details.get("genres", []):
            profile["genres"][genre] += 1

        for style in details.get("styles", []):
            profile["styles"][style] += 1

    return profile


def _score_album(album, profile):
    score = 0
    year = _safe_int(album.get("year"))

    if year and profile["years"]:
        closest_year = min(abs(year - favorite_year) for favorite_year in profile["years"])

        if closest_year <= 2:
            score += 34
        elif closest_year <= 6:
            score += 22
        elif closest_year <= 12:
            score += 12

    if album.get("type") in profile["types"]:
        score += 12

    if album.get("artist_title") in profile["artists"]:
        score += 36

    score += 18 * len(set(album.get("genres", [])) & set(profile["genres"]))
    score += 14 * len(set(album.get("styles", [])) & set(profile["styles"]))

    if album.get("role") == "Main":
        score += 8

    if album.get("type") == "master":
        score += 6

    if album.get("thumb"):
        score += 4

    return score


def _ranked_unique(candidates, profile, limit):
    unique = {}

    for candidate in candidates:
        raw_release_id = candidate.get("id")
        if raw_release_id is None:
            continue

        release_id = str(raw_release_id)

        if not release_id or release_id in profile["favorite_ids"]:
            continue

        if release_id not in unique:
            unique[release_id] = candidate

    return sorted(
        unique.values(),
        key=lambda album: (_score_album(album, profile), _safe_int(album.get("year")) or 0),
        reverse=True,
    )[:limit]


def recommendations_from_search(favorites, releases, artist, limit=6):
    profile = _favorite_profile(favorites)
    candidates = [
        _normalize_album(release, fallback_artist=artist)
        for release in releases
    ]

    return _ranked_unique(candidates, profile, limit)


def recommendations_from_favorites(favorites, limit=8):
    if not favorites:
        return []

    profile = _favorite_profile(favorites)
    candidates = []

    for artist, _count in profile["artists"].most_common(3):
        candidates.extend(search_album_recommendations(artist=artist, limit=10))

    for genre, _count in profile["genres"].most_common(2):
        candidates.extend(search_album_recommendations(genre=genre, limit=8))

    for style, _count in profile["styles"].most_common(2):
        candidates.extend(search_album_recommendations(style=style, limit=8))

    normalized_candidates = [
        _normalize_album(candidate)
        for candidate in candidates
    ]

    return _ranked_unique(normalized_candidates, profile, limit)
