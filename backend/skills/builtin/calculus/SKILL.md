---
name: calculus
description: Solves calculus problems (derivatives, integrals, limits) using SymPy with step-by-step explanations.
patterns:
  - "derivative"
  - "derive"
  - "integral"
  - "integrate"
  - "limit"
  - "d/dx"
version: 1.0.0
author: System
---

# Calculus Solver

This skill handles symbolic calculus operations.

## Strategy
1. Identify the operation (differentiation, integration, limit).
2. Parse the expression into a SymPy object.
3. Apply the appropriate SymPy function (`diff`, `integrate`, `limit`).
4. Format the output as LaTeX.

## Template

```python
import sympy as sp

def solve(problem):
    """
    Solves calculus problems.
    Input: problem dictionary with 'text' and 'latex'.
    """
    x = sp.Symbol('x')
    
    # logic to parse and solve
    # ...
    return {
        "result": "...",
        "steps": []
    }
```
