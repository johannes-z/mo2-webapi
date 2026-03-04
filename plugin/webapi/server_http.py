from flask import Flask

from . import config
from .log import log
from .routes import register_routes

app = Flask(__name__)
app.config["JSON_SORT_KEYS"] = False


@app.after_request
def add_cors_headers(response):
	response.headers["Access-Control-Allow-Origin"] = config.CORS_ALLOW_ORIGIN
	response.headers["Access-Control-Allow-Methods"] = config.CORS_ALLOW_METHODS
	response.headers["Access-Control-Allow-Headers"] = config.CORS_ALLOW_HEADERS
	return response


@app.errorhandler(404)
def not_found(error):
	return {"error": "Endpoint not found"}, 404


@app.errorhandler(500)
def internal_error(error):
	log.error(f"Internal server error: {error}")
	return {"error": "Internal server error"}, 500


register_routes(app)

_server = None


def shutdown_server() -> None:
	global _server
	if not _server:
		return
	log.info("Shutting down HTTP server")
	try:
		_server.shutdown()
	except Exception as e:
		log.error(f"Error during HTTP server shutdown: {e}")
	_server = None


def run_server(port: int) -> None:
	global _server
	from werkzeug.serving import make_server
	try:
		log.info(f"Starting Flask HTTP server on port {port}")
		_server = make_server("0.0.0.0", port, app, threaded=True)
		_server.serve_forever()
	except Exception as e:
		log.error(f"Failed to start HTTP server on port {port}: {e}")
	finally:
		_server = None
