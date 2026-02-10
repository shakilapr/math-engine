import os
import sys
import pytest
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock, patch

# Add backend to path
sys.path.append(str(Path(__file__).parent.parent / "backend"))

# Mock heavy libraries
sys.modules["numpy"] = MagicMock()
sys.modules["scipy"] = MagicMock()
sys.modules["pandas"] = MagicMock()
sys.modules["matplotlib"] = MagicMock()
sys.modules["matplotlib.pyplot"] = MagicMock()
sys.modules["mpmath"] = MagicMock()
sys.modules["mpmath.libmp"] = MagicMock()
sys.modules["sympy"] = MagicMock()
sys.modules["PIL"] = MagicMock()

from skills.loader import load_skill_from_file
from skills.registry import SkillRegistry
from core.engine import MathEngine
from api.models import SolveRequest, LLMProvider

# ── Fixtures ───────────────────────────────────────────────────────────

@pytest.fixture
def sample_skill_file(tmp_path):
    d = tmp_path / "skills" / "test_skill"
    d.mkdir(parents=True)
    f = d / "SKILL.md"
    content = """---
name: test_skill
description: A test skill
patterns:
  - "test pattern"
  - "another pattern"
version: 0.1.0
---
def solve():
    pass
"""
    f.write_text(content, encoding="utf-8")
    return str(f)

# ── Loader Tests ───────────────────────────────────────────────────────

def test_load_skill_valid(sample_skill_file):
    skill = load_skill_from_file(sample_skill_file)
    assert skill is not None
    assert skill.name == "test_skill"
    assert "test pattern" in skill.patterns
    assert "def solve():" in skill.template

def test_load_skill_no_frontmatter(tmp_path):
    f = tmp_path / "nocontent.md"
    f.write_text("Just text", encoding="utf-8")
    skill = load_skill_from_file(str(f))
    assert skill is None

# ── Registry Tests ─────────────────────────────────────────────────────

def test_registry_scan(tmp_path):
    # Create structure
    (tmp_path / "skills" / "s1").mkdir(parents=True)
    (tmp_path / "skills" / "s1" / "SKILL.md").write_text(
        "---\nname: s1\npatterns: ['p1']\n---\nbody", encoding="utf-8"
    )
    
    registry = SkillRegistry(str(tmp_path))
    registry.load_all_skills() # This scans builtin too, but valid test
    
    # We expect at least s1. Builtins might be mocked or real depending on __file__
    s1 = registry.get_skill_by_name("s1")
    assert s1 is not None
    assert s1.matches("p1")

def test_registry_find_matching(tmp_path):
    (tmp_path / "skills" / "math").mkdir(parents=True)
    (tmp_path / "skills" / "math" / "SKILL.md").write_text(
        "---\nname: math_skill\npatterns:\n  - calc\n---\nbody", encoding="utf-8"
    )
    
    registry = SkillRegistry(str(tmp_path))
    # We patch _scan_directory to avoid loading builtins which might interfere
    with patch.object(registry, "_scan_directory") as mock_scan:
        # Manually load our temp skill
        from skills.loader import load_skill_from_file
        skill = load_skill_from_file(str(tmp_path / "skills" / "math" / "SKILL.md"))
        registry.skills.append(skill)
        
        found = registry.find_skill("Please calc this")
        assert found is not None
        assert found.name == "math_skill"
        
        not_found = registry.find_skill("random text")
        assert not_found is None

# ── Engine Integration Tests ───────────────────────────────────────────

@pytest.mark.anyio
async def test_engine_uses_skill():
    # Setup Engine with mocked components
    engine = MathEngine()
    engine.executor = MagicMock()
    engine.executor.execute.return_value = {"success": True, "result": "42"}
    
    # Mock parser (to prevent using mocked libraries)
    engine.parser = MagicMock()
    engine.parser.text_to_latex.return_value = "test input"
    
    # Mock ScriptLibrary to prevent finding existing script
    engine.script_library = MagicMock()
    engine.script_library.search.return_value = []
    
    # Mock SkillRegistry to return a specific skill
    mock_skill = MagicMock()
    mock_skill.name = "mock_skill"
    mock_skill.template = "# Mock Template"
    mock_skill.matches.return_value = True
    
    engine.skills = MagicMock(spec=SkillRegistry)
    engine.skills.find_skill.return_value = mock_skill
    
    # Mock LLM
    mock_llm = AsyncMock()
    mock_llm.understand_problem.return_value = {"category": "test", "description": "desc"}
    mock_llm.generate_solver_code.return_value = "print(42)"
    
    with patch("core.engine.get_llm_provider", return_value=mock_llm):
        await engine.solve(SolveRequest(input="test input", provider=LLMProvider.GEMINI))
        
        # Verify find_skill called
        engine.skills.find_skill.assert_called_with("test input") # after parsing
        
        # Verify LLM understand called
        mock_llm.understand_problem.assert_called()
        
        # Verify LLM generate called with understanding containing template
        call_args = mock_llm.generate_solver_code.call_args
        assert call_args is not None
        understanding_arg = call_args[0][1] # 2nd arg
        assert understanding_arg["skill_template"] == "# Mock Template"
        assert "[Using skill: mock_skill]" in understanding_arg["description"]
