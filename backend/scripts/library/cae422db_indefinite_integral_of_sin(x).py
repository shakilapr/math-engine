
import sympy as sp
x = sp.symbols('x')
expr = sp.sin(x)
integral = sp.integrate(expr, x)
_steps = [
    {"description": "Identify integrand.", "latex": sp.latex(expr), "code": "expr = sp.sin(x)"},
    {"description": "Recall antiderivative of sin(x) is -cos(x).", "latex": "\int \sin(x)\,dx = -\cos(x) + C", "code": "integral = -sp.cos(x)"},
    {"description": "Add constant of integration.", "latex": sp.latex(integral) + " + C", "code": "integral = -sp.cos(x)"}
]
_result = integral
_result_latex = sp.latex(integral) + " + C"
