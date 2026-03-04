"""WebAPI Plugin for Mod Organizer 2. HTTP and WebSocket APIs for external apps."""
import threading
import time

import mobase

from . import config, context, server_http, server_websocket
from .log import log
from .task_executor import SignalTaskExecutor, TaskExecutor


class WebAPIPlugin(mobase.IPlugin):
	def __init__(self) -> None:
		super().__init__()
		self._organizer: mobase.IOrganizer | None = None
		self._task_executor: TaskExecutor | None = None
		self._server_thread: threading.Thread | None = None
		self._websocket_thread: threading.Thread | None = None
		self._http_port = config.HTTP_PORT
		self._websocket_port = config.WEBSOCKET_PORT

	def init(self, organizer: mobase.IOrganizer) -> bool:
		log.info("WebAPI Plugin initializing...")
		try:
			self._organizer = organizer
			from .organizer import db_helper, mod_helper
			db_helper.init_db()
			self._register_invalidation_hooks(organizer, mod_helper)
			self._setup_task_executor(organizer)
			frontend_dist = config.PLUGIN_DIR / config.FRONTEND_DIST_DIR
			if frontend_dist.exists():
				log.info(f"Frontend directory: {frontend_dist}")
			else:
				log.info(f"No frontend dist at {frontend_dist}, API-only mode")
			context.set_context(organizer, self._task_executor, frontend_dist if frontend_dist.exists() else None)
			self._start_background_init(organizer, mod_helper)
			log.info("WebAPIPlugin initialized successfully")
			return True
		except Exception as e:
			log.error(f"Failed to initialize WebAPIPlugin: {e}")
			return False

	def _start_background_init(self, organizer: mobase.IOrganizer, mod_helper) -> None:
		def background() -> None:
			time.sleep(2)
			mod_helper.populate_installation_metadata(organizer)
			mod_helper.compute_conflict_summaries(organizer)
			self._start_servers()
		threading.Thread(target=background, daemon=True, name="WebAPI-Background-Init").start()

	def _register_invalidation_hooks(self, organizer: mobase.IOrganizer, mod_helper) -> None:
		from .organizer import db_helper
		mod_list = organizer.modList()
		mod_list.onModStateChanged(lambda _: mod_helper.invalidate_conflict_cache())
		mod_list.onModInstalled(lambda _: mod_helper.invalidate_conflict_cache())
		mod_list.onModRemoved(lambda _: mod_helper.invalidate_conflict_cache())
		mod_list.onModMoved(lambda *_: mod_helper.invalidate_conflict_cache())
		try:
			def on_renamed(old_name: str, new_name: str) -> None:
				db_helper.rename_mod_metadata(old_name, new_name)
				mod_helper.invalidate_conflict_cache()
				server_websocket.broadcast({
					"event": "mod_renamed",
					"oldName": old_name,
					"newName": new_name,
					"mod": mod_helper.get_mod_info(organizer, new_name),
				})
			mod_list.onModRenamed(on_renamed)
		except AttributeError:
			log.info("onModRenamed not available in this MO2 version")

	def _setup_task_executor(self, organizer: mobase.IOrganizer) -> None:
		self._task_executor = SignalTaskExecutor()
		self._task_executor.start(organizer)

	def _start_servers(self) -> None:
		self._server_thread = threading.Thread(
			target=server_http.run_server,
			kwargs={"port": self._http_port},
			daemon=True,
			name="WebAPI-HTTP-Server",
		)
		self._server_thread.start()
		log.info(f"HTTP server starting on port {self._http_port}")
		self._websocket_thread = threading.Thread(
			target=server_websocket.start_server,
			kwargs={"port": self._websocket_port},
			daemon=True,
			name="WebAPI-WebSocket-Server",
		)
		self._websocket_thread.start()
		log.info(f"WebSocket server starting on port {self._websocket_port}")

	def name(self) -> str:
		return "WebAPIPlugin"

	def localizedName(self) -> str:
		return "Web API Plugin"

	def author(self) -> str:
		return "johannes-z"

	def description(self) -> str:
		return (
			f"Provides HTTP (port {self._http_port}) and WebSocket (port {self._websocket_port}) "
			f"APIs for external applications to interact with Mod Organizer 2."
		)

	def version(self) -> mobase.VersionInfo:
		return mobase.VersionInfo(1, 1, 0, mobase.ReleaseType.BETA)

	def isActive(self) -> bool:
		if not self._organizer:
			return False
		return self._organizer.pluginSetting(self.name(), "enabled")

	def settings(self) -> list[mobase.PluginSetting]:
		return [
			mobase.PluginSetting("enabled", "Enable Web API Plugin", True),
			mobase.PluginSetting("http_port", "HTTP Server Port", self._http_port),
			mobase.PluginSetting("websocket_port", "WebSocket Server Port", self._websocket_port),
		]
