"""WebAPI package for Mod Organizer 2. Provides HTTP and WebSocket APIs for external applications."""
import sys
from pathlib import Path

_webapi_lib = Path(__file__).parent.parent / "webapi_lib"
if _webapi_lib.exists() and str(_webapi_lib) not in sys.path:
	sys.path.insert(0, str(_webapi_lib))

from .plugin import WebAPIPlugin

__all__ = ["WebAPIPlugin"]
