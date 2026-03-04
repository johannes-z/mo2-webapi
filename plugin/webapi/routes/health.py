from flask import Blueprint, jsonify

from .. import config

bp = Blueprint("health", __name__)


@bp.route("/health", methods=["GET"])
def health_check():
	return jsonify({"status": "ok", "version": config.API_VERSION})
