"""Tests for user preference management."""
import pytest
from src.preferences import Preference, PreferenceStore, default_preferences


@pytest.fixture
def store():
    s = PreferenceStore()
    s.register("theme", "dark", "string", "UI theme")
    s.register("items_per_page", 25, "int", "Page size")
    s.register("auto_save", True, "bool", "Auto-save")
    return s


def test_register(store):
    assert store.has("theme")
    assert store.get("theme") == "dark"


def test_get_missing(store):
    assert store.get("nonexistent") is None


def test_set_valid(store):
    assert store.set("theme", "light") is True
    assert store.get("theme") == "light"


def test_set_type_mismatch(store):
    assert store.set("items_per_page", "twenty") is False
    assert store.get("items_per_page") == 25
    assert store.set("auto_save", "yes") is False
    assert store.get("auto_save") is True


def test_set_missing_key(store):
    assert store.set("nonexistent", "value") is False


def test_reset(store):
    store.set("theme", "light")
    assert store.reset("theme") is True
    assert store.get("theme") == "dark"
    assert store.reset("nonexistent") is False


def test_reset_all(store):
    store.set("theme", "light")
    store.set("items_per_page", 50)
    store.reset_all()
    assert store.get("theme") == "dark"
    assert store.get("items_per_page") == 25


def test_get_all(store):
    all_prefs = store.get_all()
    assert all_prefs["theme"] == "dark"
    assert all_prefs["items_per_page"] == 25


def test_list_preferences(store):
    prefs = store.list_preferences()
    assert len(prefs) == 3


def test_count(store):
    assert store.count() == 3


def test_changed_preferences(store):
    store.set("theme", "light")
    changed = store.changed_preferences()
    assert len(changed) == 1
    assert changed[0].key == "theme"


def test_no_changed(store):
    assert len(store.changed_preferences()) == 0


def test_to_dict(store):
    d = store.to_dict()
    assert "theme" in d
    assert d["theme"]["value"] == "dark"
    assert d["theme"]["type"] == "string"


def test_preference_is_default():
    p = Preference(key="x", value=5, type="int", default=5)
    assert p.is_default is True
    p.value = 10
    assert p.is_default is False


def test_preference_reset_to_default():
    p = Preference(key="x", value=10, type="int", default=5)
    p.reset_to_default()
    assert p.value == 5


def test_default_preferences():
    store = default_preferences()
    assert store.count() == 10
    assert store.get("theme") == "dark"
    assert store.get("auto_save") is True
    assert store.get("items_per_page") == 25


def test_type_validation_bool():
    store = PreferenceStore()
    store.register("flag", True, "bool")
    assert store.set("flag", False) is True
    assert store.set("flag", 1) is False


def test_type_validation_float():
    store = PreferenceStore()
    store.register("ratio", 0.5, "float")
    assert store.set("ratio", 0.75) is True
    assert store.set("ratio", 3) is True
