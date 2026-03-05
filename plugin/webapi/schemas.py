"""Pydantic models for request bodies and OpenAPI documentation."""

from pydantic import BaseModel, Field

# --- Error responses ---


class ErrorResponse(BaseModel):
	"""Error body for 400, 404, 409, 500."""

	error: str = Field(..., description="Error message.")


class ErrorHintResponse(BaseModel):
	"""Error body with hint (e.g. 501)."""

	error: str = Field(..., description="Error message.")
	hint: str = Field(..., description="Hint for the user.")


# --- Health ---


class HealthResponse(BaseModel):
	"""GET /health."""

	status: str = Field(..., description="Server status.")
	version: str = Field(..., description="API version.")


class ConfigResponse(BaseModel):
	"""GET /config."""

	httpPort: int = Field(..., description="HTTP server port.")
	websocketPort: int = Field(..., description="WebSocket server port.")


# --- Profile ---


class ProfileResponse(BaseModel):
	"""GET /profile."""

	name: str | None = Field(None, description="Current profile name.")


# --- Mods: list and query ---


class ModListItem(BaseModel):
	"""Lightweight mod entry (name, isEnabled, priority)."""

	name: str = Field(..., description="Mod name.")
	isEnabled: bool = Field(..., description="Whether the mod is enabled.")
	priority: int = Field(..., description="Load order priority.")


class ConflictSummary(BaseModel):
	"""Nested conflict counts in mod info."""

	overwriting: int = Field(..., description="Number of files this mod overwrites.")
	overridden: int = Field(..., description="Number of files overwritten by others.")


class ModInfo(BaseModel):
	"""Full mod info (GET /mods, GET /mods/:name)."""

	name: str = Field(..., description="Mod name.")
	isEnabled: bool = Field(..., description="Whether the mod is enabled.")
	version: str = Field(..., description="Version string.")
	priority: int = Field(..., description="Load order priority.")
	isSeparator: bool = Field(..., description="True if separator.")
	isForeign: bool = Field(..., description="True if foreign (e.g. game data).")
	isOverwrite: bool = Field(..., description="True if overwrite folder.")
	nexusId: int | None = Field(None, description="Nexus Mods ID.")
	categories: list[str] = Field(default_factory=list, description="Category names.")
	comments: str | None = Field(None, description="Mod comments.")
	hasLooseFiles: bool = Field(False, description="Has loose files.")
	isValid: bool = Field(False, description="Mod is valid.")
	isEmpty: bool = Field(False, description="Mod is empty.")
	fileCount: int = Field(0, description="File count.")
	conflicts: ConflictSummary = Field(..., description="Conflict summary.")
	meta: dict[str, str] = Field(default_factory=dict, description="Custom metadata.")


class ModPriorityItem(BaseModel):
	"""Name and priority (GET /mods/priority)."""

	name: str = Field(..., description="Mod name.")
	priority: int = Field(..., description="Load order priority.")


# --- Mods: conflicts ---


class ConflictSummaryFull(BaseModel):
	"""Full conflict summary per mod (GET /mods/conflicts)."""

	overwriting: int = Field(..., description="Number of files this mod overwrites.")
	overridden: int = Field(..., description="Number of files overwritten by others.")
	overwritingMods: list[str] = Field(default_factory=list, description="Mods overwritten by this one.")
	overriddenByMods: list[str] = Field(default_factory=list, description="Mods that overwrite this one.")


class ConflictWinItem(BaseModel):
	"""Winning file entry (mod conflicts detail)."""

	file: str = Field(..., description="File path.")
	overwriting: list[str] = Field(..., description="Mod names overwritten by this file.")


class ConflictLoseItem(BaseModel):
	"""Losing file entry (mod conflicts detail)."""

	file: str = Field(..., description="File path.")
	overwrittenBy: str = Field(..., description="Mod name that wins.")


class ModConflictsDetail(BaseModel):
	"""GET /mods/:name/conflicts."""

	winning: list[ConflictWinItem] = Field(default_factory=list, description="Files this mod wins.")
	losing: list[ConflictLoseItem] = Field(default_factory=list, description="Files this mod loses.")
	winningCount: int = Field(..., description="Count of winning files.")
	losingCount: int = Field(..., description="Count of losing files.")


# --- Mods: metadata ---


class ModMetaKeyResponse(BaseModel):
	"""GET /mods/:name/meta/:key."""

	mod: str = Field(..., description="Mod name.")
	key: str = Field(..., description="Metadata key.")
	value: str | int = Field(..., description="Metadata value.")


# --- Request bodies ---


class ModNameBody(BaseModel):
	"""Body for enable, disable, toggle, set-priority."""

	name: str = Field(..., description="Mod name (as shown in MO2).")

	model_config = {"json_schema_extra": {"example": {"name": "ModName"}}}


class ModRenameBody(BaseModel):
	"""Body for renaming a mod."""

	newName: str = Field(..., description="New display name for the mod.")

	model_config = {"json_schema_extra": {"example": {"newName": "NewModName"}}}


class ModNamesBody(BaseModel):
	"""Body for enable-batch and disable-batch."""

	names: list[str] = Field(..., description="List of mod names.")

	model_config = {"json_schema_extra": {"example": {"names": ["ModA", "ModB"]}}}


class ModStateItem(BaseModel):
	"""One entry in the bulk state update list."""

	name: str = Field(..., description="Mod name.")
	state: bool = Field(..., description="True to enable, False to disable.")

	model_config = {"json_schema_extra": {"example": {"name": "ModA", "state": True}}}


class ModStateBody(BaseModel):
	"""Body for PATCH /mods/state: list of name + state."""

	root: list[ModStateItem]

	model_config = {"json_schema_extra": {"example": [{"name": "ModA", "state": True}, {"name": "ModB", "state": False}]}}


class ModSetPriorityBody(BaseModel):
	"""Body for set-priority."""

	name: str = Field(..., description="Mod name.")
	priority: int = Field(..., description="New priority (integer, lower = higher in load order).")

	model_config = {"json_schema_extra": {"example": {"name": "ModName", "priority": 0}}}


class ModMetaDataBody(BaseModel):
	"""Body for PATCH /mods/{mod_name}/meta: key-value metadata."""

	data: dict[str, str | int] = Field(..., description="Key-value pairs to set for the mod.")

	model_config = {"json_schema_extra": {"example": {"data": {"key1": "value1", "key2": "value2"}}}}


class ModMetaValueBody(BaseModel):
	"""Body for PUT /mods/{mod_name}/meta/{key}: single value."""

	value: str | int = Field(..., description="Value to set (string or number).")

	model_config = {"json_schema_extra": {"example": {"value": "value1"}}}
