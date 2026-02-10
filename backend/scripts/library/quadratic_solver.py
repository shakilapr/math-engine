"""
Solver for quadratic equations of the form a*x^2 + b*x + c = 0.
"""
import sympy as sp

# Define symbols
x = sp.symbols('x')
a, b, c = sp.symbols('a b c')

# Input values (will be set by caller)
# For demonstration, use placeholders; actual values will be substituted
expr = a*x**2 + b*x + c

# Solve
solutions = sp.solve(expr, x, dict=True)

# Prepare steps
_steps = [
    {
        "description": "Write the quadratic equation in standard form.",
        "expression": f"{a} x^2 + {b} x + {c} = 0",
        "result": "",
        "latex": f"{a} x^{{2}} + {b} x + {c} = 0",
        "code": "expr = a*x**2 + b*x + c"
    },
    {
        "description": "Compute the discriminant D = b^2 - 4ac.",
        "expression": f"D = {b}^2 - 4*{a}*{c}",
        "result": f"D = {b**2 - 4*a*c}",
        "latex": f"D = b^{{2}} - 4ac = {b}^{{2}} - 4 \\cdot {a} \\cdot {c}",
        "code": "D = b**2 - 4*a*c"
    },
    {
        "description": "Apply the quadratic formula: x = (-b ± sqrt(D)) / (2a).",
        "expression": f"x = (-{b} ± sqrt(D)) / (2*{a})",
        "result": f"x = {sp.simplify((-b + sp.sqrt(b**2 - 4*a*c))/(2*a))}, {sp.simplify((-b - sp.sqrt(b**2 - 4*a*c))/(2*a))}",
        "latex": f"x = \\frac{{-b \\pm \\sqrt{{D}}}}{{2a}} = \\frac{{-{b} \\pm \\sqrt{{{b**2 - 4*a*c}}}}}{{2 \\cdot {a}}}",
        "code": "sol1 = (-b + sp.sqrt(D))/(2*a); sol2 = (-b - sp.sqrt(D))/(2*a)"
    }
]

# Final answer
_result = solutions
_result_latex = sp.latex(solutions)

# If you want numeric evaluation, you can substitute actual a,b,c later.
# This script is a template; the engine will substitute actual numeric values.