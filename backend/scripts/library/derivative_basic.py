"""
Compute derivative of a polynomial or simple function.
"""
import sympy as sp

x = sp.symbols('x')
# Function expression placeholder
expr = sp.sympify('x**3 + 2*x')

# Compute derivative
derivative = sp.diff(expr, x)

# Steps
_steps = [
    {
        "description": "Identify the function to differentiate.",
        "expression": sp.latex(expr),
        "result": "",
        "latex": sp.latex(expr),
        "code": "expr = x**3 + 2*x"
    },
    {
        "description": "Apply the power rule: d/dx x^n = n x^(n-1).",
        "expression": "d/dx (x^3) = 3*x^2, d/dx (2*x) = 2",
        "result": "",
        "latex": "\\frac{d}{dx} x^{3} = 3 x^{2}, \\quad \\frac{d}{dx} (2x) = 2",
        "code": "derivative = sp.diff(expr, x)"
    },
    {
        "description": "Sum the derivatives.",
        "expression": "3*x^2 + 2",
        "result": sp.latex(derivative),
        "latex": sp.latex(derivative),
        "code": "derivative = 3*x**2 + 2"
    }
]

_result = derivative
_result_latex = sp.latex(derivative)