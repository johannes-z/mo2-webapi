from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from .. import context

router = APIRouter(tags=["Profile"])


def _parse_modlist(profile_dir: Path) -> list[dict] | None:
	# modlist.txt: + enabled, - disabled, * unmanaged
	modlist_path = profile_dir / "modlist.txt"
	if not modlist_path.exists():
		return None

	mods = []
	with open(modlist_path, "r", encoding="utf-8") as f:
		for priority, line in enumerate(f):
			line = line.strip()
			if not line or line.startswith("#"):
				continue
			prefix = line[0]
			if prefix not in ("+", "-", "*"):
				continue
			name = line[1:]
			mods.append({
				"name": name,
				"isEnabled": prefix == "+",
				"priority": priority,
			})
	return mods


@router.get("/profile")
def get_profile():
	organizer = context.get_organizer()
	if not organizer:
		return JSONResponse(content={"error": "Organizer not initialized"}, status_code=500)
	profile = organizer.profile()
	return {"name": profile.name() if profile else None}


@router.get("/profiles")
def list_profiles():
	organizer = context.get_organizer()
	if not organizer:
		return JSONResponse(content={"error": "Organizer not initialized"}, status_code=500)
	profiles_dir = Path(organizer.profilePath()).parent
	if not profiles_dir.exists():
		return []
	current = organizer.profileName()
	profiles = sorted([
		d.name for d in profiles_dir.iterdir()
		if d.is_dir() and (d / "modlist.txt").exists()
	])
	return profiles


@router.post("/profiles/{profile_name:path}/activate")
def activate_profile(profile_name: str):
	return JSONResponse(
		content={
			"error": "Profile switching is not supported by the mobase Python plugin API",
			"hint": "Profile changes must be made through the MO2 UI",
		},
		status_code=501,
	)
