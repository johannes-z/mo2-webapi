from pathlib import Path

from flask import Blueprint, jsonify

from .. import context

bp = Blueprint("profile", __name__)


def _parse_modlist(profile_dir: Path) -> list[dict] | None:
	# modlist.txt: + enabled, - disabled, * unmanaged
	modlist_path = profile_dir / "modlist.txt"
	if not modlist_path.exists():
		return None

	mods = []
	with open(modlist_path, 'r', encoding='utf-8') as f:
		for priority, line in enumerate(f):
			line = line.strip()
			if not line or line.startswith('#'):
				continue

			prefix = line[0]
			if prefix not in ('+', '-', '*'):
				continue

			name = line[1:]
			mods.append({
				"name": name,
				"isEnabled": prefix == '+',
				"priority": priority,
			})

	return mods


@bp.route("/profile", methods=["GET"])
def get_profile():
	organizer = context.get_organizer()
	if not organizer:
		return jsonify({"error": "Organizer not initialized"}), 500
	profile = organizer.profile()
	return jsonify({"name": profile.name() if profile else None})


@bp.route("/profiles", methods=["GET"])
def list_profiles():
	organizer = context.get_organizer()
	if not organizer:
		return jsonify({"error": "Organizer not initialized"}), 500
	profiles_dir = Path(organizer.profilePath()).parent
	if not profiles_dir.exists():
		return jsonify({"current": None, "profiles": []})
	current = organizer.profileName()
	profiles = sorted([
		d.name for d in profiles_dir.iterdir()
		if d.is_dir() and (d / "modlist.txt").exists()
	])

	return jsonify(profiles)


@bp.route("/profiles/<path:profile_name>/activate", methods=["POST"])
def activate_profile(profile_name: str):
	return jsonify({
		"error": "Profile switching is not supported by the mobase Python plugin API",
		"hint": "Profile changes must be made through the MO2 UI",
	}), 501
