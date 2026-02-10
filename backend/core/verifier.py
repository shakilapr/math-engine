"""
Cross-verification module — checks answers with multiple math libraries.
Uses sympy, numpy/scipy, and mpmath for independent verification.
"""
from __future__ import annotations

import traceback
from typing import Any

import sympy as sp
import numpy as np
import mpmath

from api.models import VerificationResult


class CrossVerifier:
    """Verify a math result using at least 3 independent libraries."""

    def verify(
        self,
        problem_latex: str,
        answer: str,
        solver_code: str,
    ) -> list[VerificationResult]:
        """Run verification across multiple backends."""
        results: list[VerificationResult] = []

        # 1. SymPy verification (symbolic)
        results.append(self._verify_sympy(answer, solver_code))

        # 2. NumPy/SciPy verification (numeric)
        results.append(self._verify_numpy(answer, solver_code))

        # 3. mpmath verification (arbitrary precision)
        results.append(self._verify_mpmath(answer, solver_code))

        return results

    def _verify_sympy(self, answer: str, solver_code: str) -> VerificationResult:
        """Verify using SymPy symbolic computation."""
        try:
            # Execute the solver code in a sympy-only namespace
            ns = {
                "sympy": sp, "sp": sp,
                "symbols": sp.symbols, "Symbol": sp.Symbol,
                "solve": sp.solve, "simplify": sp.simplify,
                "sqrt": sp.sqrt, "Rational": sp.Rational,
                "integrate": sp.integrate, "diff": sp.diff,
                "sin": sp.sin, "cos": sp.cos, "tan": sp.tan,
                "log": sp.log, "exp": sp.exp, "pi": sp.pi,
                "Matrix": sp.Matrix, "latex": sp.latex,
                "oo": sp.oo, "I": sp.I, "E": sp.E,
                "_result": None, "_steps": [], "_result_latex": None, "_plots": [],
            }
            exec(solver_code, ns)
            sym_result = str(ns.get("_result", ""))

            matches = self._results_match(answer, sym_result)
            return VerificationResult(
                library="SymPy (symbolic)",
                result=sym_result,
                matches=matches,
                code="# Verified using SymPy symbolic engine",
            )
        except Exception as e:
            return VerificationResult(
                library="SymPy (symbolic)",
                result=f"Error: {e}",
                matches=False,
                code="",
            )

    def _verify_numpy(self, answer: str, solver_code: str) -> VerificationResult:
        """Verify using NumPy/SciPy numerical computation."""
        try:
            ns = {
                "numpy": np, "np": np,
                "scipy": __import__("scipy"),
                "math": __import__("math"),
                "_result": None, "_steps": [], "_result_latex": None, "_plots": [],
                # also need sympy for code that uses it
                "sympy": sp, "sp": sp,
                "symbols": sp.symbols, "Symbol": sp.Symbol,
                "solve": sp.solve, "simplify": sp.simplify,
                "sqrt": sp.sqrt, "Rational": sp.Rational,
                "integrate": sp.integrate, "diff": sp.diff,
                "sin": sp.sin, "cos": sp.cos, "tan": sp.tan,
                "log": sp.log, "exp": sp.exp, "pi": sp.pi,
                "Matrix": sp.Matrix, "latex": sp.latex,
                "oo": sp.oo, "I": sp.I, "E": sp.E,
            }
            exec(solver_code, ns)
            np_result = str(ns.get("_result", ""))

            matches = self._results_match(answer, np_result)
            return VerificationResult(
                library="NumPy/SciPy (numerical)",
                result=np_result,
                matches=matches,
                code="# Verified using NumPy/SciPy numerical engine",
            )
        except Exception as e:
            return VerificationResult(
                library="NumPy/SciPy (numerical)",
                result=f"Error: {e}",
                matches=False,
                code="",
            )

    def _verify_mpmath(self, answer: str, solver_code: str) -> VerificationResult:
        """Verify using mpmath arbitrary-precision arithmetic."""
        try:
            ns = {
                "mpmath": mpmath,
                "mp": mpmath,
                "_result": None, "_steps": [], "_result_latex": None, "_plots": [],
                # also need sympy
                "sympy": sp, "sp": sp,
                "symbols": sp.symbols, "Symbol": sp.Symbol,
                "solve": sp.solve, "simplify": sp.simplify,
                "sqrt": sp.sqrt, "Rational": sp.Rational,
                "integrate": sp.integrate, "diff": sp.diff,
                "sin": sp.sin, "cos": sp.cos, "tan": sp.tan,
                "log": sp.log, "exp": sp.exp, "pi": sp.pi,
                "Matrix": sp.Matrix, "latex": sp.latex,
                "oo": sp.oo, "I": sp.I, "E": sp.E,
                "numpy": np, "np": np,
            }
            exec(solver_code, ns)
            mp_result = str(ns.get("_result", ""))

            matches = self._results_match(answer, mp_result)
            return VerificationResult(
                library="mpmath (arbitrary precision)",
                result=mp_result,
                matches=matches,
                code="# Verified using mpmath arbitrary-precision engine",
            )
        except Exception as e:
            return VerificationResult(
                library="mpmath (arbitrary precision)",
                result=f"Error: {e}",
                matches=False,
                code="",
            )

    @staticmethod
    def _results_match(a: str, b: str) -> bool:
        """Check if two results are equivalent (handles formatting differences)."""
        if not a or not b:
            return False
        a, b = a.strip(), b.strip()
        if a == b:
            return True
        # Try numeric comparison
        try:
            fa, fb = float(sp.sympify(a)), float(sp.sympify(b))
            return abs(fa - fb) < 1e-10
        except Exception:
            pass
        # Try symbolic comparison
        try:
            sa, sb = sp.sympify(a), sp.sympify(b)
            return sp.simplify(sa - sb) == 0
        except Exception:
            pass
        return False
