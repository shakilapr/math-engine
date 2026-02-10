"""
Base classes for the Skills system.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Skill:
    """Represents a modular problem-solving capability."""
    name: str
    description: str
    patterns: list[str] = field(default_factory=list)  # Regex patterns or keywords
    template: str = ""  # Code template for the solver
    examples: list[dict] = field(default_factory=list)  # Example inputs/outputs
    verification_logic: str = ""  # Optional custom verification
    version: str = "1.0.0"
    author: str = "System"
    path: Optional[str] = None  # File path where skill was loaded from

    def matches(self, problem_text: str) -> bool:
        """Check if this skill applies to the problem text."""
        import re
        for pattern in self.patterns:
            if re.search(pattern, problem_text, re.IGNORECASE):
                return True
        return False
