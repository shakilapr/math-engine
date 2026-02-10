
import sympy as sp
x, y = sp.symbols('x y')
eq1 = 2*x + 3*y - 5
eq2 = 4*x - y - 3
solution = sp.solve([eq1, eq2], (x, y), dict=True)
_steps = [
    {"description": "Write system of equations.", "latex": "2x + 3y = 5, \quad 4x - y = 3", "code": "eq1 = 2*x + 3*y - 5; eq2 = 4*x - y - 3"},
    {"description": "Solve using substitution or elimination.", "latex": "x = 1, y = 1", "code": "sp.solve([eq1, eq2], (x, y))"}
]
_result = solution
_result_latex = sp.latex(solution)
