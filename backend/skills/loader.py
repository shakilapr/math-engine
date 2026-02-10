"""
Loads skills from directories by parsing SKILL.md files.
"""
from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Optional, Any
from .base import Skill

# Pattern to extract YAML frontmatter
FRONTMATTER_PATTERN = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)


def load_skill_from_file(path: str) -> Optional[Skill]:
    """Load a skill from a markdown file with YAML frontmatter."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        
        match = FRONTMATTER_PATTERN.match(content)
        if not match:
            # Maybe entire file is instructions if no frontmatter?
            # For now, require frontmatter for metadata
            return None
            
        fm_text = match.group(1)
        body = content[match.end():].strip()
        
        metadata = _parse_yaml_simple(fm_text)
        
        # Ensure patterns is a list
        patterns = metadata.get("patterns", [])
        if isinstance(patterns, str):
            patterns = [patterns]
            
        return Skill(
            name=metadata.get("name", Path(path).parent.name),
            description=metadata.get("description", ""),
            patterns=patterns,
            template=body,
            version=metadata.get("version", "1.0.0"),
            author=metadata.get("author", "System"),
            path=path
        )
    except Exception as e:
        print(f"Error loading skill {path}: {e}")
        return None


def _parse_yaml_simple(text: str) -> dict[str, Any]:
    """
    Very basic YAML parser to avoid dependencies.
    Supports:
    key: value
    list:
      - item1
      - item2
    """
    data = {}
    lines = text.splitlines()
    current_key = None
    
    for line in lines:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
            
        # Handle list items
        if line.startswith("- "):
            val = line[2:].strip().strip('"').strip("'")
            if current_key:
                if current_key not in data:
                    data[current_key] = []
                if not isinstance(data[current_key], list):
                    # Convert previous single value to list if mixed (shouldn't happen in valid YAML)
                    data[current_key] = [data[current_key]]
                data[current_key].append(val)
            continue
            
        # Handle key: value
        if ":" in line:
            key, val = line.split(":", 1)
            key = key.strip()
            val = val.strip().strip('"').strip("'")
            
            if not val:
                # Key with empty value -> likely start of list
                current_key = key
                data[key] = [] 
            else:
                current_key = key
                # Boolean handling
                if val.lower() == "true":
                    data[key] = True
                elif val.lower() == "false":
                    data[key] = False
                else:
                    data[key] = val
                    
    return data
