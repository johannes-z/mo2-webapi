"""Route modules for the WebAPI."""
from fastapi import FastAPI

from . import health, mods, profile, static


def register_routes(app: FastAPI) -> None:
	app.include_router(health.router)
	app.include_router(profile.router)
	app.include_router(mods.router)
	# Static last so /health, /mods, etc. are not caught by /{path:path}
	app.include_router(static.router)
