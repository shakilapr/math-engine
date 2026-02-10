"""
Script library manager — indexes and retrieves pre-built solver scripts.
"""
from __future__ import annotations

import json
import os
from typing import Optional

SCRIPTS_DIR = os.path.join(os.path.dirname(__file__), "library")
INDEX_PATH = os.path.join(os.path.dirname(__file__), "index.json")


class ScriptLibrary:
    """Manage a library of reusable solver scripts with an index."""

    def __init__(self):
        os.makedirs(SCRIPTS_DIR, exist_ok=True)
        self.index = self._load_index()

    def _load_index(self) -> dict:
        """Load the script index."""
        if os.path.exists(INDEX_PATH):
            with open(INDEX_PATH, "r") as f:
                return json.load(f)
        return {"scripts": []}

    def _save_index(self):
        """Persist the index to disk."""
        with open(INDEX_PATH, "w") as f:
            json.dump(self.index, f, indent=2)

    def search(self, query: str, category: str = "") -> list[dict]:
        """Search the library for matching scripts."""
        results = []
        query_lower = query.lower()
        for script in self.index.get("scripts", []):
            score = 0
            if query_lower in script.get("name", "").lower():
                score += 3
            if query_lower in script.get("description", "").lower():
                score += 2
            for tag in script.get("tags", []):
                if query_lower in tag.lower():
                    score += 1
            if category and script.get("category", "") == category:
                score += 2
            if score > 0:
                results.append({**script, "_score": score})

        results.sort(key=lambda x: x["_score"], reverse=True)
        return results

    def get_script(self, script_id: str) -> Optional[str]:
        """Load a script by its ID."""
        for script in self.index.get("scripts", []):
            if script.get("id") == script_id:
                path = os.path.join(SCRIPTS_DIR, script["filename"])
                if os.path.exists(path):
                    try:
                        with open(path, "r", encoding="utf-8") as f:
                            return f.read()
                    except UnicodeDecodeError:
                        # Fallback to latin‑1 or ignore errors
                        with open(path, "r", encoding="utf-8", errors="replace") as f:
                            return f.read()
        return None

    def add_script(
        self,
        name: str,
        description: str,
        code: str,
        category: str,
        tags: list[str],
    ) -> str:
        """Add a new script to the library."""
        import uuid
        import re

        script_id = uuid.uuid4().hex[:8]
        # Sanitize name for filename: alphanumeric, underscore, dash only
        safe_name = re.sub(r'[^\w\-]', '_', name.lower().replace(' ', '_'))
        filename = f"{script_id}_{safe_name}.py"
        filepath = os.path.join(SCRIPTS_DIR, filename)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(code)

        entry = {
            "id": script_id,
            "name": name,
            "description": description,
            "category": category,
            "tags": tags,
            "filename": filename,
        }
        self.index.setdefault("scripts", []).append(entry)
        self._save_index()

        return script_id

    def list_all(self) -> list[dict]:
        """List all scripts in the library."""
        return self.index.get("scripts", [])
