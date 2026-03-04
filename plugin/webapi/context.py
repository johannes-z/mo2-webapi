from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
	import mobase
	from .task_executor import TaskExecutor

_organizer: "mobase.IOrganizer | None" = None
_task_executor: "TaskExecutor | None" = None
_static_dir: Path | None = None


def set_context(
	organizer: "mobase.IOrganizer",
	task_executor: "TaskExecutor",
	static_dir: Path | None = None,
) -> None:
	global _organizer, _task_executor, _static_dir
	_organizer = organizer
	_task_executor = task_executor
	_static_dir = static_dir


def get_organizer() -> "mobase.IOrganizer | None":
	return _organizer


def get_task_executor() -> "TaskExecutor | None":
	return _task_executor


def get_static_dir() -> Path | None:
	return _static_dir
