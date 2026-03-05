from functools import wraps

import mobase
from fastapi import APIRouter
from fastapi.responses import JSONResponse, Response

from .. import context
from ..organizer import mod_helper, db_helper
from ..log import log
from ..schemas import (
	ConflictSummaryFull,
	ErrorResponse,
	ModConflictsDetail,
	ModInfo,
	ModListItem,
	ModMetaKeyResponse,
	ModMetaDataBody,
	ModMetaValueBody,
	ModNameBody,
	ModNamesBody,
	ModPriorityItem,
	ModRenameBody,
	ModSetPriorityBody,
	ModStateItem,
)

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

@router.get(
	"/mods/list",
	summary="Lightweight mod list",
	response_model=list[ModListItem],
	responses={
		200: {"description": "List of mods with name, isEnabled, priority only."},
		500: {"description": "Organizer not initialized.", "model": ErrorResponse},
	},
)
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


@router.get(
	"/mods",
	summary="All mods (full info)",
	response_model=list[ModInfo],
	responses={
		200: {"description": "All installed mods with full info (name, isEnabled, version, priority, nexusId, categories, conflicts, meta, etc.)."},
		500: {"description": "Organizer not initialized.", "model": ErrorResponse},
	},
)
@_require_organizer
async def get_mods():
	return _get_mods_filtered()


@router.get(
	"/mods/enabled",
	summary="Enabled mods only",
	response_model=list[ModInfo],
	responses={
		200: {"description": "Mods that are currently enabled."},
		500: {"description": "Organizer not initialized.", "model": ErrorResponse},
	},
)
@_require_organizer
async def get_enabled_mods():
	return _get_mods_filtered(lambda state: state & mobase.ModState.ACTIVE)


@router.get(
	"/mods/disabled",
	summary="Disabled mods only",
	response_model=list[ModInfo],
	responses={
		200: {"description": "Mods that are currently disabled."},
		500: {"description": "Organizer not initialized.", "model": ErrorResponse},
	},
)
@_require_organizer
async def get_disabled_mods():
	return _get_mods_filtered(lambda state: not (state & mobase.ModState.ACTIVE))


@router.get(
	"/mods/priority",
	summary="Mod priorities",
	response_model=list[ModPriorityItem],
	responses={
		200: {"description": "List of mod name and priority."},
		500: {"description": "Organizer not initialized.", "model": ErrorResponse},
	},
)
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


@router.get(
	"/mods/search",
	summary="Search mods by name",
	response_model=list[ModInfo],
	responses={
		200: {"description": "Mods whose name contains the query (case-insensitive)."},
		400: {"description": "Missing or empty query parameter 'q'.", "model": ErrorResponse},
		500: {"description": "Organizer not initialized.", "model": ErrorResponse},
	},
)
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


@router.get(
	"/mods/meta",
	summary="All mods metadata",
	response_model=dict[str, dict[str, str]],
	responses={
		200: {"description": "All mods' custom metadata as key-value per mod."},
		500: {"description": "Organizer not initialized.", "model": ErrorResponse},
	},
)
@_require_organizer
async def get_all_mods_meta():
	return db_helper.read_all_metadata()


# --- Conflicts ---

@router.get(
	"/mods/conflicts",
	summary="Conflict summaries (all mods)",
	response_model=dict[str, ConflictSummaryFull],
	responses={
		200: {"description": "Conflict summaries for all mods. Use ?refresh=true to force recompute."},
		500: {"description": "Organizer not initialized.", "model": ErrorResponse},
	},
)
@_require_organizer
async def get_all_conflicts(refresh: str = ""):
	organizer = context.get_organizer()
	if mod_helper.is_conflicts_stale() or refresh.lower() in ("true", "1"):
		mod_helper.compute_conflict_summaries(organizer)
	return mod_helper.get_all_conflict_summaries()


@router.get(
	"/mods/{mod_name:path}/conflicts",
	summary="File-level conflicts for one mod",
	response_model=ModConflictsDetail,
	responses={
		200: {"description": "Winning/losing file-level conflicts. Use ?refresh=true to recompute cache."},
		404: {"description": "Mod not found.", "model": ErrorResponse},
		500: {"description": "Organizer not initialized.", "model": ErrorResponse},
	},
)
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

@router.patch(
	"/mods/enable",
	summary="Enable a mod",
	responses={
		200: {"description": "Mod enabled (empty body)."},
		400: {"description": "Missing or invalid 'name'."},
		500: {"description": "Organizer not initialized."},
	},
)
@_require_organizer
async def enable_mod(body: ModNameBody):
	context.get_task_executor().submit(mod_helper.set_mod_active_fn(body.name, True))
	return Response(status_code=200)


@router.patch(
	"/mods/disable",
	summary="Disable a mod",
	responses={
		200: {"description": "Mod disabled (empty body)."},
		400: {"description": "Missing or invalid 'name'."},
		500: {"description": "Organizer not initialized."},
	},
)
@_require_organizer
async def disable_mod(body: ModNameBody):
	context.get_task_executor().submit(mod_helper.set_mod_active_fn(body.name, False))
	return Response(status_code=200)


@router.patch(
	"/mods/toggle",
	summary="Toggle mod enabled state",
	responses={
		200: {"description": "Mod state toggled (empty body)."},
		400: {"description": "Missing or invalid 'name'."},
		500: {"description": "Organizer not initialized."},
	},
)
@_require_organizer
async def toggle_mod(body: ModNameBody):
	context.get_task_executor().submit(mod_helper.toggle_mod_fn(body.name))
	return Response(status_code=200)


@router.patch(
	"/mods/state",
	summary="Set enabled state for multiple mods",
	responses={
		200: {"description": "States applied (empty body)."},
		400: {"description": "Invalid body (must be non-empty array of {name, state})."},
		500: {"description": "Organizer not initialized."},
	},
)
@_require_organizer
async def set_mods_state(body: list[ModStateItem]):
	if not body:
		return JSONResponse(content={"error": "Request body must be a non-empty array"}, status_code=400)
	for item in body:
		context.get_task_executor().submit(mod_helper.set_mod_active_fn(item.name, item.state))
	return Response(status_code=200)


@router.patch(
	"/mods/set-priority",
	summary="Set mod priority",
	responses={
		200: {"description": "Priority set (empty body)."},
		400: {"description": "Missing or invalid 'name' or 'priority'."},
		500: {"description": "Organizer not initialized."},
	},
)
@_require_organizer
async def set_priority(body: ModSetPriorityBody):
	context.get_task_executor().submit(mod_helper.set_mod_priority_fn(body.name, body.priority))
	return Response(status_code=200)


@router.patch(
	"/mods/{mod_name:path}/rename",
	summary="Rename a mod",
	responses={
		200: {"description": "Rename queued (empty body)."},
		400: {"description": "Missing or invalid 'newName'."},
		404: {"description": "Mod not found."},
		409: {"description": "Target name already exists."},
		500: {"description": "Organizer not initialized."},
	},
)
@_require_organizer
async def rename_mod(mod_name: str, body: ModRenameBody):
	_, error = _validate_mod(mod_name)
	if error:
		return error
	new_name = body.newName.strip()
	if not new_name:
		return JSONResponse(content={"error": "newName cannot be empty"}, status_code=400)
	if context.get_organizer().modList().getMod(new_name):
		return JSONResponse(content={"error": f"Mod '{new_name}' already exists"}, status_code=409)
	context.get_task_executor().submit(mod_helper.rename_mod_fn(mod_name, new_name))
	return Response(status_code=200)


@router.delete(
	"/mods/{mod_name:path}",
	summary="Uninstall/remove mod",
	responses={
		200: {"description": "Mod removed (empty body)."},
		404: {"description": "Mod not found."},
		500: {"description": "Organizer not initialized."},
	},
)
@_require_organizer
async def remove_mod(mod_name: str):
	_, error = _validate_mod(mod_name)
	if error:
		return error
	context.get_task_executor().submit(mod_helper.remove_mod_fn(mod_name))
	return Response(status_code=200)


@router.patch(
	"/mods/enable-batch",
	summary="Enable multiple mods",
	responses={
		200: {"description": "Mods enabled (empty body)."},
		400: {"description": "Missing or invalid 'names' array."},
		500: {"description": "Organizer not initialized."},
	},
)
@_require_organizer
async def enable_batch(body: ModNamesBody):
	for name in body.names:
		context.get_task_executor().submit(mod_helper.set_mod_active_fn(name, True))
	return Response(status_code=200)


@router.patch(
	"/mods/disable-batch",
	summary="Disable multiple mods",
	responses={
		200: {"description": "Mods disabled (empty body)."},
		400: {"description": "Missing or invalid 'names' array."},
		500: {"description": "Organizer not initialized."},
	},
)
@_require_organizer
async def disable_batch(body: ModNamesBody):
	for name in body.names:
		context.get_task_executor().submit(mod_helper.set_mod_active_fn(name, False))
	return Response(status_code=200)


# --- Metadata ---

@router.get(
	"/mods/{mod_name:path}/meta",
	summary="Get mod metadata",
	response_model=dict[str, str],
	responses={
		200: {"description": "All custom key-value metadata for the mod."},
		404: {"description": "Mod not found.", "model": ErrorResponse},
		500: {"description": "Organizer not initialized.", "model": ErrorResponse},
	},
)
@_require_organizer
async def get_mod_meta(mod_name: str):
	_, error = _validate_mod(mod_name)
	if error:
		return error
	return db_helper.read_mod_metadata(mod_name)


@router.get(
	"/mods/{mod_name:path}/meta/{key}",
	summary="Get one metadata key",
	response_model=ModMetaKeyResponse,
	responses={
		200: {"description": "Mod name, key, and value."},
		404: {"description": "Mod or key not found.", "model": ErrorResponse},
		500: {"description": "Organizer not initialized.", "model": ErrorResponse},
	},
)
@_require_organizer
async def get_mod_meta_key(mod_name: str, key: str):
	_, error = _validate_mod(mod_name)
	if error:
		return error
	value = db_helper.read_meta_value(mod_name, key)
	if value is None:
		return JSONResponse(content={"error": f"Key '{key}' not found"}, status_code=404)
	return {"mod": mod_name, "key": key, "value": value}


@router.patch(
	"/mods/{mod_name:path}/meta",
	summary="Set mod metadata (merge)",
	responses={
		200: {"description": "Metadata updated (empty body)."},
		400: {"description": "Missing or invalid 'data' object."},
		404: {"description": "Mod not found."},
		500: {"description": "Organizer not initialized."},
	},
)
@_require_organizer
async def set_mod_meta(mod_name: str, body: ModMetaDataBody):
	_, error = _validate_mod(mod_name)
	if error:
		return error
	context.get_task_executor().submit(db_helper.write_meta_values_fn(mod_name, body.data))
	return Response(status_code=200)


@router.put(
	"/mods/{mod_name:path}/meta/{key}",
	summary="Set one metadata key",
	responses={
		200: {"description": "Value set (empty body)."},
		400: {"description": "Missing 'value'."},
		404: {"description": "Mod not found."},
		500: {"description": "Organizer not initialized."},
	},
)
@_require_organizer
async def set_mod_meta_key(mod_name: str, key: str, body: ModMetaValueBody):
	_, error = _validate_mod(mod_name)
	if error:
		return error
	context.get_task_executor().submit(db_helper.write_meta_value_fn(mod_name, key, str(body.value)))
	return Response(status_code=200)


@router.delete(
	"/mods/{mod_name:path}/meta/{key}",
	summary="Delete one metadata key",
	responses={
		200: {"description": "Key removed (empty body)."},
		404: {"description": "Mod not found."},
		500: {"description": "Organizer not initialized."},
	},
)
@_require_organizer
async def delete_mod_meta_key(mod_name: str, key: str):
	_, error = _validate_mod(mod_name)
	if error:
		return error
	context.get_task_executor().submit(db_helper.delete_meta_key_fn(mod_name, key))
	return Response(status_code=200)


# --- Single mod info (must be last: /mods/{mod_name:path} would match /mods/list etc.) ---

@router.get(
	"/mods/{mod_name:path}",
	summary="Single mod info",
	response_model=ModInfo,
	responses={
		200: {"description": "Full mod info (name, isEnabled, version, priority, conflicts, meta, etc.)."},
		404: {"description": "Mod not found.", "model": ErrorResponse},
		500: {"description": "Organizer not initialized.", "model": ErrorResponse},
	},
)
@_require_organizer
async def get_mod_info_endpoint(mod_name: str):
	mod_info = mod_helper.get_mod_info(context.get_organizer(), mod_name)
	if not mod_info:
		return JSONResponse(content={"error": f"Mod '{mod_name}' not found"}, status_code=404)
	return mod_info
