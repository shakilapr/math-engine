import sympy as sp

# Define symbols
z = sp.symbols('z')
n = sp.symbols('n', integer=True)

# Initialize steps list
_steps = []

# Part (a): Laurent series expansions of f(z) = 1/((z-1)(z-2)) from z0=0
_steps.append({
    "description": "Define the function f(z)",
    "expression": "f(z) = 1/((z-1)*(z-2))",
    "result": "f(z) = 1/((z-1)*(z-2))",
    "latex": sp.latex(1/((z-1)*(z-2))),
    "code": "f = 1/((z-1)*(z-2))"
})
f = 1/((z-1)*(z-2))

# Partial fraction decomposition
_steps.append({
    "description": "Perform partial fraction decomposition",
    "expression": "f(z) = A/(z-1) + B/(z-2)",
    "result": "f(z) = 1/(1-z) - 1/(2-z)",
    "latex": r"\frac{1}{1-z} - \frac{1}{2-z}",
    "code": "A, B = sp.symbols('A B'); eqs = [sp.Eq(A+B, 0), sp.Eq(2*A+B, -1)]; sol = sp.solve(eqs, (A, B)); f_partial = sol[A]/(z-1) + sol[B]/(z-2)"
})
# Actually compute the decomposition
A, B = sp.symbols('A B')
eq1 = sp.Eq(A + B, 0)  # coefficient of z
eq2 = sp.Eq(2*A + B, -1)  # constant term
sol = sp.solve([eq1, eq2], (A, B))
f_partial = sol[A]/(z-1) + sol[B]/(z-2)
# Simplify to more convenient form
f_partial = -1/(z-1) + 1/(z-2)  # From solving: A = -1, B = 1
# Rewrite as:
f_partial = 1/(1-z) - 1/(2-z)

# Domain i: |z| < 1
_steps.append({
    "description": "For |z| < 1: expand both terms as geometric series",
    "expression": "1/(1-z) = sum_{n=0}^{∞} z^n, 1/(2-z) = 1/2 * 1/(1 - z/2) = 1/2 * sum_{n=0}^{∞} (z/2)^n",
    "result": "f(z) = sum_{n=0}^{∞} z^n - sum_{n=0}^{∞} z^n/2^{n+1}",
    "latex": r"\sum_{n=0}^{\infty} z^n - \sum_{n=0}^{\infty} \frac{z^n}{2^{n+1}}",
    "code": "series1 = sp.summation(z**n, (n, 0, sp.oo)); series2 = sp.summation(z**n/2**(n+1), (n, 0, sp.oo))"
})
# Compute series for |z| < 1
series1_i = sp.summation(z**n, (n, 0, sp.oo))
series2_i = sp.summation(z**n/2**(n+1), (n, 0, sp.oo))
series_i = series1_i - series2_i
# Simplify the combined series
series_i_simplified = sp.summation((1 - 1/2**(n+1))*z**n, (n, 0, sp.oo))

_steps.append({
    "description": "Combine series for |z| < 1",
    "expression": "f(z) = sum_{n=0}^{∞} (1 - 1/2^{n+1}) z^n",
    "result": str(series_i_simplified),
    "latex": sp.latex(series_i_simplified),
    "code": "series_i_simplified = sp.summation((1 - 1/2**(n+1))*z**n, (n, 0, sp.oo))"
})

# Domain ii: 1 < |z| < 2
_steps.append({
    "description": "For 1 < |z| < 2: rewrite 1/(1-z) as -1/z * 1/(1 - 1/z)",
    "expression": "1/(1-z) = -1/z * sum_{n=0}^{∞} (1/z)^n = -sum_{n=0}^{∞} z^{-n-1}",
    "result": "1/(1-z) = -sum_{n=0}^{∞} z^{-n-1}",
    "latex": r"-\sum_{n=0}^{\infty} z^{-n-1}",
    "code": "series1_ii = -sp.summation(z**(-n-1), (n, 0, sp.oo))"
})
# For 1/(2-z): still expand as geometric series in z/2 since |z| < 2
_steps.append({
    "description": "For 1/(2-z) with |z| < 2: 1/(2-z) = 1/2 * sum_{n=0}^{∞} (z/2)^n",
    "expression": "1/(2-z) = sum_{n=0}^{∞} z^n/2^{n+1}",
    "result": "1/(2-z) = sum_{n=0}^{∞} z^n/2^{n+1}",
    "latex": r"\sum_{n=0}^{\infty} \frac{z^n}{2^{n+1}}",
    "code": "series2_ii = sp.summation(z**n/2**(n+1), (n, 0, sp.oo))"
})
series1_ii = -sp.summation(z**(-n-1), (n, 0, sp.oo))
series2_ii = sp.summation(z**n/2**(n+1), (n, 0, sp.oo))
series_ii = series1_ii + series2_ii

_steps.append({
    "description": "Combine series for 1 < |z| < 2",
    "expression": "f(z) = -sum_{n=0}^{∞} z^{-n-1} + sum_{n=0}^{∞} z^n/2^{n+1}",
    "result": str(series_ii),
    "latex": sp.latex(series_ii),
    "code": "series_ii = series1_ii + series2_ii"
})

# Domain iii: |z| > 2
_steps.append({
    "description": "For |z| > 2: rewrite both terms using 1/z expansion",
    "expression": "1/(1-z) = -1/z * sum_{n=0}^{∞} (1/z)^n = -sum_{n=0}^{∞} z^{-n-1}",
    "result": "1/(1-z) = -sum_{n=0}^{∞} z^{-n-1}",
    "latex": r"-\sum_{n=0}^{\infty} z^{-n-1}",
    "code": "series1_iii = -sp.summation(z**(-n-1), (n, 0, sp.oo))"
})
_steps.append({
    "description": "For 1/(2-z) with |z| > 2: 1/(2-z) = -1/z * 1/(1 - 2/z) = -1/z * sum_{n=0}^{∞} (2/z)^n",
    "expression": "1/(2-z) = -sum_{n=0}^{∞} 2^n z^{-n-1}",
    "result": "1/(2-z) = -sum_{n=0}^{∞} 2^n z^{-n-1}",
    "latex": r"-\sum_{n=0}^{\infty} 2^n z^{-n-1}",
    "code": "series2_iii = -sp.summation(2**n * z**(-n-1), (n, 0, sp.oo))"
})
series1_iii = -sp.summation(z**(-n-1), (n, 0, sp.oo))
series2_iii = -sp.summation(2**n * z**(-n-1), (n, 0, sp.oo))
series_iii = series1_iii - series2_iii  # Note: f = 1/(1-z) - 1/(2-z)

_steps.append({
    "description": "Combine series for |z| > 2",
    "expression": "f(z) = -sum_{n=0}^{∞} z^{-n-1} + sum_{n=0}^{∞} 2^n z^{-n-1} = sum_{n=0}^{∞} (2^n - 1) z^{-n-1}",
    "result": str(series_iii),
    "latex": sp.latex(series_iii),
    "code": "series_iii = sp.summation((2**n - 1)*z**(-n-1), (n, 0, sp.oo))"
})
# Actually compute the simplified form
series_iii_simplified = sp.summation((2**n - 1)*z**(-n-1), (n, 0, sp.oo))

# Part (c): Evaluate ∫_C dz/sin(iz) where C: |z| = 4
_steps.append({
    "description": "Define the integrand g(z) = 1/sin(iz)",
    "expression": "g(z) = 1/sin(iz)",
    "result": "g(z) = 1/sin(i*z)",
    "latex": sp.latex(1/sp.sin(sp.I*z)),
    "code": "g = 1/sp.sin(sp.I*z)"
})
g = 1/sp.sin(sp.I*z)

# Find poles inside |z| = 4
# sin(iz) = 0 when iz = kπ, k ∈ ℤ, so z = -i kπ
_steps.append({
    "description": "Find poles: sin(iz) = 0 ⇒ iz = kπ ⇒ z = -i kπ, k ∈ ℤ",
    "expression": "z_k = -i k π",
    "result": "Poles at z = -i k π for integer k",
    "latex": r"z_k = -i k \pi",
    "code": "k = sp.symbols('k', integer=True); z_k = -sp.I * k * sp.pi"
})

# Find k such that |z_k| < 4
# |z_k| = |k|π < 4 ⇒ |k| < 4/π ≈ 1.273
# So k = -1, 0, 1
# But check if sin(iz) = 0 at these points:
# At z = 0: sin(i*0) = sin(0) = 0, but is it a pole?
# lim_{z→0} 1/sin(iz) = lim_{z→0} 1/(iz) = -i/z, so it's a simple pole.
# Actually, let's compute properly:
_steps.append({
    "description": "Find poles with |z| < 4: |k|π < 4 ⇒ |k| < 4/π ≈ 1.273",
    "expression": "|k| < 4/π ≈ 1.273 ⇒ k = -1, 0, 1",
    "result": "Poles at z = iπ, 0, -iπ",
    "latex": r"z = i\pi, 0, -i\pi",
    "code": "poles = [sp.I*sp.pi, 0, -sp.I*sp.pi]"
})
poles = [sp.I*sp.pi, 0, -sp.I*sp.pi]

# Compute residues
residues = []
for pole in poles:
    # Compute residue at simple pole: Res = lim_{z→z0} (z-z0)*g(z)
    residue_expr = sp.limit((z - pole) * g, z, pole)
    residues.append(residue_expr)
    _steps.append({
        "description": f"Compute residue at z = {sp.latex(pole)}",
        "expression": f"Res(g, {sp.latex(pole)}) = lim_{sp.latex(z)}→{sp.latex(pole)} ({sp.latex(z)}-{sp.latex(pole)}) * g({sp.latex(z)})",
        "result": str(residue_expr),
        "latex": sp.latex(residue_expr),
        "code": f"residue_{pole} = sp.limit((z - {pole}) * g, z, {pole})"
    })

# Sum residues
total_residue = sum(residues)
_steps.append({
    "description": "Sum residues inside |z| = 4",
    "expression": "Sum of residues = Res(g, iπ) + Res(g, 0) + Res(g, -iπ)",
    "result": str(total_residue),
    "latex": sp.latex(total_residue),
    "code": "total_residue = sum(residues)"
})

# Apply Residue Theorem: ∫_C g(z) dz = 2πi * sum of residues
integral_value = 2*sp.pi*sp.I * total_residue
_steps.append({
    "description": "Apply Cauchy's Residue Theorem",
    "expression": "∫_C g(z) dz = 2πi * (sum of residues)",
    "result": str(integral_value),
    "latex": sp.latex(integral_value),
    "code": "integral_value = 2*sp.pi*sp.I * total_residue"
})

# Simplify the result
integral_value_simplified = sp.simplify(integral_value)
_steps.append({
    "description": "Simplify the integral value",
    "expression": "∫_C dz/sin(iz) = simplified value",
    "result": str(integral_value_simplified),
    "latex": sp.latex(integral_value_simplified),
    "code": "integral_value_simplified = sp.simplify(integral_value)"
})

# Prepare final answer
_result = {
    "part_a": {
        "domain_i": series_i_simplified,
        "domain_ii": series_ii,
        "domain_iii": series_iii_simplified
    },
    "part_c": integral_value_simplified
}

_result_latex = {
    "part_a": {
        "domain_i": sp.latex(series_i_simplified),
        "domain_ii": sp.latex(series_ii),
        "domain_iii": sp.latex(series_iii_simplified)
    },
    "part_c": sp.latex(integral_value_simplified)
}

# Set final variables as required
_result = integral_value_simplified
_result_latex = sp.latex(integral_value_simplified)