
import sympy as sp
x = sp.symbols('x')
expr = sp.sympify('x**3 + 2*x')
derivative = sp.diff(expr, x)
_steps = [
    {"description": "Identify function.", "latex": sp.latex(expr), "code": "expr = x**3 + 2*x"},
    {"description": "Apply power rule.", "latex": "\frac{d}{dx} x^{3} = 3 x^{2}", "code": "sp.diff(x**3, x)"},
    {"description": "Sum derivatives.", "latex": sp.latex(derivative), "code": "derivative = 3*x**2 + 2"}
]
_result = derivative
_result_latex = sp.latex(derivative)
