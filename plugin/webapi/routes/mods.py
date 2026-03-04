from functools import wraps

import mobase
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, Response

from .. import context
from ..organizer import mod_helper, db_helper
from ..log import log

router = APIRouter(tags=["Mods"])


def _require_organizer(f):
	@wraps(f)
	async def wrapper(*args, **kwargs):
		if not context.get_organizer():
			return JSONResponse(content={"error": "Organizer not initialized"}, status_code=500)
		return await f(*args, **kwargs)
	return wrapper


def _validate_mod(mod_name: str):
	organizer = context.get_organizer()
	if not organizer:
		return None, JSONResponse(content={"error": "Organizer not initialized"}, status_code=500)
	mod_list = organizer.modList()
	mod = mod_list.getMod(mod_name)
	if not mod:
		return None, JSONResponse(content={"error": f"Mod '{mod_name}' not found"}, status_code=404)
	return mod, None


def _get_json_field(data: dict | None, field: str, required_type=None):
	if data is None:
		data = {}
	value = data.get(field)
	if value is None:
		return None, JSONResponse(content={"error": f"Missing '{field}' parameter"}, status_code=400)
	if required_type and not isinstance(value, required_type):
		return None, JSONResponse(content={"error": f"Invalid '{field}' parameter (must be {required_type.__name__})"}, status_code=400)
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
	try:
		return list(mod_list.allModsByProfilePriority())
	except RuntimeError as e:
		log.warning(f"allModsByProfilePriority failed; using unsorted allMods: {e}")
		return list(mod_list.allMods())


# --- List (specific paths first) ---

@router.get("/mods/list")
@_require_organizer
async def get_mods_list():
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
	return mods


@router.get("/mods")
@_require_organizer
async def get_mods():
	return _get_mods_filtered()


@router.get("/mods/enabled")
@_require_organizer
async def get_enabled_mods():
	return _get_mods_filtered(lambda state: state & mobase.ModState.ACTIVE)


@router.get("/mods/disabled")
@_require_organizer
async def get_disabled_mods():
	return _get_mods_filtered(lambda state: not (state & mobase.ModState.ACTIVE))


@router.get("/mods/priority")
@_require_organizer
async def get_mods_priority():
	organizer = context.get_organizer()
	mod_list = organizer.modList()
	priorities = [
		{"name": name, "priority": mod_list.priority(name)}
		for name in _get_mod_names_by_priority(mod_list)
		if mod_list.getMod(name)
	]
	return priorities


@router.get("/mods/search")
@_require_organizer
async def search_mods(q: str = ""):
	query = q.lower()
	if not query:
		return JSONResponse(content={"error": "Missing 'q' query parameter"}, status_code=400)
	organizer = context.get_organizer()
	mod_list = organizer.modList()
	mods = [
		info for name in _get_mod_names_by_priority(mod_list)
		if query in name.lower()
		and (info := mod_helper.get_mod_info(organizer, name))
	]
	return mods


@router.get("/mods/meta")
@_require_organizer
async def get_all_mods_meta():
	return db_helper.read_all_metadata()


# --- Conflicts ---

@router.get("/mods/conflicts")
@_require_organizer
async def get_all_conflicts(refresh: str = ""):
	organizer = context.get_organizer()
	if mod_helper.is_conflicts_stale() or refresh.lower() in ("true", "1"):
		mod_helper.compute_conflict_summaries(organizer)
	return mod_helper.get_all_conflict_summaries()


@router.get("/mods/{mod_name:path}/conflicts")
@_require_organizer
async def get_mod_conflicts(mod_name: str, refresh: str = ""):
	_, error = _validate_mod(mod_name)
	if error:
		return error
	organizer = context.get_organizer()
	if mod_helper.is_conflicts_stale() or refresh.lower() in ("true", "1"):
		mod_helper.compute_conflict_summaries(organizer)
	return mod_helper.get_mod_conflicts(organizer, mod_name)


# --- State modification ---

async def _body_json(request: Request) -> dict | list | None:
	try:
		return await request.json()
	except Exception:
		return None


@router.patch("/mods/enable")
@_require_organizer
async def enable_mod(request: Request):
	data = await _body_json(request)
	name, error = _get_json_field(data, "name")
	if error:
		return error
	context.get_task_executor().submit(mod_helper.set_mod_active_fn(name, True))
	return Response(status_code=200)


@router.patch("/mods/disable")
@_require_organizer
async def disable_mod(request: Request):
	data = await _body_json(request)
	name, error = _get_json_field(data, "name")
	if error:
		return error
	context.get_task_executor().submit(mod_helper.set_mod_active_fn(name, False))
	return Response(status_code=200)


@router.patch("/mods/toggle")
@_require_organizer
async def toggle_mod(request: Request):
	data = await _body_json(request)
	name, error = _get_json_field(data, "name")
	if error:
		return error
	context.get_task_executor().submit(mod_helper.toggle_mod_fn(name))
	return Response(status_code=200)


@router.patch("/mods/state")
@_require_organizer
async def set_mods_state(request: Request):
	data = await _body_json(request)
	if not isinstance(data, list) or not data:
		return JSONResponse(content={"error": "Request body must be a non-empty array"}, status_code=400)
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
		return JSONResponse(content={"errors": errors}, status_code=400)
	return Response(status_code=200)


@router.patch("/mods/set-priority")
@_require_organizer
async def set_priority(request: Request):
	data = await _body_json(request) or {}
	name, error = _get_json_field(data, "name")
	if error:
		return error
	priority = data.get("priority")
	if priority is None:
		return JSONResponse(content={"error": "Missing 'priority' parameter"}, status_code=400)
	try:
		priority = int(priority)
	except (ValueError, TypeError):
		return JSONResponse(content={"error": "Invalid priority value, must be an integer"}, status_code=400)
	context.get_task_executor().submit(mod_helper.set_mod_priority_fn(name, priority))
	return Response(status_code=200)


@router.patch("/mods/{mod_name:path}/rename")
@_require_organizer
async def rename_mod(mod_name: str, request: Request):
	_, error = _validate_mod(mod_name)
	if error:
		return error
	data = await _body_json(request)
	new_name, error = _get_json_field(data, "newName")
	if error:
		return error
	if not new_name or not str(new_name).strip():
		return JSONResponse(content={"error": "newName cannot be empty"}, status_code=400)
	new_name = str(new_name).strip()
	if context.get_organizer().modList().getMod(new_name):
		return JSONResponse(content={"error": f"Mod '{new_name}' already exists"}, status_code=409)
	context.get_task_executor().submit(mod_helper.rename_mod_fn(mod_name, new_name))
	return Response(status_code=200)


@router.delete("/mods/{mod_name:path}")
@_require_organizer
async def remove_mod(mod_name: str):
	_, error = _validate_mod(mod_name)
	if error:
		return error
	context.get_task_executor().submit(mod_helper.remove_mod_fn(mod_name))
	return Response(status_code=200)


@router.patch("/mods/enable-batch")
@_require_organizer
async def enable_batch(request: Request):
	data = await _body_json(request)
	names, error = _get_json_field(data, "names", required_type=list)
	if error:
		return error
	for name in names:
		context.get_task_executor().submit(mod_helper.set_mod_active_fn(name, True))
	return Response(status_code=200)


@router.patch("/mods/disable-batch")
@_require_organizer
async def disable_batch(request: Request):
	data = await _body_json(request)
	names, error = _get_json_field(data, "names", required_type=list)
	if error:
		return error
	for name in names:
		context.get_task_executor().submit(mod_helper.set_mod_active_fn(name, False))
	return Response(status_code=200)


# --- Metadata ---

@router.get("/mods/{mod_name:path}/meta")
@_require_organizer
async def get_mod_meta(mod_name: str):
	_, error = _validate_mod(mod_name)
	if error:
		return error
	return db_helper.read_mod_metadata(mod_name)


@router.get("/mods/{mod_name:path}/meta/{key}")
@_require_organizer
async def get_mod_meta_key(mod_name: str, key: str):
	_, error = _validate_mod(mod_name)
	if error:
		return error
	value = db_helper.read_meta_value(mod_name, key)
	if value is None:
		return JSONResponse(content={"error": f"Key '{key}' not found"}, status_code=404)
	return {"mod": mod_name, "key": key, "value": value}


@router.patch("/mods/{mod_name:path}/meta")
@_require_organizer
async def set_mod_meta(mod_name: str, request: Request):
	_, error = _validate_mod(mod_name)
	if error:
		return error
	data = await _body_json(request)
	if not data:
		return JSONResponse(content={"error": "Request body required"}, status_code=400)
	values = data.get("data")
	if not values or not isinstance(values, dict):
		return JSONResponse(content={"error": "Missing or invalid 'data' parameter (must be object with key=value pairs)"}, status_code=400)
	context.get_task_executor().submit(db_helper.write_meta_values_fn(mod_name, values))
	return Response(status_code=200)


@router.put("/mods/{mod_name:path}/meta/{key}")
@_require_organizer
async def set_mod_meta_key(mod_name: str, key: str, request: Request):
	_, error = _validate_mod(mod_name)
	if error:
		return error
	data = await _body_json(request)
	value, err = _get_json_field(data, "value")
	if err:
		return err
	context.get_task_executor().submit(db_helper.write_meta_value_fn(mod_name, key, str(value)))
	return Response(status_code=200)


@router.delete("/mods/{mod_name:path}/meta/{key}")
@_require_organizer
async def delete_mod_meta_key(mod_name: str, key: str):
	_, error = _validate_mod(mod_name)
	if error:
		return error
	context.get_task_executor().submit(db_helper.delete_meta_key_fn(mod_name, key))
	return Response(status_code=200)


# --- Single mod info (must be last: /mods/{mod_name:path} would match /mods/list etc.) ---

@router.get("/mods/{mod_name:path}")
@_require_organizer
async def get_mod_info_endpoint(mod_name: str):
	mod_info = mod_helper.get_mod_info(context.get_organizer(), mod_name)
	if not mod_info:
		return JSONResponse(content={"error": f"Mod '{mod_name}' not found"}, status_code=404)
	return mod_info
