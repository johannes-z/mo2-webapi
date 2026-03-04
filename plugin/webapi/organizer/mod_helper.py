"""Mod operations, conflict detection via VFS, task factories for main-thread dispatch."""
import struct
import traceback
from datetime import datetime
from pathlib import Path
from typing import Callable, Dict, Optional

import mobase

from . import db_helper
from ..log import log

DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

_conflict_cache: Dict[str, Dict] = {}
_conflict_file_origins: list[tuple[str, list[str]]] = []
_conflicts_stale = True
_file_count_cache: Dict[str, int] = {}

_EMPTY_CONFLICT = {
	"overwriting": 0,
	"overridden": 0,
	"overwritingMods": [],
	"overriddenByMods": [],
}


# --- Conflict detection ---

def invalidate_conflict_cache() -> None:
	global _conflicts_stale
	_conflicts_stale = True


def is_conflicts_stale() -> bool:
	return _conflicts_stale


def _count_bsa_entries(bsa_path: Path) -> int:
	try:
		with open(bsa_path, 'rb') as f:
			header = f.read(24)
			if len(header) < 24 or header[:4] != b'BSA\x00':
				return 0
			return struct.unpack_from('<I', header, 20)[0]
	except Exception:
		return 0


def _count_foreign_mod_files(mod_name: str, organizer: mobase.IOrganizer) -> int:
	data_dir = Path(organizer.managedGame().dataDirectory().absolutePath())
	mod_basename = mod_name.split(': ')[-1] if ': ' in mod_name else mod_name
	count = 0

	for ext in ('.esm', '.esp', '.esl'):
		if (data_dir / f"{mod_basename}{ext}").exists():
			count += 1

	for bsa_file in data_dir.glob(f"{mod_basename}*.bsa"):
		count += _count_bsa_entries(bsa_file)

	return count


def _extract_file_data(file_infos) -> list[tuple[str, list[str]]]:
	# Extract C++ FileInfo to tuples immediately; try origins_/filePath_ if origins/filePath missing
	result = []
	errors = 0
	for fi in file_infos:
		try:
			origins = getattr(fi, 'origins', None)
			if origins is None:
				origins = getattr(fi, 'origins_', None)
			if not origins:
				continue
			path = getattr(fi, 'filePath', None) or getattr(fi, 'filePath_', '')
			result.append((str(path), list(origins)))
		except Exception:
			errors += 1
	if errors:
		log.warning(f"Failed to extract {errors} file info entries")
	return result


def _scan_vfs_recursive(organizer: mobase.IOrganizer) -> list[tuple[str, list[str]]]:
	# findFileInfos(path) is not recursive; recurse via listDirectories
	result = []
	dir_count = 0

	def scan_dir(path: str) -> None:
		nonlocal dir_count
		dir_count += 1
		try:
			infos = organizer.findFileInfos(path, lambda _: True)
			result.extend(_extract_file_data(infos))
		except Exception as e:
			log.warning(f"Error scanning VFS path '{path}': {e}")
		try:
			for subdir in organizer.listDirectories(path):
				scan_dir(f"{path}/{subdir}" if path else subdir)
		except Exception:
			pass

	scan_dir("")
	log.info(f"VFS recursive scan: {len(result)} files across {dir_count} directories")
	return result

def _build_summaries(files_data: list[tuple[str, list[str]]]) -> tuple[Dict[str, Dict], Dict[str, int], int]:
	# origins[0] = winning mod (highest priority)
	summaries: Dict[str, Dict] = {}
	file_counts: Dict[str, int] = {}
	conflict_count = 0

	for path, origins in files_data:
		for origin in origins:
			file_counts[origin] = file_counts.get(origin, 0) + 1

		if len(origins) < 2:
			continue

		conflict_count += 1

		winner = origins[0]
		losers = origins[1:]

		entry = summaries.setdefault(winner, {
			"overwriting": 0, "overridden": 0,
			"overwritingMods": set(), "overriddenByMods": set(),
		})
		entry["overwriting"] += 1
		entry["overwritingMods"].update(losers)

		for loser in losers:
			entry = summaries.setdefault(loser, {
				"overwriting": 0, "overridden": 0,
				"overwritingMods": set(), "overriddenByMods": set(),
			})
			entry["overridden"] += 1
			entry["overriddenByMods"].add(winner)

	return summaries, file_counts, conflict_count


def compute_conflict_summaries(organizer: mobase.IOrganizer) -> Dict[str, Dict]:
	global _conflict_cache, _conflict_file_origins, _file_count_cache, _conflicts_stale
	try:
		log.info("Computing mod conflict summaries...")
		files_data = _scan_vfs_recursive(organizer)
		summaries, file_counts, conflict_count = _build_summaries(files_data)
		mod_list = organizer.modList()
		for mod_name in mod_list.allMods():
			if mod_name in file_counts:
				continue
			mod = mod_list.getMod(mod_name)
			if mod and mod.isForeign():
				file_counts[mod_name] = _count_foreign_mod_files(mod_name, organizer)
		for data in summaries.values():
			data["overwritingMods"] = sorted(data["overwritingMods"])
			data["overriddenByMods"] = sorted(data["overriddenByMods"])
		_conflict_cache = summaries
		_conflict_file_origins = files_data
		_file_count_cache.clear()
		_file_count_cache.update(file_counts)
		_conflicts_stale = False
		log.info(f"Conflict summaries complete: {len(files_data)} files, {conflict_count} conflicted, {len(summaries)} mods affected")
		return summaries
	except Exception as e:
		log.error(f"Error computing conflict summaries: {e}")
		log.error(traceback.format_exc())
		return _conflict_cache


def get_conflict_summary(mod_name: str) -> Dict:
	return _conflict_cache.get(mod_name, dict(_EMPTY_CONFLICT))


def get_file_count(mod_name: str) -> int:
	return _file_count_cache.get(mod_name, 0)


def get_all_conflict_summaries() -> Dict[str, Dict]:
	return dict(_conflict_cache)


def get_mod_conflicts(organizer: mobase.IOrganizer, mod_name: str) -> Dict:
	if not organizer.modList().getMod(mod_name):
		return {"winning": [], "losing": [], "winningCount": 0, "losingCount": 0}
	if _conflicts_stale:
		compute_conflict_summaries(organizer)
	winning = []
	losing = []
	for filepath, origins in _conflict_file_origins:
		if len(origins) < 2 or mod_name not in origins:
			continue
		if origins[0] == mod_name:
			winning.append({"file": filepath, "overwriting": origins[1:]})
		else:
			losing.append({"file": filepath, "overwrittenBy": origins[0]})
	return {
		"winning": winning,
		"losing": losing,
		"winningCount": len(winning),
		"losingCount": len(losing),
	}


# --- Installation date ---

def _get_installation_date(mod: mobase.IModInterface, mod_name: str, organizer: mobase.IOrganizer) -> Optional[str]:
	try:
		inst_file = mod.installationFile()
		if inst_file:
			inst_path = Path(inst_file)
			if inst_path.exists():
				return datetime.fromtimestamp(inst_path.stat().st_mtime).strftime(DATE_FORMAT)

		if mod.isForeign():
			data_dir = Path(organizer.managedGame().dataDirectory().absolutePath())
			mod_basename = mod_name.split(': ')[-1] if ': ' in mod_name else mod_name
			for ext in ('.esm', '.esp', '.esl'):
				plugin_file = data_dir / f"{mod_basename}{ext}"
				if plugin_file.exists():
					return datetime.fromtimestamp(plugin_file.stat().st_mtime).strftime(DATE_FORMAT)
		else:
			mod_path = Path(mod.absolutePath())
			if mod_path.exists():
				return datetime.fromtimestamp(mod_path.stat().st_ctime).strftime(DATE_FORMAT)
	except Exception as e:
		log.warning(f"Failed to get installation date for '{mod_name}': {e}")
	return None


def populate_installation_metadata(organizer: mobase.IOrganizer) -> None:
	try:
		log.info("Populating installation metadata for mods...")
		mod_list = organizer.modList()
		updates = {}
		total = 0
		found = 0

		for mod_name in mod_list.allMods():
			total += 1
			mod = mod_list.getMod(mod_name)
			if not mod:
				continue

			values = {}
			inst_file = mod.installationFile()
			if inst_file:
				values["installationFile"] = inst_file

			install_date = _get_installation_date(mod, mod_name, organizer)
			if install_date:
				values["installDate"] = install_date
				found += 1

			if values:
				updates[mod_name] = values

		if updates:
			success = db_helper.batch_update(updates)
			if success:
				log.info(f"Updated installation metadata for {len(updates)}/{total} mods ({total - found} dates unavailable)")
			else:
				log.error("Failed to write installation metadata to database!")
		else:
			log.info(f"No installation metadata to update for {total} mods")

	except Exception as e:
		log.error(f"Error populating installation metadata: {e}")


# --- Mod info ---

def _check_state_flag(state: int, flag_name: str) -> bool:
	flag = getattr(mobase.ModState, flag_name, None)
	return bool(state & flag) if flag is not None else False


def get_mod_info(organizer: mobase.IOrganizer, mod_name: str) -> Optional[Dict]:
	try:
		mod_list = organizer.modList()
		mod = mod_list.getMod(mod_name)
		if not mod:
			return None

		state = mod_list.state(mod_name)
		conflict = get_conflict_summary(mod_name)

		return {
			"name": mod.name(),
			"isEnabled": bool(state & mobase.ModState.ACTIVE),
			"version": mod.version().displayString(),
			"priority": mod_list.priority(mod_name),
			"isSeparator": mod.isSeparator(),
			"isForeign": mod.isForeign(),
			"isOverwrite": mod.isOverwrite(),
			"nexusId": mod.nexusId(),
			"categories": list(mod.categories()),
			"comments": mod.comments(),
			"hasLooseFiles": _check_state_flag(state, "LOOSE_FILES"),
			"isValid": _check_state_flag(state, "VALID"),
			"isEmpty": _check_state_flag(state, "EMPTY"),
			"fileCount": get_file_count(mod_name),
			"conflicts": {
				"overwriting": conflict["overwriting"],
				"overridden": conflict["overridden"],
			},
			"meta": db_helper.read_mod_metadata(mod_name),
		}
	except Exception as e:
		log.error(f"Error getting mod info for '{mod_name}': {e}")
		return None


# --- Task closure factories ---

def set_mod_active_fn(mod_name: str, active: bool) -> Callable[[mobase.IOrganizer], bool]:
	def task(organizer: mobase.IOrganizer) -> bool:
		return organizer.modList().setActive(mod_name, active)
	return task


def toggle_mod_fn(mod_name: str) -> Callable[[mobase.IOrganizer], bool]:
	def task(organizer: mobase.IOrganizer) -> bool:
		mod_list = organizer.modList()
		is_active = bool(mod_list.state(mod_name) & mobase.ModState.ACTIVE)
		return mod_list.setActive(mod_name, not is_active)
	return task


def rename_mod_fn(old_name: str, new_name: str) -> Callable[[mobase.IOrganizer], bool]:
	def task(organizer: mobase.IOrganizer) -> bool:
		mod_list = organizer.modList()
		if not mod_list.getMod(old_name):
			log.warning(f"Rename failed: mod '{old_name}' not found")
			return False
		try:
			result = mod_list.renameMod(old_name, new_name)
		except AttributeError:
			log.error("renameMod not available in this MO2 version")
			return False
		if not result:
			log.warning(f"renameMod('{old_name}', '{new_name}') returned False")
			return False
		db_helper.rename_mod_metadata(old_name, new_name)
		invalidate_conflict_cache()
		# Broadcast via websocket (lazy import avoids circular dependency)
		from ..server_websocket import broadcast
		new_info = get_mod_info(organizer, new_name)
		broadcast({
			"event": "mod_renamed",
			"oldName": old_name,
			"newName": new_name,
			"mod": new_info,
		})
		return True
	return task


def remove_mod_fn(mod_name: str) -> Callable[[mobase.IOrganizer], bool]:
	def task(organizer: mobase.IOrganizer) -> bool:
		mod = organizer.modList().getMod(mod_name)
		if not mod:
			log.warning(f"Remove failed: mod '{mod_name}' not found")
			return False
		try:
			result = organizer.removeMod(mod)
		except AttributeError:
			log.error("removeMod not available in this MO2 version")
			return False
		if not result:
			log.warning(f"removeMod('{mod_name}') returned False")
			return False
		db_helper.delete_mod_metadata(mod_name)
		invalidate_conflict_cache()
		return True
	return task


def set_mod_priority_fn(mod_name: str, priority: int) -> Callable[[mobase.IOrganizer], bool]:
	def task(organizer: mobase.IOrganizer) -> bool:
		return organizer.modList().setPriority(mod_name, priority)
	return task
