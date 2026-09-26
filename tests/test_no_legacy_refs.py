"""The tracked tree must not mention the previous project or how we got here."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
# Split so this file does not match itself.
BANNED = [
    "python-telegram-" + "bot-calendar",
    "art" + "em",
    "bakh" + "anov",
    "succ" + "essor",
    "fo" + "rk",
    "drop" + "-in",
    "migr" + "ation",
    "orig" + "inal",
]


def tracked_files() -> list[Path]:
    try:
        out = subprocess.run(
            ["git", "ls-files", "-co", "--exclude-standard"], cwd=ROOT, check=True, capture_output=True, text=True
        ).stdout
    except (OSError, subprocess.CalledProcessError):
        pytest.skip("git is not available")
    return [ROOT / name for name in out.splitlines() if (ROOT / name).is_file()]


def test_no_legacy_references() -> None:
    hits = []
    for path in tracked_files():
        text = path.read_bytes().decode("utf-8", errors="ignore").lower()
        hits += [f"{path.relative_to(ROOT)}: {word}" for word in BANNED if word in text]
    assert not hits, "\n".join(hits)


def test_license_has_no_copyright_line() -> None:
    lines = (ROOT / "LICENSE").read_text(encoding="utf-8").splitlines()
    assert not [line for line in lines if line.lstrip().startswith("Copyright")]
