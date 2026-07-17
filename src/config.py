"""Configuration management for DevTask Manager."""
import os, json

DEFAULT_CONFIG = {"storage_path": None, "color_output": True, "default_priority": "medium", "date_format": "%Y-%m-%d", "sort_order": "priority", "show_tags": True}

def get_config_path():
    return os.path.join(os.path.expanduser("~"), ".devtask", "config.json")

def load_config():
    config = DEFAULT_CONFIG.copy()
    path = get_config_path()
    if os.path.exists(path):
        with open(path, "r") as f:
            config.update(json.load(f))
    return config

def save_config(config):
    path = get_config_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(config, f, indent=2)

def get_storage_path():
    config = load_config()
    return config.get("storage_path") or os.path.join(os.path.expanduser("~"), ".devtask", "tasks.json")
