import asyncio
import json

import websockets

from . import context
from .log import log
from .organizer import mod_helper

_server_stop_event: asyncio.Event | None = None
_server_loop: asyncio.AbstractEventLoop | None = None
_connected_clients: set = set()
_handlers_registered = False


def shutdown_server() -> None:
	global _server_stop_event, _server_loop
	if not (_server_stop_event and _server_loop):
		return
	log.info("Shutting down WebSocket server")
	try:
		_server_loop.call_soon_threadsafe(_server_stop_event.set)
	except Exception as e:
		log.error(f"Error shutting down WebSocket server: {e}")
	_server_stop_event = None
	_server_loop = None


def broadcast(data: dict) -> None:
	if not _connected_clients or not _server_loop:
		return
	message = json.dumps(data)
	for client in _connected_clients.copy():
		asyncio.run_coroutine_threadsafe(
			_safe_send(client, message), _server_loop
		)


async def _safe_send(client, message: str) -> None:
	try:
		await client.send(message)
	except websockets.exceptions.ConnectionClosed:
		_connected_clients.discard(client)
	except Exception as e:
		log.error(f"Error sending to WebSocket client: {e}")
		_connected_clients.discard(client)


def _register_event_handlers() -> None:
	global _handlers_registered
	if _handlers_registered:
		return
	_handlers_registered = True
	organizer = context.get_organizer()
	if not organizer:
		return
	mod_list = organizer.modList()

	def on_mod_state_changed(mod_info_dict) -> None:
		try:
			mods = [
				info for name in mod_info_dict
				if (info := mod_helper.get_mod_info(organizer, name))
			]
			if mods:
				broadcast({"event": "mod_updated", "mods": mods})
		except Exception as e:
			log.error(f"Error in on_mod_state_changed: {e}")

	def on_mod_installed(mod) -> None:
		try:
			info = mod_helper.get_mod_info(organizer, mod.name())
			if info:
				broadcast({"event": "mod_installed", "mods": [info]})
		except Exception as e:
			log.error(f"Error in on_mod_installed: {e}")

	def on_mod_moved(mod_name: str, old_priority: int, new_priority: int) -> None:
		try:
			info = mod_helper.get_mod_info(organizer, mod_name)
			if info:
				broadcast({
					"event": "mod_moved",
					"mods": [info],
					"oldPriority": old_priority,
					"newPriority": new_priority,
				})
		except Exception as e:
			log.error(f"Error in on_mod_moved: {e}")

	def on_mod_removed(mod_name: str) -> None:
		try:
			broadcast({"event": "mod_removed", "mod": mod_name})
		except Exception as e:
			log.error(f"Error in on_mod_removed: {e}")

	mod_list.onModStateChanged(on_mod_state_changed)
	mod_list.onModInstalled(on_mod_installed)
	mod_list.onModMoved(on_mod_moved)
	mod_list.onModRemoved(on_mod_removed)
	log.info("WebSocket event handlers registered")


async def _handle_client(websocket) -> None:
	_connected_clients.add(websocket)
	log.info(f"WebSocket client connected from {websocket.remote_address}")
	try:
		await websocket.wait_closed()
	except websockets.exceptions.ConnectionClosed:
		pass
	finally:
		_connected_clients.discard(websocket)
		log.info("WebSocket client disconnected")


def start_server(port: int) -> None:
	global _server_stop_event, _server_loop
	_register_event_handlers()

	async def main() -> None:
		global _server_stop_event, _server_loop
		_server_loop = asyncio.get_event_loop()
		_server_stop_event = asyncio.Event()
		try:
			async with websockets.serve(_handle_client, "localhost", port):
				log.info(f"WebSocket server running on port {port}")
				await _server_stop_event.wait()
				log.info("WebSocket server shutting down")
		except Exception as e:
			log.error(f"Failed to start WebSocket server on port {port}: {e}")
		finally:
			_server_stop_event = None

	try:
		asyncio.run(main())
	except Exception as e:
		log.error(f"WebSocket server crashed: {e}")
