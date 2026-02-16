"""
Internal version control for the script library.

Tracks changes, diffs, and allows rollback of individual scripts.
Storage: backend/scripts/versions/{script_id}/{version}.py + metadata.json
"""
from __future__ import annotations

import json
import os
import shutil
import time
from dataclasses import dataclass, asdict
from typing import Optional


VERSIONS_DIR = os.path.join(os.path.dirname(__file__), "versions")


@dataclass
class VersionEntry:
    version: int
    timestamp: float
    commit_message: str
    filename: str  # e.g. "1.py", "2.py"


@dataclass
class ScriptHistory:
    script_id: str
    script_name: str
    current_version: int
    entries: list[VersionEntry]


class ScriptVersionControl:
    """Git-like version control scoped to the scripts directory."""

    def __init__(self):
        os.makedirs(VERSIONS_DIR, exist_ok=True)

    def _script_dir(self, script_id: str) -> str:
        path = os.path.join(VERSIONS_DIR, script_id)
        os.makedirs(path, exist_ok=True)
        return path

    def _load_meta(self, script_id: str) -> dict:
        meta_path = os.path.join(self._script_dir(script_id), "metadata.json")
        if os.path.exists(meta_path):
            with open(meta_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {"script_id": script_id, "current_version": 0, "entries": []}

    def _save_meta(self, script_id: str, meta: dict):
        meta_path = os.path.join(self._script_dir(script_id), "metadata.json")
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2)

    def commit(self, script_id: str, script_name: str, code: str, message: str = "Auto-commit") -> int:
        """Save a new version of a script. Returns the new version number."""
        meta = self._load_meta(script_id)
        new_version = meta["current_version"] + 1

        # Write the versioned code file
        version_file = f"{new_version}.py"
        version_path = os.path.join(self._script_dir(script_id), version_file)
        with open(version_path, "w", encoding="utf-8") as f:
            f.write(code)

        # Update metadata
        entry = {
            "version": new_version,
            "timestamp": time.time(),
            "commit_message": message,
            "filename": version_file,
        }
        meta["current_version"] = new_version
        meta["script_name"] = script_name
        meta.setdefault("entries", []).append(entry)
        self._save_meta(script_id, meta)

        return new_version

    def get_history(self, script_id: str) -> ScriptHistory | None:
        """Get full version history for a script."""
        meta = self._load_meta(script_id)
        if not meta.get("entries"):
            return None
        entries = [
            VersionEntry(
                version=e["version"],
                timestamp=e["timestamp"],
                commit_message=e["commit_message"],
                filename=e["filename"],
            )
            for e in meta["entries"]
        ]
        return ScriptHistory(
            script_id=script_id,
            script_name=meta.get("script_name", script_id),
            current_version=meta["current_version"],
            entries=entries,
        )

    def get_version_code(self, script_id: str, version: int) -> str | None:
        """Read the code of a specific version."""
        version_path = os.path.join(self._script_dir(script_id), f"{version}.py")
        if os.path.exists(version_path):
            with open(version_path, "r", encoding="utf-8") as f:
                return f.read()
        return None

    def rollback(self, script_id: str, target_version: int, library_filepath: str) -> bool:
        """Rollback a script to a previous version. Overwrites the library file."""
        code = self.get_version_code(script_id, target_version)
        if code is None:
            return False

        # Overwrite the current library file
        with open(library_filepath, "w", encoding="utf-8") as f:
            f.write(code)

        # Record the rollback as a new version
        meta = self._load_meta(script_id)
        self.commit(
            script_id,
            meta.get("script_name", script_id),
            code,
            f"Rollback to version {target_version}",
        )
        return True

    def get_diff(self, script_id: str, v1: int, v2: int) -> dict:
        """Get a simple diff between two versions."""
        code1 = self.get_version_code(script_id, v1) or ""
        code2 = self.get_version_code(script_id, v2) or ""
        return {
            "script_id": script_id,
            "from_version": v1,
            "to_version": v2,
            "old_code": code1,
            "new_code": code2,
        }

    def list_tracked_scripts(self) -> list[dict]:
        """List all scripts that have version history."""
        result = []
        if not os.path.exists(VERSIONS_DIR):
            return result
        for script_id in os.listdir(VERSIONS_DIR):
            script_dir = os.path.join(VERSIONS_DIR, script_id)
            if os.path.isdir(script_dir):
                meta = self._load_meta(script_id)
                result.append({
                    "script_id": script_id,
                    "script_name": meta.get("script_name", script_id),
                    "current_version": meta.get("current_version", 0),
                    "total_versions": len(meta.get("entries", [])),
                })
        return result
