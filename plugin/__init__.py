"""MO2 WebAPI Plugin.

A plugin for Mod Organizer 2 that provides HTTP and WebSocket APIs
for external applications to interact with mod management.

Note: This plugin runs persistent background server threads.
To pick up code changes, restart Mod Organizer 2.
"""
import sys
from pathlib import Path

_plugin_dir = Path(__file__).parent
if str(_plugin_dir) not in sys.path:
	sys.path.insert(0, str(_plugin_dir))

from webapi.plugin import WebAPIPlugin

__version__ = "1.1.0"
__author__ = "johannes-z"


def createPlugin() -> WebAPIPlugin:
	return WebAPIPlugin()
