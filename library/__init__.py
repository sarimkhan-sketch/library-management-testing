"""Library Management System: a small Flask + SQLite REST API."""
from datetime import date
from pathlib import Path

from flask import Flask, jsonify

from . import auth, books, db, loans

__version__ = "1.1.0"


def create_app(config=None):
    app = Flask(__name__)
    app.config.update(
        DATABASE=str(Path(app.instance_path) / "library.db"),
        ADMIN_USERNAME="admin",
        ADMIN_PASSWORD=None,
        TODAY=date.today,
    )
    if config:
        app.config.update(config)
    Path(app.config["DATABASE"]).parent.mkdir(parents=True, exist_ok=True)

    app.teardown_appcontext(db.close_db)
    for module in (auth, books, loans):
        app.register_blueprint(module.bp)

    @app.get("/")
    def index():
        # Demo web page (library/static/index.html); it only calls the JSON API below.
        return app.send_static_file("index.html")

    @app.get("/api")
    def api_info():
        return jsonify({"service": "Library Management System", "version": __version__})

    @app.errorhandler(404)
    def not_found(_e):
        return jsonify({"error": "not found"}), 404

    @app.errorhandler(405)
    def bad_method(_e):
        return jsonify({"error": "method not allowed"}), 405

    with app.app_context():
        db.init_db()
    return app
