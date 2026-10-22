"""Guardrails for Chrome extension manifest permissions (issue #22)."""

import json
import re
from pathlib import Path

EXTENSION_DIR = Path(__file__).resolve().parents[2] / "yt-doubt-extension"
MANIFEST_PATH = EXTENSION_DIR / "manifest.json"
EXTENSION_JS = [EXTENSION_DIR / "background.js", EXTENSION_DIR / "content.js"]


def _load_manifest():
    with MANIFEST_PATH.open(encoding="utf-8") as f:
        return json.load(f)


def _extension_source():
    return "\n".join(path.read_text(encoding="utf-8") for path in EXTENSION_JS)


def test_manifest_has_no_unused_activeTab_or_scripting():
    """activeTab/scripting must not be declared unless chrome.tabs/scripting is used."""
    manifest = _load_manifest()
    permissions = set(manifest.get("permissions") or [])
    source = _extension_source()

    uses_scripting = bool(re.search(r"chrome\.scripting\b", source))
    uses_tabs = bool(re.search(r"chrome\.tabs\b", source))

    if "scripting" in permissions:
        assert uses_scripting, (
            "manifest declares 'scripting' but no chrome.scripting.* call exists; "
            "remove it (content_scripts inject without this permission)"
        )
    if "activeTab" in permissions:
        assert uses_tabs or uses_scripting, (
            "manifest declares 'activeTab' but no chrome.tabs/scripting usage exists; "
            "remove it"
        )


def test_content_scripts_cover_youtube_without_scripting_api():
    """Declarative content_scripts must inject the widget on YouTube watch pages."""
    manifest = _load_manifest()
    scripts = manifest.get("content_scripts") or []
    assert scripts, "content_scripts required so scripting permission is unnecessary"

    matches = []
    js_files = []
    for entry in scripts:
        matches.extend(entry.get("matches") or [])
        js_files.extend(entry.get("js") or [])

    assert any("youtube.com" in m for m in matches)
    assert "content.js" in js_files
    assert (EXTENSION_DIR / "content.js").is_file()
