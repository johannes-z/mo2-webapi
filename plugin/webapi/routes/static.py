import os
from pathlib import Path

from flask import Blueprint, redirect, send_from_directory

from .. import context
from ..log import log

bp = Blueprint("static", __name__)


@bp.route("/api-docs")
def redirect_api_docs_to_slash():
	"""Redirect /api-docs to /api-docs/ so both show the same."""
	return redirect("/api-docs/", code=302)


@bp.route("/api-docs/")
def serve_api_docs_index():
	"""Serve api-explorer index so /api-docs and /api-docs/ always work."""
	static_dir = context.get_static_dir()
	if not static_dir or not static_dir.exists():
		return {"error": "Frontend not available"}, 404
	static_dir = static_dir.resolve()
	api_docs_dir = static_dir / "api-docs"
	index_path = api_docs_dir / "index.html"
	index_str = os.path.normpath(os.path.join(str(static_dir), "api-docs", "index.html"))
	if not os.path.isfile(index_str):
		log.warning(f"api-docs index not found at {index_str} (static_dir={static_dir})")
		return {"error": "File not found"}, 404
	return send_from_directory(str(api_docs_dir), "index.html")


@bp.route("/", defaults={"path": ""})
@bp.route("/<path:path>")
def serve_static(path: str):
	static_dir = context.get_static_dir()
	if not static_dir or not static_dir.exists():
		return {"error": "Frontend not available"}, 404
	static_dir = static_dir.resolve()
	if not path:
		path = "index.html"
	path_clean = path.rstrip("/")
	# Fallback: if asking for api-docs dir, serve its index.html
	if path_clean == "api-docs":
		api_docs_index = os.path.normpath(os.path.join(str(static_dir), "api-docs", "index.html"))
		if os.path.isfile(api_docs_index):
			return send_from_directory(os.path.join(str(static_dir), "api-docs"), "index.html")
	file_path = (static_dir / path_clean).resolve()
	try:
		if not file_path.is_relative_to(static_dir):
			return {"error": "Invalid path"}, 400
	except (ValueError, AttributeError):
		return {"error": "Invalid path"}, 400
	if file_path.exists() and file_path.is_dir():
		path_clean = f"{path_clean}/index.html"
		file_path = (static_dir / path_clean).resolve()
	elif not file_path.exists() and not path_clean.endswith(".html"):
		index_candidate = static_dir / path_clean / "index.html"
		if index_candidate.resolve().exists() and index_candidate.resolve().is_file():
			path_clean = f"{path_clean}/index.html"
			file_path = index_candidate.resolve()
	if not file_path.exists() or not file_path.is_file():
		return {"error": "File not found"}, 404
	path = path_clean
	try:
		return send_from_directory(static_dir, path)
	except Exception as e:
		log.error(f"Error serving static file {file_path}: {e}")
		return {"error": "Failed to serve file"}, 500
