"""
Safe code executor — runs LLM-generated Python in a restricted sandbox.
"""
from __future__ import annotations

import ast
import io
import sys
import traceback
import math
from typing import Any

import numpy as np
import sympy as sp
import mpmath
import scipy


# Allowed modules in the sandbox
ALLOWED_MODULES = {
    "math": math,
    "numpy": np,
    "np": np,
    "sympy": sp,
    "sp": sp,
    "mpmath": mpmath,
    "scipy": scipy,
    "fractions": __import__("fractions"),
    "itertools": __import__("itertools"),
    "functools": __import__("functools"),
    "collections": __import__("collections"),
}

# Blocked builtins
BLOCKED_BUILTINS = {
    "exec", "eval", "compile", "__import__", "open",
    "input", "breakpoint", "exit", "quit",
}


class SafeExecutor:
    """Execute generated Python code in a restricted namespace."""

    def __init__(self, timeout: float = 30.0):
        self.timeout = timeout

    def _build_namespace(self) -> dict[str, Any]:
        """Build a safe execution namespace."""
        import builtins as _builtins

        safe_builtins = {
            k: v for k, v in vars(_builtins).items()
            if k not in BLOCKED_BUILTINS
        }
        safe_builtins["__import__"] = self._safe_import

        ns: dict[str, Any] = {
            "__builtins__": safe_builtins,
            # Pre-import common math libraries
            "np": np,
            "numpy": np,
            "sp": sp,
            "sympy": sp,
            "mpmath": mpmath,
            "scipy": scipy,
            "math": math,
            "Rational": sp.Rational,
            "Symbol": sp.Symbol,
            "symbols": sp.symbols,
            "sqrt": sp.sqrt,
            "sin": sp.sin,
            "cos": sp.cos,
            "tan": sp.tan,
            "log": sp.log,
            "exp": sp.exp,
            "pi": sp.pi,
            "E": sp.E,
            "oo": sp.oo,
            "I": sp.I,
            "Matrix": sp.Matrix,
            "integrate": sp.integrate,
            "diff": sp.diff,
            "limit": sp.limit,
            "summation": sp.summation,
            "solve": sp.solve,
            "simplify": sp.simplify,
            "expand": sp.expand,
            "factor": sp.factor,
            "series": sp.series,
            "latex": sp.latex,
            # Results container
            "_steps": [],
            "_result": None,
            "_result_latex": None,
            "_plots": [],
        }
        return ns

    @staticmethod
    def _safe_import(name: str, *args, **kwargs):
        """Only allow importing from the allowlist."""
        if name in ALLOWED_MODULES:
            return ALLOWED_MODULES[name]
        # Allow sub-imports for allowed top-level packages
        top = name.split(".")[0]
        if top in ALLOWED_MODULES:
            return __import__(name, *args, **kwargs)
        raise ImportError(f"Import of '{name}' is not allowed in sandbox")

    def execute(self, code: str) -> dict[str, Any]:
        """
        Execute code and return results.

        The generated code should set:
          _result       — final answer (any type)
          _result_latex — LaTeX string of the final answer
          _steps        — list of dicts with keys:
                          {description, expression, result, latex}
        """
        try:
            # Basic AST validation
            tree = ast.parse(code)
            self._validate_ast(tree)
        except SyntaxError as e:
            return {"success": False, "error": f"Syntax error: {e}"}
        except SecurityError as e:
            return {"success": False, "error": str(e)}

        ns = self._build_namespace()

        # Capture stdout
        old_stdout = sys.stdout
        sys.stdout = captured = io.StringIO()

        try:
            exec(compile(tree, "<solver>", "exec"), ns)

            result = ns.get("_result")
            result_latex = ns.get("_result_latex", "")
            steps = ns.get("_steps", [])
            plots = ns.get("_plots", [])

            # Try to convert result to latex if not provided
            if result is not None and not result_latex:
                try:
                    result_latex = sp.latex(result)
                except Exception:
                    result_latex = str(result)

            return {
                "success": True,
                "result": str(result) if result is not None else "",
                "result_latex": result_latex or "",
                "steps": steps,
                "plots": plots,
                "stdout": captured.getvalue(),
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"{type(e).__name__}: {e}",
                "traceback": traceback.format_exc(),
            }
        finally:
            sys.stdout = old_stdout

    def _validate_ast(self, tree: ast.AST):
        """Walk AST and block dangerous patterns."""
        for node in ast.walk(tree):
            # Block os/sys/subprocess access
            if isinstance(node, ast.Import):
                for alias in node.names:
                    top = alias.name.split(".")[0]
                    if top not in ALLOWED_MODULES:
                        raise SecurityError(f"Import of '{alias.name}' is blocked")
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    top = node.module.split(".")[0]
                    if top not in ALLOWED_MODULES:
                        raise SecurityError(f"Import from '{node.module}' is blocked")
            # Block attribute access to dangerous objects
            elif isinstance(node, ast.Attribute):
                if node.attr in ("system", "popen", "remove", "rmdir", "unlink"):
                    raise SecurityError(f"Access to '.{node.attr}' is blocked")


class SecurityError(Exception):
    pass
