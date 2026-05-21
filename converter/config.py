import json
import os
from pathlib import Path

DEFAULT_SETTINGS = {
    "last_format": "PNG",
    "last_quality": 95,
    "last_width": "",
    "last_height": "",
    "keep_proportions": True,
    "interpolation": "LANCZOS"
}

CONFIG_FILE = Path.home() / ".image_converter_settings.json"


def load_config() -> dict:
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
                merged = DEFAULT_SETTINGS.copy()
                merged.update(config)
                return merged
        except (json.JSONDecodeError, IOError):
            return DEFAULT_SETTINGS.copy()
    return DEFAULT_SETTINGS.copy()


def save_config(config: dict) -> bool:
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
        return True
    except IOError:
        return False


def update_setting(key: str, value) -> bool:
    config = load_config()
    config[key] = value
    return save_config(config)