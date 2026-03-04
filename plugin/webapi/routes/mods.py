from functools import wraps

import mobase
from flask import Blueprint, jsonify, request

from .. import context
from ..organizer import mod_helper, db_helper
from ..log import log

bp = Blueprint("mods", __name__)


def _require_organizer(f):
	@wraps(f)
	def wrapper(*args, **kwargs):
		if not context.get_organizer():
			return jsonify({"error": "Organizer not initialized"}), 500
		return f(*args, **kwargs)
	return wrapper


def _validate_mod(mod_name: str):
	organizer = context.get_organizer()
	if not organizer:
		return None, (jsonify({"error": "Organizer not initialized"}), 500)
	mod_list = organizer.modList()
	mod = mod_list.getMod(mod_name)
	if not mod:
		return None, (jsonify({"error": f"Mod '{mod_name}' not found"}), 404)
	return mod, None


def _get_json_field(field: str, required_type=None):
	"""Extract a field from JSON body. Returns (value, error_response)."""
	data = request.get_json()
	value = data.get(field) if data else None
	if value is None:
		return None, (jsonify({"error": f"Missing '{field}' parameter"}), 400)
	if required_type and not isinstance(value, required_type):
		return None, (jsonify({"error": f"Invalid '{field}' parameter (must be {required_type.__name__})"}), 400)
	return value, None


def _get_mods_filtered(filter_fn=None) -> list:
	organizer = context.get_organizer()
	if not organizer:
		return []
	mod_list = organizer.modList()
	mods = []
	for mod_name in _get_mod_names_by_priority(mod_list):
		if not mod_list.getMod(mod_name):
			continue
		if filter_fn:
			state = mod_list.state(mod_name)
			if not filter_fn(state):
				continue
		mod_info = mod_helper.get_mod_info(organizer, mod_name)
		if mod_info:
			mods.append(mod_info)
	return mods


def _get_mod_names_by_priority(mod_list: mobase.IModList) -> list[str]:
	# MO2 can throw invalid mod index after deletes; fall back to unsorted allMods
	try:
		return list(mod_list.allModsByProfilePriority())
	except RuntimeError as e:
		log.warning(f"allModsByProfilePriority failed; using unsorted allMods: {e}")
		return list(mod_list.allMods())


# --- List endpoints ---

@bp.route("/mods/list", methods=["GET"])
@_require_organizer
def get_mods_list():
	organizer = context.get_organizer()
	mod_list = organizer.modList()
	mods = []
	for priority, mod_name in enumerate(_get_mod_names_by_priority(mod_list)):
		if not mod_list.getMod(mod_name):
			continue
		state = mod_list.state(mod_name)
		mods.append({
			"name": mod_name,
			"isEnabled": bool(state & mobase.ModState.ACTIVE),
			"priority": priority,
		})
	return jsonify(mods)


@bp.route("/mods", methods=["GET"])
@_require_organizer
def get_mods():
	return jsonify(_get_mods_filtered())


@bp.route("/mods/enabled", methods=["GET"])
@_require_organizer
def get_enabled_mods():
	return jsonify(_get_mods_filtered(lambda state: state & mobase.ModState.ACTIVE))


@bp.route("/mods/disabled", methods=["GET"])
@_require_organizer
def get_disabled_mods():
	return jsonify(_get_mods_filtered(lambda state: not (state & mobase.ModState.ACTIVE)))


@bp.route("/mods/priority", methods=["GET"])
@_require_organizer
def get_mods_priority():
	organizer = context.get_organizer()
	mod_list = organizer.modList()
	priorities = [
		{"name": name, "priority": mod_list.priority(name)}
		for name in _get_mod_names_by_priority(mod_list)
		if mod_list.getMod(name)
	]
	return jsonify(priorities)


# --- Query endpoints ---

@bp.route("/mods/search", methods=["GET"])
@_require_organizer
def search_mods():
	query = request.args.get("q", "").lower()
	if not query:
		return jsonify({"error": "Missing 'q' query parameter"}), 400
	organizer = context.get_organizer()
	mod_list = organizer.modList()
	mods = [
		info for name in _get_mod_names_by_priority(mod_list)
		if query in name.lower()
		and (info := mod_helper.get_mod_info(organizer, name))
	]
	return jsonify(mods)


@bp.route("/mods/meta", methods=["GET"])
@_require_organizer
def get_all_mods_meta():
	return jsonify(db_helper.read_all_metadata())


@bp.route("/mods/<path:mod_name>", methods=["GET"])
@_require_organizer
def get_mod_info_endpoint(mod_name: str):
	mod_info = mod_helper.get_mod_info(context.get_organizer(), mod_name)
	if not mod_info:
		return jsonify({"error": f"Mod '{mod_name}' not found"}), 404
	return jsonify(mod_info)


# --- Conflict endpoints ---

@bp.route("/mods/conflicts", methods=["GET"])
@_require_organizer
def get_all_conflicts():
	"""Get conflict summaries for all mods.

	If cache is stale, recomputes (may take a moment for large mod lists).
	Use ?refresh=true to force recomputation.
	"""
	refresh = request.args.get("refresh", "").lower() in ("true", "1")
	organizer = context.get_organizer()
	if mod_helper.is_conflicts_stale() or refresh:
		mod_helper.compute_conflict_summaries(organizer)
	return jsonify(mod_helper.get_all_conflict_summaries())


@bp.route("/mods/<path:mod_name>/conflicts", methods=["GET"])
@_require_organizer
def get_mod_conflicts(mod_name: str):
	_, error = _validate_mod(mod_name)
	if error:
		return error
	organizer = context.get_organizer()
	refresh = request.args.get("refresh", "").lower() in ("true", "1")
	if mod_helper.is_conflicts_stale() or refresh:
		mod_helper.compute_conflict_summaries(organizer)
	return jsonify(mod_helper.get_mod_conflicts(organizer, mod_name))


# --- State modification endpoints ---

@bp.route("/mods/enable", methods=["PATCH"])
@_require_organizer
def enable_mod():
	name, error = _get_json_field("name")
	if error:
		return error
	context.get_task_executor().submit(mod_helper.set_mod_active_fn(name, True))
	return ("", 200)


@bp.route("/mods/disable", methods=["PATCH"])
@_require_organizer
def disable_mod():
	name, error = _get_json_field("name")
	if error:
		return error
	context.get_task_executor().submit(mod_helper.set_mod_active_fn(name, False))
	return ("", 200)


@bp.route("/mods/toggle", methods=["PATCH"])
@_require_organizer
def toggle_mod():
	name, error = _get_json_field("name")
	if error:
		return error
	context.get_task_executor().submit(mod_helper.toggle_mod_fn(name))
	return ("", 200)


@bp.route("/mods/state", methods=["PATCH"])
@_require_organizer
def set_mods_state():
	data = request.get_json()
	if not isinstance(data, list) or not data:
		return jsonify({"error": "Request body must be a non-empty array"}), 400

	errors = []
	for idx, item in enumerate(data):
		if not isinstance(item, dict):
			errors.append({"index": idx, "error": "Item must be an object"})
			continue
		name = item.get("name")
		state = item.get("state")
		if not name or not isinstance(name, str):
			errors.append({"index": idx, "error": "Missing or invalid 'name'"})
			continue
		if not isinstance(state, bool):
			errors.append({"index": idx, "error": "Missing or invalid 'state' (must be boolean)"})
			continue
		context.get_task_executor().submit(mod_helper.set_mod_active_fn(name, state))
	if errors:
		return jsonify({"errors": errors}), 400
	return ("", 200)


@bp.route("/mods/set-priority", methods=["PATCH"])
@_require_organizer
def set_priority():
	name, error = _get_json_field("name")
	if error:
		return error

	data = request.get_json()
	priority = data.get("priority") if data else None
	if priority is None:
		return jsonify({"error": "Missing 'priority' parameter"}), 400
	try:
		priority = int(priority)
	except (ValueError, TypeError):
		return jsonify({"error": "Invalid priority value, must be an integer"}), 400

	context.get_task_executor().submit(mod_helper.set_mod_priority_fn(name, priority))
	return ("", 200)


@bp.route("/mods/<path:mod_name>/rename", methods=["PATCH"])
@_require_organizer
def rename_mod(mod_name: str):
	_, error = _validate_mod(mod_name)
	if error:
		return error
	new_name, error = _get_json_field("newName")
	if error:
		return error
	if not new_name or not new_name.strip():
		return jsonify({"error": "newName cannot be empty"}), 400
	new_name = new_name.strip()
	if context.get_organizer().modList().getMod(new_name):
		return jsonify({"error": f"Mod '{new_name}' already exists"}), 409
	context.get_task_executor().submit(mod_helper.rename_mod_fn(mod_name, new_name))
	return ("", 200)


@bp.route("/mods/<path:mod_name>", methods=["DELETE"])
@_require_organizer
def remove_mod(mod_name: str):
	_, error = _validate_mod(mod_name)
	if error:
		return error
	context.get_task_executor().submit(mod_helper.remove_mod_fn(mod_name))
	return ("", 200)


@bp.route("/mods/enable-batch", methods=["PATCH"])
@_require_organizer
def enable_batch():
	names, error = _get_json_field("names", required_type=list)
	if error:
		return error
	for name in names:
		context.get_task_executor().submit(mod_helper.set_mod_active_fn(name, True))
	return ("", 200)


@bp.route("/mods/disable-batch", methods=["PATCH"])
@_require_organizer
def disable_batch():
	names, error = _get_json_field("names", required_type=list)
	if error:
		return error
	for name in names:
		context.get_task_executor().submit(mod_helper.set_mod_active_fn(name, False))
	return ("", 200)


# --- Metadata endpoints ---

@bp.route("/mods/<path:mod_name>/meta", methods=["GET"])
@_require_organizer
def get_mod_meta(mod_name: str):
	_, error = _validate_mod(mod_name)
	if error:
		return error
	return jsonify(db_helper.read_mod_metadata(mod_name))


@bp.route("/mods/<path:mod_name>/meta/<key>", methods=["GET"])
@_require_organizer
def get_mod_meta_key(mod_name: str, key: str):
	_, error = _validate_mod(mod_name)
	if error:
		return error
	value = db_helper.read_meta_value(mod_name, key)
	if value is None:
		return jsonify({"error": f"Key '{key}' not found"}), 404
	return jsonify({"mod": mod_name, "key": key, "value": value})


@bp.route("/mods/<path:mod_name>/meta", methods=["PATCH"])
@_require_organizer
def set_mod_meta(mod_name: str):
	_, error = _validate_mod(mod_name)
	if error:
		return error

	data = request.get_json()
	if not data:
		return jsonify({"error": "Request body required"}), 400

	values = data.get("data")
	if not values or not isinstance(values, dict):
		return jsonify({"error": "Missing or invalid 'data' parameter (must be object with key=value pairs)"}), 400

	context.get_task_executor().submit(db_helper.write_meta_values_fn(mod_name, values))
	return ("", 200)


@bp.route("/mods/<path:mod_name>/meta/<key>", methods=["PUT"])
@_require_organizer
def set_mod_meta_key(mod_name: str, key: str):
	_, error = _validate_mod(mod_name)
	if error:
		return error

	value, err = _get_json_field("value")
	if err:
		return err

	context.get_task_executor().submit(db_helper.write_meta_value_fn(mod_name, key, str(value)))
	return ("", 200)


@bp.route("/mods/<path:mod_name>/meta/<key>", methods=["DELETE"])
@_require_organizer
def delete_mod_meta_key(mod_name: str, key: str):
	_, error = _validate_mod(mod_name)
	if error:
		return error
	context.get_task_executor().submit(db_helper.delete_meta_key_fn(mod_name, key))
	return ("", 200)
