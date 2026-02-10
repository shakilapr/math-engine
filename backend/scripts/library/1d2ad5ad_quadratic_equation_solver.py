
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
        "latex": f"x = \frac{{-b \pm \sqrt{{D}}}}{{2a}}",
        "code": "sol1 = (-b + sp.sqrt(D))/(2*a); sol2 = (-b - sp.sqrt(D))/(2*a)"
    }
]
_result = solutions
_result_latex = sp.latex(solutions)
