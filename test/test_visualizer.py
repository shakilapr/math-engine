"""
Unit tests for MathVisualizer — mathematical plot generation.
Tests cover:
- generate() with plots from exec_result
- _save_plot() with mocked figure
- _auto_plot() for single-variable functions
- _plot_function() integration with sympy
- Error handling (exceptions)
"""
from __future__ import annotations

import sys
import os
import tempfile
import uuid
from pathlib import Path
from unittest.mock import MagicMock, patch, call
import pytest

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from core.visualizer import MathVisualizer, PLOT_DIR
import core.visualizer
from api.models import Visualization


# ── Fixtures ───────────────────────────────────────────────────────────

@pytest.fixture
def visualizer():
    """Create a MathVisualizer instance with temporary plot directory."""
    # Temporarily override PLOT_DIR to a temporary directory
    with tempfile.TemporaryDirectory() as tmpdir:
        with patch('core.visualizer.PLOT_DIR', tmpdir):
            yield MathVisualizer()


@pytest.fixture
def mock_figure():
    """Create a mock matplotlib figure."""
    fig = MagicMock()
    fig.savefig = MagicMock()
    return fig


# ── Generate Tests ─────────────────────────────────────────────────────

def test_generate_empty_plots(visualizer: MathVisualizer):
    """generate() with no plots returns empty list."""
    result = visualizer.generate(
        problem_latex="x^2",
        solver_code="",
        exec_result={"plots": []}
    )
    assert result == []


def test_generate_with_plots(visualizer: MathVisualizer, mock_figure):
    """generate() processes plots from exec_result."""
    plot_info = {
        "figure": mock_figure,
        "title": "Test Plot",
        "description": "A test"
    }
    exec_result = {"plots": [plot_info]}
    with patch('core.visualizer.uuid') as mock_uuid:
        mock_uuid.uuid4.return_value.hex = "1234567890ab"
        result = visualizer.generate("x^2", "", exec_result)
    assert len(result) == 1
    vis = result[0]
    assert isinstance(vis, Visualization)
    assert vis.title == "Test Plot"
    assert vis.description == "A test"
    assert vis.image_url == "/static/plots/1234567890ab.png"
    # Ensure savefig was called
    mock_figure.savefig.assert_called_once()
    plt_mock = MagicMock()
    with patch('core.visualizer.plt', plt_mock):
        # plt.close is called within _save_plot
        pass


def test_generate_with_auto_plot(visualizer: MathVisualizer):
    """generate() triggers auto_plot if no plots provided."""
    exec_result = {"plots": [], "result": "x**2"}
    with patch.object(visualizer, '_auto_plot') as mock_auto:
        mock_auto.return_value = Visualization(
            title="Auto", image_url="/static/plots/auto.png", description=""
        )
        result = visualizer.generate("x^2", "code", exec_result)
        mock_auto.assert_called_once_with("code", exec_result)
        assert len(result) == 1
        assert result[0].title == "Auto"


# ── Save Plot Tests ───────────────────────────────────────────────────

def test_save_plot_success(visualizer: MathVisualizer, mock_figure):
    """_save_plot returns a Visualization when figure is present."""
    plot_info = {
        "figure": mock_figure,
        "title": "Test",
        "description": "Desc"
    }
    with patch('core.visualizer.uuid') as mock_uuid:
        mock_uuid.uuid4.return_value.hex = "abc123"
        result = visualizer._save_plot(plot_info)
    assert result is not None
    assert result.title == "Test"
    assert result.description == "Desc"
    assert result.image_url == "/static/plots/abc123.png"
    mock_figure.savefig.assert_called_once()
    # Check that plt.close was called (via patch)
    # We'll verify that the file path is correct
    expected_path = os.path.join(core.visualizer.PLOT_DIR, "abc123.png")
    mock_figure.savefig.assert_called_with(expected_path, dpi=150, bbox_inches="tight", facecolor="#1a1a2e")


def test_save_plot_no_figure(visualizer: MathVisualizer):
    """_save_plot returns None if figure is missing."""
    plot_info = {"title": "No figure"}
    result = visualizer._save_plot(plot_info)
    assert result is None


def test_save_plot_exception(visualizer: MathVisualizer, mock_figure):
    """_save_plot returns None on exception."""
    mock_figure.savefig.side_effect = RuntimeError("save failed")
    plot_info = {"figure": mock_figure, "title": "Error"}
    result = visualizer._save_plot(plot_info)
    assert result is None


# ── Auto Plot Tests ───────────────────────────────────────────────────

def test_auto_plot_no_result(visualizer: MathVisualizer):
    """_auto_plot returns None if result is empty."""
    exec_result = {"result": ""}
    result = visualizer._auto_plot("code", exec_result)
    assert result is None


def test_auto_plot_with_sympy_function(visualizer: MathVisualizer):
    """_auto_plot returns a plot for a single-variable expression."""
    exec_result = {"result": "x**2"}
    with patch.object(visualizer, '_plot_function') as mock_plot:
        mock_plot.return_value = Visualization(title="Plot", image_url="", description="")
        result = visualizer._auto_plot("code", exec_result)
        # Check that _plot_function was called with appropriate sympy expression
        # We can assert that mock_plot was called with expected args
        assert mock_plot.called
        # First argument should be a sympy expression x**2
        arg_expr = mock_plot.call_args[0][0]
        assert str(arg_expr) == "x**2"  # sympy expression
        assert result is not None


def test_auto_plot_sympify_fails(visualizer: MathVisualizer):
    """_auto_plot returns None if sympify fails."""
    exec_result = {"result": "invalid expression!!"}
    with patch('core.visualizer.sp.sympify', side_effect=Exception):
        result = visualizer._auto_plot("code", exec_result)
        assert result is None


def test_auto_plot_multi_variable(visualizer: MathVisualizer):
    """_auto_plot returns None for multi-variable expression."""
    exec_result = {"result": "x + y"}
    with patch('core.visualizer.sp.sympify') as mock_sympify:
        mock_expr = MagicMock()
        mock_expr.free_symbols = {MagicMock(), MagicMock()}  # two symbols
        mock_sympify.return_value = mock_expr
        result = visualizer._auto_plot("code", exec_result)
        assert result is None


# ── Plot Function Tests ───────────────────────────────────────────────

def test_plot_function_success(visualizer: MathVisualizer):
    """_plot_function creates a plot and returns a Visualization."""
    import sympy as sp
    x = sp.Symbol('x')
    expr = x**2
    with patch('core.visualizer.np.linspace') as mock_linspace, \
         patch('core.visualizer.sp.lambdify') as mock_lambdify, \
         patch('core.visualizer.plt.subplots') as mock_subplots, \
         patch('core.visualizer.uuid') as mock_uuid:
        # Setup mocks
        mock_linspace.return_value = [0, 1, 2]
        mock_f = MagicMock(return_value=[0, 1, 4])
        mock_lambdify.return_value = mock_f
        mock_fig = MagicMock()
        mock_ax = MagicMock()
        mock_subplots.return_value = (mock_fig, mock_ax)
        mock_uuid.uuid4.return_value.hex = "plot123"
        
        result = visualizer._plot_function(expr, x)
        assert result is not None
        assert isinstance(result, Visualization)
        assert result.title.startswith("Graph of y =")
        assert result.image_url == "/static/plots/plot123.png"
        # Verify subplots called
        mock_subplots.assert_called_once_with(figsize=(10, 6))
        # Verify savefig called
        mock_fig.savefig.assert_called_once()
        # Verify lambdify called with correct arguments
        mock_lambdify.assert_called_with(x, expr, modules=["numpy"])


def test_plot_function_exception(visualizer: MathVisualizer):
    """_plot_function returns None on exception."""
    import sympy as sp
    x = sp.Symbol('x')
    expr = x**2
    with patch('core.visualizer.sp.lambdify', side_effect=RuntimeError):
        result = visualizer._plot_function(expr, x)
        assert result is None


def test_plot_function_with_nan(visualizer: MathVisualizer):
    """_plot_function handles NaN/infinite values."""
    import sympy as sp
    import numpy as np
    x = sp.Symbol('x')
    expr = 1 / x  # division by zero at x=0
    with patch('core.visualizer.np.linspace') as mock_linspace, \
         patch('core.visualizer.sp.lambdify') as mock_lambdify, \
         patch('core.visualizer.plt.subplots') as mock_subplots, \
         patch('core.visualizer.uuid'):
        mock_linspace.return_value = np.array([-1, 0, 1])
        # Simulate division by zero leading to inf
        mock_f = MagicMock(return_value=np.array([-1.0, np.inf, 1.0]))
        mock_lambdify.return_value = mock_f
        mock_fig = MagicMock()
        mock_ax = MagicMock()
        mock_subplots.return_value = (mock_fig, mock_ax)
        # Should not raise; np.where will replace inf with nan
        result = visualizer._plot_function(expr, x)
        # Expect a plot
        assert result is not None


# ── Integration with File System ──────────────────────────────────────

def test_plot_directory_creation():
    """MathVisualizer creates PLOT_DIR on init."""
    with tempfile.TemporaryDirectory() as tmpdir:
        with patch('core.visualizer.PLOT_DIR', tmpdir):
            # Ensure directory does not exist yet
            import shutil
            if os.path.exists(tmpdir):
                shutil.rmtree(tmpdir)
            visualizer = MathVisualizer()
            assert os.path.exists(tmpdir)
            assert os.path.isdir(tmpdir)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])