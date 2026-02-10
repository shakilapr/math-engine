#!/usr/bin/env python3
"""
Populate the script library with template scripts.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from scripts.library_manager import ScriptLibrary

def main():
    lib = ScriptLibrary()
    
    # Quadratic solver
    quad_code = """
import sympy as sp
x, a, b, c = sp.symbols('x a b c')
expr = a*x**2 + b*x + c
solutions = sp.solve(expr, x, dict=True)
_steps = [
    {
        "description": "Write the quadratic equation in standard form.",
        "expression": f"{a} x^2 + {b} x + {c} = 0",
        "latex": f"{a} x^{{2}} + {b} x + {c} = 0",
        "code": "expr = a*x**2 + b*x + c"
    },
    {
        "description": "Compute discriminant D = b^2 - 4ac.",
        "expression": f"D = {b}^2 - 4*{a}*{c}",
        "latex": f"D = b^{{2}} - 4ac",
        "code": "D = b**2 - 4*a*c"
    },
    {
        "description": "Apply quadratic formula.",
        "expression": f"x = (-{b} ± sqrt(D)) / (2*{a})",
        "latex": f"x = \\frac{{-b \\pm \\sqrt{{D}}}}{{2a}}",
        "code": "sol1 = (-b + sp.sqrt(D))/(2*a); sol2 = (-b - sp.sqrt(D))/(2*a)"
    }
]
_result = solutions
_result_latex = sp.latex(solutions)
"""
    lib.add_script(
        name="Quadratic Equation Solver",
        description="Solves quadratic equations of form a*x^2 + b*x + c = 0",
        code=quad_code,
        category="algebra",
        tags=["quadratic", "polynomial", "roots"]
    )
    
    # Derivative
    deriv_code = """
import sympy as sp
x = sp.symbols('x')
expr = sp.sympify('x**3 + 2*x')
derivative = sp.diff(expr, x)
_steps = [
    {"description": "Identify function.", "latex": sp.latex(expr), "code": "expr = x**3 + 2*x"},
    {"description": "Apply power rule.", "latex": "\\frac{d}{dx} x^{3} = 3 x^{2}", "code": "sp.diff(x**3, x)"},
    {"description": "Sum derivatives.", "latex": sp.latex(derivative), "code": "derivative = 3*x**2 + 2"}
]
_result = derivative
_result_latex = sp.latex(derivative)
"""
    lib.add_script(
        name="Basic Derivative",
        description="Computes derivative of polynomial functions",
        code=deriv_code,
        category="calculus",
        tags=["derivative", "polynomial", "power rule"]
    )
    
    # Integral
    integral_code = """
import sympy as sp
x = sp.symbols('x')
expr = sp.sin(x)
integral = sp.integrate(expr, x)
_steps = [
    {"description": "Identify integrand.", "latex": sp.latex(expr), "code": "expr = sp.sin(x)"},
    {"description": "Recall antiderivative of sin(x) is -cos(x).", "latex": "\\int \\sin(x)\\,dx = -\\cos(x) + C", "code": "integral = -sp.cos(x)"},
    {"description": "Add constant of integration.", "latex": sp.latex(integral) + " + C", "code": "integral = -sp.cos(x)"}
]
_result = integral
_result_latex = sp.latex(integral) + " + C"
"""
    lib.add_script(
        name="Indefinite Integral of sin(x)",
        description="Computes ∫ sin(x) dx",
        code=integral_code,
        category="calculus",
        tags=["integral", "antiderivative", "trigonometry"]
    )
    
    # Linear system
    linear_code = """
import sympy as sp
x, y = sp.symbols('x y')
eq1 = 2*x + 3*y - 5
eq2 = 4*x - y - 3
solution = sp.solve([eq1, eq2], (x, y), dict=True)
_steps = [
    {"description": "Write system of equations.", "latex": "2x + 3y = 5, \\quad 4x - y = 3", "code": "eq1 = 2*x + 3*y - 5; eq2 = 4*x - y - 3"},
    {"description": "Solve using substitution or elimination.", "latex": "x = 1, y = 1", "code": "sp.solve([eq1, eq2], (x, y))"}
]
_result = solution
_result_latex = sp.latex(solution)
"""
    lib.add_script(
        name="Linear System Solver",
        description="Solves 2x2 linear system",
        code=linear_code,
        category="linear_algebra",
        tags=["linear", "system", "2x2"]
    )
    
    # Limit
    limit_code = """
import sympy as sp
x = sp.symbols('x')
expr = sp.sin(x)/x
limit_val = sp.limit(expr, x, 0)
_steps = [
    {"description": "Identify limit expression.", "latex": sp.latex(expr), "code": "expr = sp.sin(x)/x"},
    {"description": "Apply limit as x -> 0, using known limit sin(x)/x -> 1.", "latex": "\\lim_{x \\to 0} \\frac{\\sin(x)}{x} = 1", "code": "limit_val = sp.limit(expr, x, 0)"}
]
_result = limit_val
_result_latex = sp.latex(limit_val)
"""
    lib.add_script(
        name="Limit sin(x)/x",
        description="Evaluates limit of sin(x)/x as x -> 0",
        code=limit_code,
        category="calculus",
        tags=["limit", "trigonometric", "sinx/x"]
    )
    
    print(f"Added {len(lib.list_all())} scripts to library.")

if __name__ == "__main__":
    main()