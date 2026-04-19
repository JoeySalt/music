import os
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
RELEASES_PER_PAGE = 24


def configure_app(app):
    app.config.from_mapping(
        CACHE_TYPE="RedisCache",
        CACHE_REDIS_URL=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
        CACHE_DEFAULT_TIMEOUT=3600,
        DISCOGS_TOKEN=os.getenv("DISCOGS_TOKEN"),
        DISCOGS_USER_AGENT="VinylFinder/1.0 +https://example.com",
        FAVORITES_FILE=PROJECT_ROOT / "favorites.json",
        RELEASES_PER_PAGE=RELEASES_PER_PAGE,
    )
