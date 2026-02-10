"""
Input parser — handles LaTeX, text, and image inputs.
"""
from __future__ import annotations

import base64
import io
import re
import tempfile
import os
from typing import Optional

import sympy as sp


class InputParser:
    """Parse different input formats into LaTeX."""

    def text_to_latex(self, text: str) -> str:
        """Convert a text math problem into LaTeX representation.
        
        Handles common patterns like:
        - "solve x^2 + 3x - 4 = 0"
        - "integrate sin(x) from 0 to pi"
        - "derivative of x^3 + 2x"
        - "limit of (sin(x)/x) as x approaches 0"
        """
        text = text.strip()

        # If it already looks like LaTeX (has \commands or $...$), return as-is
        if re.search(r"\\[a-zA-Z]+", text) or "$" in text:
            # Strip $ wrapping if present
            text = text.strip("$").strip()
            return text

        # Try to parse with sympy
        try:
            expr = sp.sympify(text, evaluate=False)
            return sp.latex(expr)
        except Exception:
            pass

        # Common text patterns → LaTeX conversions
        conversions = [
            # Powers: x^2, x**2
            (r"(\w)\*\*(\d+)", r"\1^{\2}"),
            (r"(\w)\^(\d+)", r"\1^{\2}"),
            # Fractions: a/b
            (r"(\d+)/(\d+)", r"\\frac{\1}{\2}"),
            # Square root
            (r"sqrt\(([^)]+)\)", r"\\sqrt{\1}"),
            # Trig functions
            (r"\bsin\b", r"\\sin"),
            (r"\bcos\b", r"\\cos"),
            (r"\btan\b", r"\\tan"),
            (r"\blog\b", r"\\log"),
            (r"\bln\b", r"\\ln"),
            # Special values
            (r"\bpi\b", r"\\pi"),
            (r"\binfinity\b", r"\\infty"),
            (r"\binf\b", r"\\infty"),
            # Integral notation
            (r"integrate\s+(.+?)\s+from\s+(\S+)\s+to\s+(\S+)",
             r"\\int_{\2}^{\3} \1 \\, dx"),
            (r"integral\s+of\s+(.+)",
             r"\\int \1 \\, dx"),
            # Derivative notation
            (r"derivative\s+of\s+(.+)",
             r"\\frac{d}{dx}\\left(\1\\right)"),
            (r"d/dx\s+(.+)",
             r"\\frac{d}{dx}\\left(\1\\right)"),
            # Limit notation
            (r"limit\s+(?:of\s+)?(.+?)\s+as\s+(\w+)\s+(?:approaches|->|→)\s+(\S+)",
             r"\\lim_{\2 \\to \3} \1"),
            # Sum notation
            (r"sum\s+(.+?)\s+from\s+(\w+)=(\S+)\s+to\s+(\S+)",
             r"\\sum_{\2=\3}^{\4} \1"),
            # Multiplication dot
            (r"\*", r"\\cdot "),
        ]

        result = text
        for pattern, replacement in conversions:
            result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)

        return result

    async def image_to_latex(self, image_data: str) -> str:
        """Convert base64 image to LaTeX using pix2tex.
        
        Args:
            image_data: Base64 encoded image string
        """
        try:
            from PIL import Image
            from pix2tex.cli import LatexOCR

            # Decode base64 image
            if "," in image_data:
                image_data = image_data.split(",", 1)[1]

            image_bytes = base64.b64decode(image_data)
            image = Image.open(io.BytesIO(image_bytes))

            # Run OCR
            model = LatexOCR()
            latex = model(image)

            return latex
        except ImportError:
            raise RuntimeError(
                "pix2tex is not installed. Install it with: pip install pix2tex"
            )
        except Exception as e:
            raise RuntimeError(f"Failed to convert image to LaTeX: {e}")
