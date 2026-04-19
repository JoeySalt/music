from flask import Flask
from dotenv import load_dotenv

from .config import configure_app, PROJECT_ROOT
from .extensions import cache
from .routes import register_routes


def create_app():
    load_dotenv()

    app = Flask(
        __name__,
        template_folder=str(PROJECT_ROOT / "templates"),
        static_folder=str(PROJECT_ROOT / "static"),
    )

    configure_app(app)
    cache.init_app(app)
    register_routes(app)

    return app
