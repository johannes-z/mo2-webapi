"""Thread-safe mod metadata (JSON file + in-memory cache)."""
import json
from typing import Callable, Dict, Optional
from threading import Lock

import mobase

from .. import config
from ..log import log

DB_PATH = config.PLUGIN_DIR / "mod_metadata.json"

_db_lock = Lock()
_db_cache: Optional[Dict[str, Dict[str, str]]] = None


def _load_cache() -> Dict[str, Dict[str, str]]:
	global _db_cache
	if _db_cache is not None:
		return _db_cache

	if not DB_PATH.exists():
		_db_cache = {}
		return _db_cache

	try:
		with open(DB_PATH, 'r', encoding='utf-8') as f:
			_db_cache = json.load(f)
	except Exception as e:
		log.error(f"Error reading metadata database: {e}")
		_db_cache = {}
	return _db_cache


def _flush() -> bool:
	try:
		with open(DB_PATH, 'w', encoding='utf-8') as f:
			json.dump(_db_cache, f, indent=2, ensure_ascii=False)
		return True
	except Exception as e:
		log.error(f"Error writing metadata database: {e}")
		return False


def init_db() -> None:
	try:
		with _db_lock:
			global _db_cache
			if not DB_PATH.exists():
				_db_cache = {}
				_flush()
				log.info(f"Created metadata database at {DB_PATH}")
				return
			_load_cache()
	except Exception as e:
		log.error(f"Error initializing database: {e}")


def read_meta_value(mod_name: str, key: str) -> Optional[str]:
	try:
		with _db_lock:
			data = _load_cache()
			return data.get(mod_name, {}).get(key)
	except Exception as e:
		log.error(f"Error reading metadata for '{mod_name}': {e}")
		return None


def read_mod_metadata(mod_name: str) -> Dict[str, str]:
	try:
		with _db_lock:
			data = _load_cache()
			return dict(data.get(mod_name, {}))
	except Exception as e:
		log.error(f"Error reading metadata for '{mod_name}': {e}")
		return {}


def read_all_metadata() -> Dict[str, Dict[str, str]]:
	try:
		with _db_lock:
			return dict(_load_cache())
	except Exception as e:
		log.error(f"Error reading all metadata: {e}")
		return {}


def write_meta_value(mod_name: str, key: str, value: str) -> bool:
	try:
		with _db_lock:
			data = _load_cache()
			data.setdefault(mod_name, {})[key] = str(value)
			return _flush()
	except Exception as e:
		log.error(f"Error writing metadata for '{mod_name}': {e}")
		return False


def write_meta_values(mod_name: str, values: Dict[str, str]) -> bool:
	try:
		with _db_lock:
			data = _load_cache()
			mod_data = data.setdefault(mod_name, {})
			for key, value in values.items():
				mod_data[key] = str(value)
			return _flush()
	except Exception as e:
		log.error(f"Error writing metadata for '{mod_name}': {e}")
		return False


def batch_update(updates: Dict[str, Dict[str, str]]) -> bool:
	if not updates:
		return True
	try:
		with _db_lock:
			data = _load_cache()
			for mod_name, values in updates.items():
				mod_data = data.setdefault(mod_name, {})
				mod_data.update(values)
			return _flush()
	except Exception as e:
		log.error(f"Error batch updating metadata: {e}")
		return False


def delete_meta_key(mod_name: str, key: str) -> bool:
	try:
		with _db_lock:
			data = _load_cache()
			if mod_name not in data or key not in data[mod_name]:
				return True
			del data[mod_name][key]
			if not data[mod_name]:
				del data[mod_name]
			return _flush()
	except Exception as e:
		log.error(f"Error deleting metadata key for '{mod_name}': {e}")
		return False


def rename_mod_metadata(old_name: str, new_name: str) -> bool:
	try:
		with _db_lock:
			data = _load_cache()
			if old_name not in data:
				return True
			data[new_name] = data.pop(old_name)
			return _flush()
	except Exception as e:
		log.error(f"Error renaming metadata '{old_name}' -> '{new_name}': {e}")
		return False


def delete_mod_metadata(mod_name: str) -> bool:
	try:
		with _db_lock:
			data = _load_cache()
			if mod_name not in data:
				return True
			del data[mod_name]
			return _flush()
	except Exception as e:
		log.error(f"Error deleting metadata for '{mod_name}': {e}")
		return False


def write_meta_value_fn(mod_name: str, key: str, value: str) -> Callable[[mobase.IOrganizer], bool]:
	def task(organizer: mobase.IOrganizer) -> bool:
		if not organizer.modList().getMod(mod_name):
			log.warning(f"Mod '{mod_name}' not found")
			return False
		return write_meta_value(mod_name, key, value)
	return task


def write_meta_values_fn(mod_name: str, values: Dict[str, str]) -> Callable[[mobase.IOrganizer], bool]:
	def task(organizer: mobase.IOrganizer) -> bool:
		if not organizer.modList().getMod(mod_name):
			log.warning(f"Mod '{mod_name}' not found")
			return False
		return write_meta_values(mod_name, values)
	return task


def delete_meta_key_fn(mod_name: str, key: str) -> Callable[[mobase.IOrganizer], bool]:
	def task(organizer: mobase.IOrganizer) -> bool:
		if not organizer.modList().getMod(mod_name):
			log.warning(f"Mod '{mod_name}' not found")
			return False
		return delete_meta_key(mod_name, key)
	return task
