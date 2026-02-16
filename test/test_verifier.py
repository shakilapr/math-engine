"""
Unit tests for CrossVerifier — cross‑library verification of math results.
Tests cover:
- verify() orchestrates three verification backends
- Each backend returns a VerificationResult
- Matching logic for numeric and symbolic equivalence
- Error handling (exception catching)
"""
from __future__ import annotations

import sys
import pytest
from unittest.mock import MagicMock, patch, call
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from core.verifier import CrossVerifier
from api.models import VerificationResult


# ── Fixtures ───────────────────────────────────────────────────────────

@pytest.fixture
def verifier():
    """Create a CrossVerifier instance."""
    return CrossVerifier()


# ── Verify Orchestration Tests ────────────────────────────────────────

def test_verify_calls_all_backends(verifier: CrossVerifier):
    """verify() should call each of the three verification methods."""
    with patch.object(verifier, '_verify_sympy') as mock_sympy, \
         patch.object(verifier, '_verify_numpy') as mock_numpy, \
         patch.object(verifier, '_verify_mpmath') as mock_mpmath:
        mock_sympy.return_value = VerificationResult(
            library="SymPy (symbolic)", result="42", matches=True, code="")
        mock_numpy.return_value = VerificationResult(
            library="NumPy/SciPy (numerical)", result="42", matches=True, code="")
        mock_mpmath.return_value = VerificationResult(
            library="mpmath (arbitrary precision)", result="42", matches=True, code="")

        results = verifier.verify(
            problem_latex="test",
            answer="42",
            solver_code="_result = 42"
        )
        assert len(results) == 3
        mock_sympy.assert_called_once_with("42", "_result = 42")
        mock_numpy.assert_called_once_with("42", "_result = 42")
        mock_mpmath.assert_called_once_with("42", "_result = 42")


# ── Backend Verification Tests (with mocked exec) ─────────────────────

def test_verify_sympy_success():
    """SymPy verification returns a result when code runs."""
    verifier = CrossVerifier()
    solver_code = """
_result = 42
_result_latex = "42"
_steps = []
"""
    with patch('builtins.exec') as mock_exec:
        # Simulate namespace after exec
        def side_effect(code, ns):
            ns['_result'] = 42
            ns['_result_latex'] = "42"
        mock_exec.side_effect = side_effect

        result = verifier._verify_sympy("42", solver_code)
        assert result.library == "SymPy (symbolic)"
        assert result.result == "42"
        assert result.matches is True
        assert "SymPy symbolic engine" in result.code


def test_verify_sympy_error():
    """SymPy verification catches exceptions and returns error result."""
    verifier = CrossVerifier()
    solver_code = "raise ValueError('test')"
    with patch('builtins.exec', side_effect=ValueError('test')):
        result = verifier._verify_sympy("42", solver_code)
        assert result.library == "SymPy (symbolic)"
        assert "Error" in result.result
        assert result.matches is False


def test_verify_numpy_success():
    """NumPy verification returns a result."""
    verifier = CrossVerifier()
    solver_code = "_result = 3.14"
    with patch('builtins.exec') as mock_exec:
        def side_effect(code, ns):
            ns['_result'] = 3.14
        mock_exec.side_effect = side_effect

        result = verifier._verify_numpy("3.14", solver_code)
        assert result.library == "NumPy/SciPy (numerical)"
        assert result.result == "3.14"
        assert result.matches is True


def test_verify_numpy_error():
    """NumPy verification catches exceptions."""
    verifier = CrossVerifier()
    with patch('builtins.exec', side_effect=RuntimeError('numpy error')):
        result = verifier._verify_numpy("3.14", "")
        assert result.library == "NumPy/SciPy (numerical)"
        assert "Error" in result.result
        assert result.matches is False


def test_verify_mpmath_success():
    """mpmath verification returns a result."""
    verifier = CrossVerifier()
    solver_code = "_result = 1.61803398875"
    with patch('builtins.exec') as mock_exec:
        def side_effect(code, ns):
            ns['_result'] = 1.61803398875
        mock_exec.side_effect = side_effect

        result = verifier._verify_mpmath("1.61803398875", solver_code)
        assert result.library == "mpmath (arbitrary precision)"
        assert result.result == "1.61803398875"
        assert result.matches is True


def test_verify_mpmath_error():
    """mpmath verification catches exceptions."""
    verifier = CrossVerifier()
    with patch('builtins.exec', side_effect=ImportError('mpmath missing')):
        result = verifier._verify_mpmath("0", "")
        assert result.library == "mpmath (arbitrary precision)"
        assert "Error" in result.result
        assert result.matches is False


# ── Results Match Logic Tests ────────────────────────────────────────

def test_results_match_exact_strings():
    """Exact string equality should match."""
    assert CrossVerifier._results_match("42", "42") is True
    assert CrossVerifier._results_match("x^2", "x^2") is True
    assert CrossVerifier._results_match("", "") is False  # empty strings considered false
    assert CrossVerifier._results_match("a", "b") is False


def test_results_match_numeric():
    """Numeric equality within tolerance."""
    assert CrossVerifier._results_match("3.14159", "3.14159") is True
    assert CrossVerifier._results_match("3.14159", "3.14159000001") is True  # within 1e-10 (diff 1e-11)
    assert CrossVerifier._results_match("1.0", "1.000000000001") is True
    assert CrossVerifier._results_match("1.0", "1.1") is False


def test_results_match_symbolic():
    """Symbolic equality via sympy.simplify."""
    # This test depends on sympy being available; we'll mock sympy.sympify
    with patch('core.verifier.sp') as mock_sp:
        # Create a mock expression that raises TypeError when float() is called
        # (to ensure numeric comparison fails and symbolic path is taken)
        mock_expr = MagicMock()
        mock_expr.__float__ = MagicMock(side_effect=TypeError("cannot convert to float"))
        mock_sp.sympify.side_effect = lambda x: mock_expr
        mock_sp.simplify.return_value = MagicMock(__eq__=lambda self, other: True)
        assert CrossVerifier._results_match("x + x", "2*x") is True

        mock_sp.simplify.return_value = MagicMock(__eq__=lambda self, other: False)
        assert CrossVerifier._results_match("x", "y") is False


def test_results_match_mixed():
    """Edge cases: empty strings, None."""
    assert CrossVerifier._results_match("", "42") is False
    assert CrossVerifier._results_match("42", "") is False
    # Non‑numeric strings that cannot be sympified should return False
    with patch('core.verifier.sp.sympify', side_effect=Exception):
        assert CrossVerifier._results_match("not a number", "also not") is False


# ── Integration with Real Libraries (if installed) ───────────────────

def test_verify_with_simple_code(verifier: CrossVerifier):
    """
    A simple integration test that uses the actual libraries (if they are present).
    This test may be skipped if numpy/sympy/mpmath are not installed.
    """
    try:
        import numpy
        import sympy
        import mpmath
    except ImportError:
        pytest.skip("Required libraries not installed")

    solver_code = """
import sympy as sp
x = sp.Symbol('x')
_result = sp.integrate(x**2, (x, 0, 1))
"""
    results = verifier.verify("integral", "1/3", solver_code)
    assert len(results) == 3
    # At least one verification should match (likely SymPy)
    matches = [r.matches for r in results]
    assert any(matches), f"All verifications failed: {results}"


def test_verify_with_error_code(verifier: CrossVerifier):
    """Verification should gracefully handle code that raises an error."""
    solver_code = "raise ValueError('intentional error')"
    results = verifier.verify("problem", "answer", solver_code)
    for r in results:
        assert not r.matches
        assert "Error" in r.result


# ── Edge Cases ──────────────────────────────────────────────────────

def test_verify_empty_answer(verifier: CrossVerifier):
    """Empty answer should not match anything."""
    solver_code = "_result = 0"
    results = verifier.verify("", "", solver_code)
    for r in results:
        # Because answer is empty string, matches should be False
        assert r.matches is False or "Error" in r.result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])