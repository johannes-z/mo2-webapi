"""Submit tasks from any thread; run in Qt main thread via QueuedConnection."""
from queue import Queue
from typing import Callable, Protocol

import mobase
from PyQt6.QtCore import QObject, QMetaObject, Qt, pyqtSlot

from .log import log


class TaskExecutor(Protocol):
	def submit(self, task: Callable[[mobase.IOrganizer], None]) -> None: ...
	def start(self, organizer: mobase.IOrganizer) -> None: ...
	def stop(self) -> None: ...


class SignalTaskExecutor(QObject):
	def __init__(self) -> None:
		super().__init__()
		self._organizer: mobase.IOrganizer | None = None
		self._task_queue: Queue = Queue()

	def submit(self, task: Callable[[mobase.IOrganizer], None]) -> None:
		self._task_queue.put(task)
		QMetaObject.invokeMethod(
			self, "_process_tasks", Qt.ConnectionType.QueuedConnection
		)

	def start(self, organizer: mobase.IOrganizer) -> None:
		self._organizer = organizer

	def stop(self) -> None:
		pass

	@pyqtSlot()
	def _process_tasks(self) -> None:
		while not self._task_queue.empty():
			try:
				task = self._task_queue.get_nowait()
				task(self._organizer)
			except Exception as e:
				log.warning(f"Task execution failed: {e}")
			finally:
				self._task_queue.task_done()
