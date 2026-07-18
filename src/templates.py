"""Task templates for quick creation."""

TEMPLATES = {
    "bug": {"title": "Fix: ", "description": "Steps to reproduce:\n1. \n2. \n\nExpected: \nActual: ", "priority": "high", "tags": ["bug"]},
    "feature": {"title": "Add: ", "description": "User story:\nAs a user, I want to...\nSo that...", "priority": "medium", "tags": ["feature"]},
    "refactor": {"title": "Refactor: ", "description": "Current: \nProblem: \nProposed: ", "priority": "low", "tags": ["refactor", "tech-debt"]},
    "docs": {"title": "Docs: ", "description": "Section: \nType: (new/update/fix)", "priority": "low", "tags": ["documentation"]},
    "test": {"title": "Test: ", "description": "Coverage target: \nTest type: (unit/integration/e2e)", "priority": "medium", "tags": ["testing"]},
    "release": {"title": "Release: v", "description": "Version: \nChanges:\n- ", "priority": "critical", "tags": ["release"]},
}

def get_template(name):
    if name not in TEMPLATES:
        raise ValueError(f"Unknown template: {name}")
    return TEMPLATES[name].copy()

def list_templates():
    return {name: t["title"].strip(": ") for name, t in TEMPLATES.items()}

def apply_template(store, template_name, title_suffix=""):
    template = get_template(template_name)
    title = template["title"] + title_suffix
    return store.create(title=title, description=template["description"], priority=template["priority"], tags=template["tags"])
