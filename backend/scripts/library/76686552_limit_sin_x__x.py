
import sympy as sp
x = sp.symbols('x')
expr = sp.sin(x)/x
limit_val = sp.limit(expr, x, 0)
_steps = [
    {"description": "Identify limit expression.", "latex": sp.latex(expr), "code": "expr = sp.sin(x)/x"},
    {"description": "Apply limit as x -> 0, using known limit sin(x)/x -> 1.", "latex": "\lim_{x \to 0} \frac{\sin(x)}{x} = 1", "code": "limit_val = sp.limit(expr, x, 0)"}
]
_result = limit_val
_result_latex = sp.latex(limit_val)
