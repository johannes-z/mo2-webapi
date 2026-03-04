"""Config from config.ini in plugin root. Creates file with defaults on first run."""
import configparser
from pathlib import Path

PLUGIN_DIR = Path(__file__).parent.parent

_DEFAULTS = {
	"server": {
		"http_port": "5000",
		"websocket_port": "5001",
	},
	"frontend": {
		"dist_dir": "dist",
	},
	"logging": {
		"level": "INFO",
	},
	"cors": {
		"allow_origin": "*",
		"allow_methods": "GET, POST, PUT, PATCH, DELETE, OPTIONS",
		"allow_headers": "Content-Type",
	},
	"dev": {
		"dev_endpoint": "false",
	},
}

_CONFIG_PATH = PLUGIN_DIR / "config.ini"


def _load_config() -> configparser.ConfigParser:
	cfg = configparser.ConfigParser()
	for section, values in _DEFAULTS.items():
		cfg[section] = values

	if _CONFIG_PATH.exists():
		cfg.read(_CONFIG_PATH, encoding="utf-8")
	else:
		with open(_CONFIG_PATH, "w", encoding="utf-8") as f:
			cfg.write(f)

	return cfg


_cfg = _load_config()

# Server
HTTP_PORT = _cfg.getint("server", "http_port")
WEBSOCKET_PORT = _cfg.getint("server", "websocket_port")

# Frontend: use combined "dist" (frontend + api-docs); migrate old "frontend/dist"
_raw_dist = _cfg.get("frontend", "dist_dir")
if _raw_dist.strip().lower() in ("frontend/dist", "frontend\\dist"):
	FRONTEND_DIST_DIR = "dist"
	_cfg.set("frontend", "dist_dir", "dist")
	try:
		with open(_CONFIG_PATH, "w", encoding="utf-8") as f:
			_cfg.write(f)
	except OSError:
		pass
else:
	FRONTEND_DIST_DIR = _raw_dist

# Logging (DEBUG, INFO, WARNING, ERROR, CRITICAL)
LOG_LEVEL = _cfg.get("logging", "level")

# CORS
CORS_ALLOW_ORIGIN = _cfg.get("cors", "allow_origin")
CORS_ALLOW_METHODS = _cfg.get("cors", "allow_methods")
CORS_ALLOW_HEADERS = _cfg.get("cors", "allow_headers")

# API
API_VERSION = "1.0.0"
