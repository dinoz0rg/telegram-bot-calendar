"""Release metadata: README images, project URLs, version, changelog."""

from __future__ import annotations

import re
import sys
from pathlib import Path

if sys.version_info >= (3, 11):
    import tomllib
else:  # pragma: no cover
    import tomli as tomllib

ROOT = Path(__file__).resolve().parent.parent
REPO = "https://github.com/dinoz0rg/telegram-bot-calendar"
IMG = "https://raw.githubusercontent.com/dinoz0rg/telegram-bot-calendar/main/docs/img/"


def test_readme_images_are_absolute() -> None:
    text = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "](docs/" not in text
    images = re.findall(r"!\[[^\]]*\]\(([^)]+)\)", text)
    assert images
    assert all(re.fullmatch(re.escape(IMG) + r"[a-z0-9-]+\.png", url) for url in images)


def test_pyproject_metadata() -> None:
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]
    assert project["version"] == "2.3.0"
    assert project["urls"] == {
        "Homepage": REPO,
        "Source": REPO,
        "Issues": f"{REPO}/issues",
        "Changelog": f"{REPO}/blob/main/CHANGELOG.md",
    }
    for minor in range(9, 14):
        assert f"Programming Language :: Python :: 3.{minor}" in project["classifiers"]
    assert "authors" not in project


def test_changelog_has_release() -> None:
    assert "## 2.3.0 — 2026-09-27" in (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")


def test_package_version_matches() -> None:
    from telegram_bot_calendar import __version__

    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]
    assert __version__ == project["version"]
