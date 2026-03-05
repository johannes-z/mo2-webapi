from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from . import config
from .log import log
from .routes import register_routes

OPENAPI_TAGS = [
	{"name": "Health", "description": "Server health and configuration."},
	{"name": "Mods", "description": "List, query, enable/disable, and manage mod metadata and conflicts."},
	{"name": "Profile", "description": "Current profile and profile list (activation not supported via API)."},
]

app = FastAPI(
	title="MO2 WebAPI",
	description="REST API for Mod Organizer 2: query and manage mods, metadata, conflicts, and profiles.",
	version=config.API_VERSION,
	openapi_url="/openapi.json",
	docs_url="/docs",
	redoc_url="/redoc",
	openapi_tags=OPENAPI_TAGS,
)

app.add_middleware(
	CORSMiddleware,
	allow_origins=config.CORS_ALLOW_ORIGIN.split(",") if "," in config.CORS_ALLOW_ORIGIN else [config.CORS_ALLOW_ORIGIN],
	allow_methods=config.CORS_ALLOW_METHODS.split(","),
	allow_headers=config.CORS_ALLOW_HEADERS.split(","),
)


@app.exception_handler(404)
async def not_found(request, exc):
	return JSONResponse(content={"error": "Endpoint not found"}, status_code=404)


@app.exception_handler(500)
async def internal_error(request, exc):
	log.error(f"Internal server error: {exc}")
	return JSONResponse(content={"error": "Internal server error"}, status_code=500)


register_routes(app)

_server = None


def shutdown_server() -> None:
	global _server
	if not _server:
		return
	log.info("Shutting down HTTP server")
	try:
		_server.should_exit = True
	except Exception as e:
		log.error(f"Error during HTTP server shutdown: {e}")
	_server = None


def run_server(port: int) -> None:
	global _server
	from uvicorn import Config, Server
	config_ = Config(app=app, host="0.0.0.0", port=port, log_level="warning", log_config=None)
	_server = Server(config_)
	try:
		log.info(f"Starting FastAPI HTTP server on port {port}")
		_server.run()
	except Exception as e:
		log.error(f"Failed to start HTTP server on port {port}: {e}")
	finally:
		_server = None
