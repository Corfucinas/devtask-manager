"""Layered configuration with defaults and overrides."""
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class LayeredConfig:
    """Configuration with layered defaults and overrides."""
    def __init__(self, defaults: Dict = None):
        self._layers: List[Dict] = [dict(defaults or {})]

    def add_layer(self, overrides: Dict, name: str = ""):
        """Push an override layer on top."""
        self._layers.append(dict(overrides or {}))

    def pop_layer(self) -> Optional[Dict]:
        """Remove the topmost override layer (never removes base)."""
        if len(self._layers) > 1:
            return self._layers.pop()
        return None

    def layer_count(self) -> int:
        return len(self._layers)

    def _merged(self) -> Dict:
        merged: Dict = {}
        for layer in self._layers:
            merged.update(layer)
        return merged

    def get(self, path: str, default=None) -> Any:
        """Get value by dot-path, e.g. 'notifications.email.enabled'."""
        current: Any = self._merged()
        for part in path.split("."):
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return default
        return current

    def set(self, path: str, value: Any):
        """Set value by dot-path on the topmost layer."""
        parts = path.split(".")
        layer = self._layers[-1]
        for part in parts[:-1]:
            if part not in layer or not isinstance(layer[part], dict):
                layer[part] = {}
            layer = layer[part]
        layer[parts[-1]] = value

    def has(self, path: str) -> bool:
        sentinel = object()
        return self.get(path, sentinel) is not sentinel

    def to_dict(self) -> Dict:
        return self._merged()

    def flat_keys(self, prefix: str = "") -> List[str]:
        """Return all dot-paths present in the merged config."""
        return sorted(self._flatten(self._merged(), prefix))

    def _flatten(self, d: Dict, prefix: str) -> List[str]:
        keys = []
        for k, v in d.items():
            path = f"{prefix}.{k}" if prefix else k
            keys.append(path)
            if isinstance(v, dict):
                keys.extend(self._flatten(v, path))
        return keys

    def clear_overrides(self):
        """Remove all layers except the base defaults."""
        self._layers = [self._layers[0]]


def config_diff(a: LayeredConfig, b: LayeredConfig) -> Dict[str, Any]:
    """Compare two configs; returns {path: {a, b}} for differences."""
    keys = set(a.flat_keys()) | set(b.flat_keys())
    diff = {}
    for key in sorted(keys):
        va, vb = a.get(key), b.get(key)
        if va != vb:
            diff[key] = {"a": va, "b": vb}
    return diff


def default_config() -> LayeredConfig:
    """Sensible default task manager configuration."""
    return LayeredConfig({
        "display": {"theme": "dark", "page_size": 25},
        "notifications": {"email": {"enabled": True}, "desktop": {"enabled": True}},
        "sync": {"interval_seconds": 30, "retries": 3},
        "limits": {"max_open_tasks": 100, "max_batch_size": 10},
    })
