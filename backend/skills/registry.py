"""
Skill Registry: Discovers and manages available skills.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from .base import Skill
from .loader import load_skill_from_file


class SkillRegistry:
    """Central registry for discovering and retrieving skills."""
    
    def __init__(self, workspace_root: str):
        self.workspace_root = Path(workspace_root)
        self.skills: list[Skill] = []
        
    def load_all_skills(self) -> None:
        """Scan and load all available skills."""
        self.skills.clear()
        
        # 1. Built-in skills (bundled with backend)
        builtin_dir = Path(__file__).parent / "builtin"
        self._scan_directory(builtin_dir)
        
        # 2. Workspace skills (project-specific)
        workspace_skills = self.workspace_root / "skills"
        if workspace_skills.exists():
            self._scan_directory(workspace_skills)

    def _scan_directory(self, directory: Path) -> None:
        """Recursively find SKILL.md files."""
        if not directory.exists():
            return
            
        for root, _, files in os.walk(directory):
            if "SKILL.md" in files:
                skill_path = Path(root) / "SKILL.md"
                skill = load_skill_from_file(str(skill_path))
                if skill:
                    # Overwrite duplicates? Or keep all?
                    # For now simplicity: append all
                    self.skills.append(skill)
    
    def find_skill(self, problem_text: str) -> Optional[Skill]:
        """Find the best matching skill for a problem."""
        # Simple implementation: Return first matching
        # Future: Use scoring or LLM selection
        for skill in self.skills:
            if skill.matches(problem_text):
                return skill
        return None

    def get_skill_by_name(self, name: str) -> Optional[Skill]:
        """Retrieve a skill by exact name."""
        for skill in self.skills:
            if skill.name == name:
                return skill
        return None
