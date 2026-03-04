"""Route modules for the WebAPI."""
from flask import Flask

from .. import config


def register_routes(app: Flask) -> None:
	from . import mods, health, profile, static
	app.register_blueprint(static.bp)
	app.register_blueprint(mods.bp)
	app.register_blueprint(health.bp)
	app.register_blueprint(profile.bp)
