import re
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))


def _read_project_version() -> str:
    pyproject_path = ROOT_DIR / "pyproject.toml"
    pyproject_content = pyproject_path.read_text(encoding="utf-8")
    match = re.search(
        r"\[tool\.poetry\][\s\S]*?^version\s*=\s*\"([^\"]+)\"",
        pyproject_content,
        re.MULTILINE,
    )
    if match is None:
        return "unknown"
    return match.group(1)


project = "openapi-schema-validator"
copyright = "2023, Artur Maciag"
author = "Artur Maciag"

release = _read_project_version()

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.doctest",
    "sphinx.ext.intersphinx",
    "sphinx.ext.coverage",
    "sphinx.ext.viewcode",
    "sphinx_immaterial",
]

templates_path = ["_templates"]

exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

html_theme = "sphinx_immaterial"

html_static_path = []

html_title = "openapi-schema-validator"

html_theme_options = {
    "analytics": {
        "provider": "google",
        "property": "G-11RDPBZ7EJ",
    },
    "repo_url": "https://github.com/python-openapi/openapi-schema-validator/",
    "repo_name": "openapi-schema-validator",
    "icon": {
        "repo": "fontawesome/brands/github-alt",
        "edit": "material/file-edit-outline",
    },
    "palette": [
        {
            "media": "(prefers-color-scheme: dark)",
            "scheme": "slate",
            "primary": "lime",
            "accent": "amber",
            "scheme": "slate",
            "toggle": {
                "icon": "material/toggle-switch",
                "name": "Switch to light mode",
            },
        },
        {
            "media": "(prefers-color-scheme: light)",
            "scheme": "default",
            "primary": "lime",
            "accent": "amber",
            "toggle": {
                "icon": "material/toggle-switch-off-outline",
                "name": "Switch to dark mode",
            },
        },
    ],
    "globaltoc_collapse": False,
}
