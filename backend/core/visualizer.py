"""
Math visualization generator — produces plots and diagrams.
Uses matplotlib and plotly to create visual representations.
"""
from __future__ import annotations

import os
import uuid
from typing import Any

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import sympy as sp

from api.models import Visualization


PLOT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "outputs", "plots")


class MathVisualizer:
    """Generate mathematical visualizations."""

    def __init__(self):
        os.makedirs(PLOT_DIR, exist_ok=True)

    def generate(
        self,
        problem_latex: str,
        solver_code: str,
        exec_result: dict[str, Any],
    ) -> list[Visualization]:
        """Generate visualizations from the problem context."""
        visualizations: list[Visualization] = []

        # Check if the executed code produced any plots
        plots_data = exec_result.get("plots", [])
        for plot_info in plots_data:
            vis = self._save_plot(plot_info)
            if vis:
                visualizations.append(vis)

        # Try to auto-generate a function plot if applicable
        auto_vis = self._auto_plot(solver_code, exec_result)
        if auto_vis:
            visualizations.append(auto_vis)

        return visualizations

    def _save_plot(self, plot_info: dict) -> Visualization | None:
        """Save a plot from execution data."""
        try:
            fig = plot_info.get("figure")
            title = plot_info.get("title", "Plot")
            desc = plot_info.get("description", "")

            if fig is None:
                return None

            filename = f"{uuid.uuid4().hex[:12]}.png"
            filepath = os.path.join(PLOT_DIR, filename)
            fig.savefig(filepath, dpi=150, bbox_inches="tight", facecolor="#1a1a2e")
            plt.close(fig)

            return Visualization(
                title=title,
                image_url=f"/static/plots/{filename}",
                description=desc,
            )
        except Exception:
            return None

    def _auto_plot(
        self, solver_code: str, exec_result: dict
    ) -> Visualization | None:
        """Try to auto-generate a plot from the solver code (e.g., function graphs)."""
        try:
            # Look for single-variable functions in the result
            result = exec_result.get("result", "")
            if not result:
                return None

            # Try to parse as a sympy expression and plot
            x = sp.Symbol("x")
            try:
                expr = sp.sympify(result)
                if expr.free_symbols == {x}:
                    return self._plot_function(expr, x)
            except Exception:
                pass

            return None
        except Exception:
            return None

    def _plot_function(
        self, expr: sp.Expr, var: sp.Symbol, x_range: tuple = (-10, 10)
    ) -> Visualization | None:
        """Plot a single-variable function."""
        try:
            f = sp.lambdify(var, expr, modules=["numpy"])
            x_vals = np.linspace(x_range[0], x_range[1], 500)

            # Handle potential infinities
            with np.errstate(all="ignore"):
                y_vals = f(x_vals)
                y_vals = np.where(np.isfinite(y_vals), y_vals, np.nan)

            fig, ax = plt.subplots(figsize=(10, 6))
            fig.patch.set_facecolor("#1a1a2e")
            ax.set_facecolor("#16213e")

            ax.plot(x_vals, y_vals, color="#00d4ff", linewidth=2)
            ax.axhline(y=0, color="#ffffff", linewidth=0.5, alpha=0.3)
            ax.axvline(x=0, color="#ffffff", linewidth=0.5, alpha=0.3)
            ax.grid(True, alpha=0.15, color="#ffffff")
            ax.set_title(
                f"$y = {sp.latex(expr)}$",
                color="#ffffff", fontsize=14, pad=15,
            )
            ax.tick_params(colors="#888888")
            for spine in ax.spines.values():
                spine.set_color("#333355")

            filename = f"{uuid.uuid4().hex[:12]}.png"
            filepath = os.path.join(PLOT_DIR, filename)
            fig.savefig(filepath, dpi=150, bbox_inches="tight", facecolor="#1a1a2e")
            plt.close(fig)

            return Visualization(
                title=f"Graph of y = {sp.latex(expr)}",
                image_url=f"/static/plots/{filename}",
                description=f"Plot of the function y = {expr}",
            )
        except Exception:
            return None
