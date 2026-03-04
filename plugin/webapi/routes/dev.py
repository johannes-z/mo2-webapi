from pathlib import Path

from flask import Blueprint, send_file

bp = Blueprint("dev", __name__)
_index_html = Path(__file__).parent.parent / "static" / "index.html"


@bp.route("/dev")
@bp.route("/api-docs")
def serve_dev():
	if not _index_html.exists():
		return {"error": "API overview not found"}, 404
	return send_file(_index_html, mimetype="text/html")
