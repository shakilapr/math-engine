import pytest
import logging
import sys
from unittest.mock import AsyncMock, MagicMock, patch
from pathlib import Path
from fastapi.testclient import TestClient

# Add backend to path
sys.path.append(str(Path(__file__).parent.parent / "backend"))

# Mock heavy libraries to avoid import errors in test environment
sys.modules["numpy"] = MagicMock()
sys.modules["scipy"] = MagicMock()
sys.modules["pandas"] = MagicMock()
sys.modules["matplotlib"] = MagicMock()
sys.modules["matplotlib.pyplot"] = MagicMock()
sys.modules["mpmath"] = MagicMock()
sys.modules["mpmath.libmp"] = MagicMock()
sys.modules["sympy"] = MagicMock()

from core.self_edit import SelfEditor, PatchHunk
from core.self_improve import SelfImprover, FailureContext, ImprovementProposal
from core.engine import MathEngine
from api.models import SolveRequest, LLMProvider

# Mock LLM response for failure analysis
MOCK_ANALYSIS_RESPONSE = """
```json
{
  "cause": "Division by zero in generated code",
  "location": "solver_code",
  "suspected_files": [],
  "confidence": "high"
}
```
"""

MOCK_PATCH_RESPONSE = """
```json
{
  "explanation": "Add check for zero denominator",
  "hunks": [
    {
      "kind": "update",
      "path": "core/engine.py",
      "old_text": "x = a / b",
      "new_text": "if b == 0: raise ValueError('Zero division')\\nx = a / b"
    }
  ]
}
```
"""

@pytest.fixture
def mock_editor():
    editor = MagicMock(spec=SelfEditor)
    editor.read_file.return_value = {"content": "original content"}
    return editor

@pytest.fixture
def improver(mock_editor):
    return SelfImprover(mock_editor)

@pytest.mark.anyio
async def test_analyze_failure_solver_code_error(improver):
    """Should return None if error is in solver code (not engine)."""
    context = FailureContext(
        problem_latex="1/0",
        category="arithmetic",
        error_message="ZeroDivisionError",
        generated_code="print(1/0)",
        stack_trace="Traceback...",
    )

    with patch("core.self_improve.get_llm_provider") as mock_get_llm:
        mock_llm = AsyncMock()
        mock_llm.generate.return_value = MOCK_ANALYSIS_RESPONSE
        mock_get_llm.return_value = mock_llm

        result = await improver.analyze_failure(context)
        
        # Verify LLM call
        mock_llm.generate.assert_called_once()
        # Verify result is None because location="solver_code"
        assert result is None

@pytest.mark.anyio
async def test_analyze_failure_engine_error(improver):
    """Should generate patch if error is in engine logic."""
    context = FailureContext(
        problem_latex="test", 
        category="test", 
        error_message="Bug", 
        generated_code=""
    )
    
    analysis_resp = """
    ```json
    {
      "cause": "Bug in core/engine.py",
      "location": "engine_core",
      "suspected_files": ["core/engine.py"],
      "confidence": "high"
    }
    ```
    """
    
    with patch("core.self_improve.get_llm_provider") as mock_get_llm:
        mock_llm = AsyncMock()
        # First call: analysis, Second call: patch generation
        mock_llm.generate.side_effect = [analysis_resp, MOCK_PATCH_RESPONSE]
        mock_get_llm.return_value = mock_llm

        result = await improver.analyze_failure(context)

        assert result is not None
        assert isinstance(result, ImprovementProposal)
        assert len(result.hunks) == 1
        assert result.hunks[0].path == "core/engine.py"
        
        # Verify both LLM calls
        assert mock_llm.generate.call_count == 2
        # Verify editor read file was called
        improver.editor.read_file.assert_called_with("core/engine.py")

@pytest.mark.anyio
async def test_engine_trigger_improvement(caplog):
    """MathEngine should trigger analysis on execution failure."""
    engine = MathEngine()
    
    # Mock executor to fail
    engine.executor.execute = MagicMock(return_value={
        "success": False, 
        "error": "Simulated Error",
        "traceback": "Traceback..."
    })
    
    # Mock parser (to avoid actual parsing)
    engine.parser.text_to_latex = MagicMock(return_value="test problem")
    
    # Mock LLM (to avoid actual generation)
    mock_llm = AsyncMock()
    mock_llm.understand_problem.return_value = {"category": "algebra"}
    mock_llm.generate_solver_code.return_value = "print('fail')"
    
    # Mock SelfImprover explicitly attached to engine
    engine.improver = AsyncMock(spec=SelfImprover)
    engine.improver.analyze_failure.return_value = ImprovementProposal(
        analysis="Fix proposed",
        files_to_modify=[],
        hunks=[],
        confidence="high"
    )

    with patch("core.engine.get_llm_provider", return_value=mock_llm):
        with caplog.at_level(logging.INFO):
            response = await engine.solve(SolveRequest(
                input="test problem", 
                input_type="text",
                provider=LLMProvider.GEMINI
            ))
            
            # Verify failure response
            assert response.success is False
            assert "Simulated Error" in response.error
            
            # Verify improver was called
            engine.improver.analyze_failure.assert_called_once()
            
            # Verify log message about proposed improvement
            # Verify log message about proposed improvement
            assert "Self-improvement proposed: Fix proposed" in caplog.text

def test_api_improve_endpoint():
    """Test the POST /self-edit/improve endpoint integration."""
    try:
        from main import app
    except ImportError:
        # Fallback if using relative imports or different structure
        from backend.main import app

    client = TestClient(app)
    
    # Mock the internal improver instance in routes_self_edit
    with patch("api.routes_self_edit._improver.analyze_failure", new_callable=AsyncMock) as mock_analyze:
        mock_analyze.return_value = ImprovementProposal(
            analysis="API Test Analysis",
            files_to_modify=["core/api_test.py"],
            hunks=[
                PatchHunk(kind="update", path="core/api_test.py", old_text="old", new_text="new")
            ],
            confidence="medium"
        )
        
        payload = {
            "problem_latex": "test",
            "category": "algebra",
            "error": "Test Error",
            "code": "print(1)",
            "traceback": "Traceback"
        }
        
        response = client.post("/api/self-edit/improve", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert data["analysis"] == "API Test Analysis"
        assert "core/api_test.py" in data["files"]
        assert data["confidence"] == "medium"
        
        mock_analyze.assert_called_once()
        args = mock_analyze.call_args[0][0] # First arg is FailureContext
        assert args.error_message == "Test Error"
