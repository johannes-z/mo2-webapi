"""Route modules for the WebAPI."""
from flask import Flask

from .. import config


def register_routes(app: Flask) -> None:
	from . import mods, health, profile, static
	app.register_blueprint(mods.bp)
	app.register_blueprint(health.bp)
	app.register_blueprint(profile.bp)
	app.register_blueprint(static.bp)
	if config.DEV_ENDPOINT_ENABLED:
		from . import dev
		app.register_blueprint(dev.bp)
