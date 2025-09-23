import json
import os
from typing import Any, Dict

SAVE_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "save.json")


def _read_json() -> Dict[str, Any]:
	if not os.path.exists(SAVE_PATH):
		return {}
	try:
		with open(SAVE_PATH, "r", encoding="utf-8") as f:
			data = json.load(f)
			return data if isinstance(data, dict) else {}
	except Exception:
		return {}


def _write_json(data: Dict[str, Any]) -> None:
	with open(SAVE_PATH, "w", encoding="utf-8") as f:
		json.dump(data, f, ensure_ascii=False, indent=2)


def load_progress() -> Dict[str, Any]:
	data = _read_json()
	best = int(data.get("best_score", 0))
	return {"best_score": best}


def save_progress(data_in: Dict[str, Any]) -> None:
	data = _read_json()
	data["best_score"] = int(data_in.get("best_score", data.get("best_score", 0)))
	_write_json(data)


def load_settings() -> Dict[str, Any]:
	data = _read_json()
	settings = data.get("settings", {}) if isinstance(data.get("settings", {}), dict) else {}
	muted = bool(settings.get("muted", False))
	volume = float(settings.get("volume", 0.6))
	volume = 0.0 if volume < 0.0 else (1.0 if volume > 1.0 else volume)
	return {"muted": muted, "volume": volume}


def save_settings(muted: bool, volume: float) -> None:
	data = _read_json()
	data.setdefault("settings", {})
	data["settings"]["muted"] = bool(muted)
	v = float(volume)
	if v < 0.0:
		v = 0.0
	elif v > 1.0:
		v = 1.0
	data["settings"]["volume"] = v
	_write_json(data)


def load_controls() -> Dict[str, int]:
	# Defaults
	try:
		import pygame
		defaults = {
			"left": pygame.K_a,
			"right": pygame.K_d,
			"jump": pygame.K_SPACE,
			"pause": pygame.K_ESCAPE,
		}
	except Exception:
		defaults = {"left": 97, "right": 100, "jump": 32, "pause": 27}
	data = _read_json()
	ctrl = data.get("controls", {})
	if not isinstance(ctrl, dict):
		return defaults
	result = {}
	for k in ("left", "right", "jump", "pause"):
		v = ctrl.get(k, defaults[k])
		try:
			result[k] = int(v)
		except Exception:
			result[k] = defaults[k]
	return result


def save_controls(controls: Dict[str, int]) -> None:
	data = _read_json()
	data.setdefault("controls", {})
	for k in ("left", "right", "jump", "pause"):
		if k in controls:
			try:
				data["controls"][k] = int(controls[k])
			except Exception:
				pass
	_write_json(data)
