"""Tests for task preset templates."""
import pytest
from src.presets import Preset, PresetLibrary, default_presets


@pytest.fixture
def library():
    lib = PresetLibrary()
    lib.add("Bug", "Fix: {title}", "Bug: {description}", "high", ["bug"])
    lib.add("Feature", "Feature: {title}", "Feature: {description}", "medium", ["feature"])
    return lib


def test_preset_render_title():
    p = Preset(id=1, name="Bug", title_template="Fix: {title}")
    assert p.render_title(title="login error") == "Fix: login error"


def test_preset_render_title_no_template():
    p = Preset(id=1, name="Custom")
    assert p.render_title(title="My task") == "My task"


def test_preset_render_description_missing_key():
    p = Preset(id=1, name="Bug", description_template="Desc: {description}")
    result = p.render_description()
    assert result == "Desc: {description}"


def test_preset_to_task_attrs():
    p = Preset(id=1, name="Bug", title_template="Fix: {title}",
               description_template="Bug: {description}", priority="high", tags=["bug"])
    attrs = p.to_task_attrs(title="login", description="crash on login")
    assert attrs["title"] == "Fix: login"
    assert attrs["description"] == "Bug: crash on login"
    assert attrs["priority"] == "high"
    assert attrs["tags"] == ["bug"]


def test_library_add(library):
    assert library.count() == 2
    preset = library.add("Docs", "Docs: {title}", "", "low", ["docs"])
    assert preset.id == 3


def test_library_get(library):
    preset = library.get(1)
    assert preset is not None
    assert preset.name == "Bug"
    assert library.get(999) is None


def test_library_find_by_name(library):
    preset = library.find_by_name("Feature")
    assert preset is not None
    assert preset.priority == "medium"


def test_library_find_by_name_case_insensitive(library):
    preset = library.find_by_name("BUG")
    assert preset is not None
    assert preset.name == "Bug"


def test_library_find_by_name_missing(library):
    assert library.find_by_name("nonexistent") is None


def test_library_remove(library):
    assert library.remove(1) is True
    assert library.get(1) is None
    assert library.count() == 1
    assert library.remove(999) is False


def test_library_all_presets(library):
    presets = library.all_presets()
    assert len(presets) == 2


def test_library_apply(library):
    attrs = library.apply(1, title="login bug", description="crash")
    assert attrs is not None
    assert attrs["title"] == "Fix: login bug"
    assert attrs["priority"] == "high"


def test_library_apply_missing(library):
    assert library.apply(999) is None


def test_library_apply_by_name(library):
    attrs = library.apply_by_name("Feature", title="dark mode", description="add dark theme")
    assert attrs is not None
    assert attrs["title"] == "Feature: dark mode"
    assert "feature" in attrs["tags"]


def test_library_apply_by_name_missing(library):
    assert library.apply_by_name("nonexistent") is None


def test_default_presets():
    lib = default_presets()
    assert lib.count() == 6
    bug = lib.find_by_name("Bug")
    assert bug is not None
    assert bug.priority == "high"
    hotfix = lib.find_by_name("Hotfix")
    assert hotfix.priority == "critical"
