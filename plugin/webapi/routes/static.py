from pathlib import Path

from flask import Blueprint, send_from_directory

from .. import context
from ..log import log

bp = Blueprint("static", __name__)


@bp.route("/", defaults={"path": ""})
@bp.route("/<path:path>")
def serve_static(path: str):
	static_dir = context.get_static_dir()
	if not static_dir or not static_dir.exists():
		return {"error": "Frontend not available"}, 404
	if not path:
		path = "index.html"
	file_path = static_dir / path
	try:
		if not file_path.is_relative_to(static_dir):
			return {"error": "Invalid path"}, 400
	except (ValueError, AttributeError):
		return {"error": "Invalid path"}, 400
	if not file_path.exists() or not file_path.is_file():
		return {"error": "File not found"}, 404
	try:
		return send_from_directory(static_dir, path)
	except Exception as e:
		log.error(f"Error serving static file {file_path}: {e}")
		return {"error": "Failed to serve file"}, 500
