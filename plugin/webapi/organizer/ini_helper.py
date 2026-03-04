"""Helper functions for reading and writing mod meta.ini files.

Provides functions to read and write key=value pairs to the [mo2web] section
of mod meta.ini files.
"""
import configparser
from pathlib import Path
from typing import Callable, Dict, Optional

import mobase

from ..log import log

SECTION = "mo2web"


def _get_meta_ini_path(mod: mobase.IModInterface) -> Optional[Path]:
	try:
		mod_path = Path(mod.absolutePath())
		if not mod_path.exists():
			return None
		return mod_path / "meta.ini"
	except Exception as e:
		log.error(f"Error getting meta.ini path: {e}")
		return None


def _read_config(mod: mobase.IModInterface) -> tuple[Optional[configparser.ConfigParser], Optional[Path]]:
	"""Read a mod's meta.ini into a ConfigParser.

	Returns:
		(config, path) tuple, or (None, None) if path is invalid.
	"""
	meta_path = _get_meta_ini_path(mod)
	if not meta_path:
		return None, None

	cfg = configparser.ConfigParser()
	if meta_path.exists():
		cfg.read(meta_path, encoding='utf-8')
	return cfg, meta_path


def _write_config(cfg: configparser.ConfigParser, meta_path: Path) -> bool:
	try:
		with open(meta_path, 'w', encoding='utf-8') as f:
			cfg.write(f)
		return True
	except Exception as e:
		log.error(f"Error writing meta.ini at {meta_path}: {e}")
		return False


def read_meta_value(mod: mobase.IModInterface, key: str, section: str = SECTION) -> Optional[str]:
	try:
		cfg, _ = _read_config(mod)
		if not cfg:
			return None
		if cfg.has_option(section, key):
			return cfg.get(section, key)
		return None
	except Exception as e:
		log.error(f"Error reading meta.ini for '{mod.name()}': {e}")
		return None


def read_meta_section(mod: mobase.IModInterface, section: str = SECTION) -> Dict[str, str]:
	try:
		cfg, _ = _read_config(mod)
		if not cfg:
			return {}
		if cfg.has_section(section):
			return dict(cfg.items(section))
		return {}
	except Exception as e:
		log.error(f"Error reading meta.ini section for '{mod.name()}': {e}")
		return {}


def write_meta_values(mod: mobase.IModInterface, values: Dict[str, str], section: str = SECTION) -> bool:
	"""Write one or more key=value pairs to a mod's meta.ini.

	Creates the file and section if they don't exist.
	"""
	try:
		cfg, meta_path = _read_config(mod)
		if not cfg or not meta_path:
			log.warning(f"Cannot get meta.ini path for mod '{mod.name()}'")
			return False

		if not cfg.has_section(section):
			cfg.add_section(section)

		for key, value in values.items():
			cfg.set(section, key, str(value))

		return _write_config(cfg, meta_path)
	except Exception as e:
		log.error(f"Error writing to meta.ini for '{mod.name()}': {e}")
		return False


def write_meta_value(mod: mobase.IModInterface, key: str, value: str, section: str = SECTION) -> bool:
	return write_meta_values(mod, {key: value}, section)


def delete_meta_key(mod: mobase.IModInterface, key: str, section: str = SECTION) -> bool:
	try:
		cfg, meta_path = _read_config(mod)
		if not cfg or not meta_path or not meta_path.exists():
			return True

		if not cfg.has_section(section) or not cfg.has_option(section, key):
			return True

		cfg.remove_option(section, key)
		if not cfg.options(section):
			cfg.remove_section(section)

		return _write_config(cfg, meta_path)
	except Exception as e:
		log.error(f"Error deleting key from meta.ini for '{mod.name()}': {e}")
		return False


# Task function factories for use with TaskExecutor

def _resolve_mod(organizer: mobase.IOrganizer, mod_name: str) -> Optional[mobase.IModInterface]:
	mod = organizer.modList().getMod(mod_name)
	if not mod:
		log.warning(f"Mod '{mod_name}' not found")
	return mod


def write_meta_value_fn(mod_name: str, key: str, value: str, section: str = SECTION) -> Callable[[mobase.IOrganizer], bool]:
	def task(organizer: mobase.IOrganizer) -> bool:
		mod = _resolve_mod(organizer, mod_name)
		return write_meta_value(mod, key, value, section) if mod else False
	return task


def write_meta_values_fn(mod_name: str, values: Dict[str, str], section: str = SECTION) -> Callable[[mobase.IOrganizer], bool]:
	def task(organizer: mobase.IOrganizer) -> bool:
		mod = _resolve_mod(organizer, mod_name)
		return write_meta_values(mod, values, section) if mod else False
	return task


def delete_meta_key_fn(mod_name: str, key: str, section: str = SECTION) -> Callable[[mobase.IOrganizer], bool]:
	def task(organizer: mobase.IOrganizer) -> bool:
		mod = _resolve_mod(organizer, mod_name)
		return delete_meta_key(mod, key, section) if mod else False
	return task
