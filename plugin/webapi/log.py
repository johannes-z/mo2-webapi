"""TimedRotatingFileHandler, daily logs in logs/, backupCount=7."""
import logging
from logging.handlers import TimedRotatingFileHandler

from . import config

LOG_DIR = config.PLUGIN_DIR / "logs"
LOG_FILE = LOG_DIR / "webapi.log"
LOG_FORMAT = "%(asctime)s [%(levelname)s] %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def _setup_logger() -> logging.Logger:
	logger = logging.getLogger("webapi")
	level = getattr(logging, config.LOG_LEVEL.upper(), logging.INFO)
	logger.setLevel(level)

	if not logger.handlers:
		LOG_DIR.mkdir(exist_ok=True)
		handler = TimedRotatingFileHandler(
			LOG_FILE, when="midnight", backupCount=7, encoding="utf-8",
		)
		handler.suffix = "%Y-%m-%d"
		handler.setFormatter(logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT))
		logger.addHandler(handler)

	return logger


log = _setup_logger()
