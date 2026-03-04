"""WebAPI package for Mod Organizer 2. Provides HTTP and WebSocket APIs for external applications."""
import sys
from pathlib import Path

_flask_lib = Path(__file__).parent.parent / "flask_lib"
if _flask_lib.exists() and str(_flask_lib) not in sys.path:
	sys.path.insert(0, str(_flask_lib))

from .plugin import WebAPIPlugin

__all__ = ["WebAPIPlugin"]
