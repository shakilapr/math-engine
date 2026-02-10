import sympy as sp

# Define symbols
z = sp.symbols('z')
n = sp.symbols('n', integer=True)

# Part (a): Laurent series expansions
f = 1/((z-1)*(z-2))

# Partial fraction decomposition
A, B = sp.symbols('A B')
partial_eq = sp.Eq(1, A*(z-1) + B*(z-2))
sol = sp.solve([partial_eq.subs(z, 1), partial_eq.subs(z, 2)], (A, B))
A_val, B_val = sol[A], sol[B]
f_partial = A_val/(z-2) + B_val/(z-1)

# Simplify to standard form: 1/(z-2) - 1/(z-1)
f_partial_simplified = sp.simplify(f_partial)

_steps = []

# Step 1: Partial fraction decomposition
_steps.append({
    "description": "Perform partial fraction decomposition",
    "expression": "f(z) = \\frac{1}{(z-1)(z-2)} = \\frac{A}{z-1} + \\frac{B}{z-2}",
    "result": f"f(z) = {sp.latex(f_partial_simplified)}",
    "latex": f"f(z) = {sp.latex(f_partial_simplified)}",
    "code": f"f_partial_simplified = {sp.srepr(f_partial_simplified)}"
})

# Domain i: |z| < 1
# Both |z| < 1 and |z| < 2, so expand both as geometric series in z
term1_i = sp.series(1/(z-2), z, 0, n=5).removeO()
term2_i = sp.series(1/(z-1), z, 0, n=5).removeO()
laurent_i = sp.simplify(term1_i - term2_i)

_steps.append({
    "description": "Laurent series for |z| < 1",
    "expression": "\\frac{1}{z-2} = -\\frac{1}{2}\\sum_{n=0}^{\\infty}\\left(\\frac{z}{2}\\right)^n, \\quad \\frac{1}{z-1} = -\\sum_{n=0}^{\\infty} z^n",
    "result": f"f(z) = {sp.latex(laurent_i)} + O(z^5)",
    "latex": f"f(z) = {sp.latex(laurent_i)} + O(z^5)",
    "code": f"laurent_i = sp.series(f_partial_simplified, z, 0, n=5).removeO()"
})

# Domain ii: 1 < |z| < 2
# For 1/(z-1): |z| > 1, expand in powers of 1/z
# For 1/(z-2): |z| < 2, expand in powers of z/2
term1_ii = sp.series(1/(z-2), z, 0, n=5).removeO()
# 1/(z-1) = (1/z) * 1/(1 - 1/z) = sum_{n=0}^∞ (1/z)^{n+1} for |z| > 1
term2_ii = sp.series(1/(z-1), 1/z, 0, n=5).removeO().subs(1/z, 1/z)
laurent_ii = sp.simplify(term1_ii - term2_ii)

_steps.append({
    "description": "Laurent series for 1 < |z| < 2",
    "expression": "\\frac{1}{z-2} = -\\frac{1}{2}\\sum_{n=0}^{\\infty}\\left(\\frac{z}{2}\\right)^n, \\quad \\frac{1}{z-1} = \\frac{1}{z}\\sum_{n=0}^{\\infty}\\left(\\frac{1}{z}\\right)^n",
    "result": f"f(z) = {sp.latex(laurent_ii)} + O(z^5, (1/z)^5)",
    "latex": f"f(z) = {sp.latex(laurent_ii)} + O(z^5, (1/z)^5)",
    "code": "term1_ii = sp.series(1/(z-2), z, 0, n=5).removeO(); term2_ii = sp.series(1/(z-1), 1/z, 0, n=5).removeO().subs(1/z, 1/z); laurent_ii = sp.simplify(term1_ii - term2_ii)"
})

# Domain iii: |z| > 2
# Both |z| > 1 and |z| > 2, expand both in powers of 1/z
term1_iii = sp.series(1/(z-2), 1/z, 0, n=5).removeO().subs(1/z, 1/z)
term2_iii = sp.series(1/(z-1), 1/z, 0, n=5).removeO().subs(1/z, 1/z)
laurent_iii = sp.simplify(term1_iii - term2_iii)

_steps.append({
    "description": "Laurent series for |z| > 2",
    "expression": "\\frac{1}{z-2} = \\frac{1}{z}\\sum_{n=0}^{\\infty}\\left(\\frac{2}{z}\\right)^n, \\quad \\frac{1}{z-1} = \\frac{1}{z}\\sum_{n=0}^{\\infty}\\left(\\frac{1}{z}\\right)^n",
    "result": f"f(z) = {sp.latex(laurent_iii)} + O((1/z)^5)",
    "latex": f"f(z) = {sp.latex(laurent_iii)} + O((1/z)^5)",
    "code": "term1_iii = sp.series(1/(z-2), 1/z, 0, n=5).removeO().subs(1/z, 1/z); term2_iii = sp.series(1/(z-1), 1/z, 0, n=5).removeO().subs(1/z, 1/z); laurent_iii = sp.simplify(term1_iii - term2_iii)"
})

# Part (b): Contour integral
# Define function g(z) = 1/sin(i*z)
g = 1/sp.sin(sp.I*z)

# Find poles inside |z| = 4: sin(i*z) = 0 => i*z = n*pi => z = -i*n*pi
# We need |z| < 4 => |-i*n*pi| = |n|*pi < 4 => |n| < 4/pi ≈ 1.273
# So n = -1, 0, 1. But n=0 gives z=0, check if sin(i*0)=0? Yes, but derivative cos(i*0)=1≠0, so simple pole.
# However, careful: sin(i*z) = i*sinh(z)? Actually sin(i*z)=i*sinh(z). But poles are at i*z = n*pi => z = -i*n*pi.
# For |z|=4, we need |n| < 4/pi ≈ 1.273, so n = -1, 0, 1.
# But let's compute explicitly.

# Solve sin(i*z) = 0
pole_eq = sp.Eq(sp.sin(sp.I*z), 0)
# sin(i*z) = i*sinh(z), so zeros at z = n*pi*i? Wait: i*sinh(z)=0 => sinh(z)=0 => z = n*pi*i? Actually sinh(z)=0 => z = n*pi*i.
# But sin(i*z) = i*sinh(z), so zeros of sin(i*z) are zeros of sinh(z) => z = n*pi*i.
# But earlier we had i*z = n*pi => z = -i*n*pi. These are same: n*pi*i = -i*n*pi? Actually n*pi*i = i*n*pi, and -i*n*pi = -i*n*pi.
# Sign difference due to n being integer. So poles at z = n*pi*i for integer n.
# |z| = |n|*pi < 4 => |n| < 4/pi ≈ 1.273 => n = -1, 0, 1.

# Compute residues at these poles
# For simple pole at z0, residue = 1/(d/dz sin(i*z)) evaluated at z0
# d/dz sin(i*z) = i*cos(i*z)
# So residue = 1/(i*cos(i*z0))
# At z0 = n*pi*i: cos(i*z0) = cos(i*n*pi*i) = cos(-n*pi) = cos(n*pi) = (-1)^n
# So residue = 1/(i*(-1)^n) = (-1)^n / i = (-1)^n * (-i) = -i*(-1)^n? Actually 1/i = -i.
# So residue = (-1)^n * (-i) = -i*(-1)^n.

# Sum residues for n = -1, 0, 1
residues_sum = 0
poles_inside = []
for n_val in [-1, 0, 1]:
    z0 = n_val*sp.pi*sp.I
    # Compute residue using formula
    residue = 1/sp.diff(sp.sin(sp.I*z), z).subs(z, z0)
    residues_sum += residue
    poles_inside.append(z0)

_steps.append({
    "description": "Find poles of 1/sin(i*z) inside |z|=4",
    "expression": "\\sin(i z) = 0 \\Rightarrow i z = n\\pi \\Rightarrow z = -i n\\pi",
    "result": f"Poles inside |z|=4: {[sp.latex(p) for p in poles_inside]}",
    "latex": f"z = {sp.latex(poles_inside)}",
    "code": f"poles_inside = [n_val*sp.pi*sp.I for n_val in [-1, 0, 1]]"
})

_steps.append({
    "description": "Compute residues at poles",
    "expression": "\\operatorname{Res}\\left(\\frac{1}{\\sin(i z)}, z_0\\right) = \\frac{1}{\\frac{d}{dz}\\sin(i z)\\big|_{z=z_0}} = \\frac{1}{i\\cos(i z_0)}",
    "result": f"Residues: {[sp.latex(1/sp.diff(sp.sin(sp.I*z), z).subs(z, p)) for p in poles_inside]}",
    "latex": f"\\operatorname{{Res}} = {[sp.latex(1/sp.diff(sp.sin(sp.I*z), z).subs(z, p)) for p in poles_inside]}",
    "code": "residues = [1/sp.diff(sp.sin(sp.I*z), z).subs(z, p) for p in poles_inside]"
})

_steps.append({
    "description": "Sum of residues",
    "expression": "\\sum \\operatorname{Res}",
    "result": f"{sp.latex(residues_sum)}",
    "latex": f"\\sum \\operatorname{{Res}} = {sp.latex(residues_sum)}",
    "code": f"residues_sum = sp.simplify(sum([1/sp.diff(sp.sin(sp.I*z), z).subs(z, p) for p in poles_inside]))"
})

# Integral = 2πi * sum of residues
integral_value = 2*sp.pi*sp.I * residues_sum
integral_value_simplified = sp.simplify(integral_value)

_steps.append({
    "description": "Apply Cauchy's Residue Theorem",
    "expression": "\\int_C \\frac{dz}{\\sin(i z)} = 2\\pi i \\sum \\operatorname{Res}",
    "result": f"{sp.latex(integral_value_simplified)}",
    "latex": f"\\int_C \\frac{{dz}}{{\\sin(i z)}} = {sp.latex(integral_value_simplified)}",
    "code": f"integral_value_simplified = sp.simplify(2*sp.pi*sp.I * residues_sum)"
})

# Final answer
_result = {
    "part_a": {
        "domain_i": laurent_i,
        "domain_ii": laurent_ii,
        "domain_iii": laurent_iii
    },
    "part_b": integral_value_simplified
}

_result_latex = {
    "part_a": {
        "domain_i": sp.latex(laurent_i) + " + O(z^5)",
        "domain_ii": sp.latex(laurent_ii) + " + O(z^5, (1/z)^5)",
        "domain_iii": sp.latex(laurent_iii) + " + O((1/z)^5)"
    },
    "part_b": sp.latex(integral_value_simplified)
}