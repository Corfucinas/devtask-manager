"""Tests for label hierarchy."""
import pytest
from src.label_hierarchy import LabelNode, LabelHierarchy, default_hierarchy


@pytest.fixture
def hierarchy():
    h = LabelHierarchy()
    h.add("type")
    h.add("bug", parent="type")
    h.add("feature", parent="type")
    h.add("critical", parent="bug")
    h.add("minor", parent="bug")
    return h


def test_add():
    h = LabelHierarchy()
    node = h.add("root")
    assert node.name == "root"
    assert node.is_root is True


def test_add_with_parent(hierarchy):
    bug = hierarchy.get("bug")
    assert bug.parent == "type"
    assert "bug" in hierarchy.get("type").children


def test_add_duplicate():
    h = LabelHierarchy()
    h.add("test")
    h.add("test")
    assert h.count() == 1


def test_remove(hierarchy):
    assert hierarchy.remove("critical") is True
    assert hierarchy.get("critical") is None
    assert "critical" not in hierarchy.get("bug").children
    assert hierarchy.remove("nonexistent") is False


def test_remove_cascading(hierarchy):
    hierarchy.remove("bug")
    assert hierarchy.get("bug") is None
    assert hierarchy.get("critical") is None
    assert hierarchy.get("minor") is None


def test_get(hierarchy):
    assert hierarchy.get("type") is not None
    assert hierarchy.get("nonexistent") is None


def test_all_labels(hierarchy):
    labels = hierarchy.all_labels()
    assert "type" in labels
    assert "bug" in labels
    assert "critical" in labels


def test_count(hierarchy):
    assert hierarchy.count() == 5


def test_roots(hierarchy):
    roots = hierarchy.roots()
    assert len(roots) == 1
    assert roots[0].name == "type"


def test_leaves(hierarchy):
    leaves = hierarchy.leaves()
    assert len(leaves) == 3
    leaf_names = {l.name for l in leaves}
    assert "feature" in leaf_names
    assert "critical" in leaf_names


def test_children_of(hierarchy):
    children = hierarchy.children_of("bug")
    assert "critical" in children
    assert "minor" in children


def test_descendants_of(hierarchy):
    descendants = hierarchy.descendants_of("type")
    assert "bug" in descendants
    assert "critical" in descendants
    assert "minor" in descendants
    assert "feature" in descendants


def test_get_path(hierarchy):
    path = hierarchy.get_path("critical")
    assert path == ["type", "bug", "critical"]


def test_depth_of(hierarchy):
    assert hierarchy.depth_of("type") == 0
    assert hierarchy.depth_of("bug") == 1
    assert hierarchy.depth_of("critical") == 2


def test_subtree(hierarchy):
    tree = hierarchy.subtree("type")
    assert tree["name"] == "type"
    assert len(tree["children"]) == 2


def test_flatten(hierarchy):
    flat = hierarchy.flatten()
    assert len(flat) == 5
    crit = next(f for f in flat if f["name"] == "critical")
    assert crit["depth"] == 2
    assert "type/bug/critical" in crit["path"]


def test_default_hierarchy():
    h = default_hierarchy()
    assert h.count() >= 7
    assert h.get("bug") is not None
    assert h.get("urgent") is not None
