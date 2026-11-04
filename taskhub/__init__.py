from pathlib import Path

from flask import Flask

from .config import Config
from .extensions import db, migrate
from . import models
from .routes import main


def create_app(test_config: dict[str, object] | None = None) -> Flask:
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(Config)
    if test_config is not None:
        app.config.update(test_config)

    Path(app.instance_path).mkdir(parents=True, exist_ok=True)

    db.init_app(app)
    migrate.init_app(app, db)
    app.register_blueprint(main)
    return app
