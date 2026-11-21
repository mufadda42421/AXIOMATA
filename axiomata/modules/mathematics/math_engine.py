"""Mathematics calculations using SymPy (symbolic) and NumPy/SciPy (numeric)."""
from __future__ import annotations

from typing import Optional

import numpy as np

import sympy as sp


def _parse_expr(expr: str) -> sp.Expr:
    x = sp.Symbol("x")
    try:
        return sp.sympify(expr, locals={"x": x})
    except (sp.SympifyError, SyntaxError, TypeError) as exc:
        raise ValueError(f"Cannot parse expression: {expr!r}") from exc


def simplify(expr: str) -> str:
    return str(sp.simplify(_parse_expr(expr)))


def differentiate(expr: str, order: int = 1) -> str:
    return str(sp.diff(_parse_expr(expr), sp.Symbol("x"), order))


def integrate(expr: str, variable: Optional[str] = None,
              lower: Optional[float] = None, upper: Optional[float] = None) -> str:
    e = _parse_expr(expr)
    var = sp.Symbol(variable or "x")
    if lower is not None and upper is not None:
        return str(sp.integrate(e, (var, lower, upper)))
    return str(sp.integrate(e, var))


def solve_equation(equation: str) -> list[str]:
    """Solve an equation of the form 'lhs = rhs' or an expression '= 0'."""
    if "=" in equation:
        lhs, rhs = equation.split("=", 1)
    else:
        lhs, rhs = equation, "0"
    x = sp.Symbol("x")
    expr = sp.sympify(lhs, locals={"x": x}) - sp.sympify(rhs, locals={"x": x})
    try:
        sols = sp.solve(expr, x)
    except Exception as exc:  # noqa: BLE001
        raise ValueError(f"Could not solve: {equation!r}") from exc
    return [str(s) for s in sols]


def evaluate_numeric(expr: str, x_value: float) -> float:
    e = _parse_expr(expr)
    return float(e.subs(sp.Symbol("x"), x_value).evalf())


def matrix_operations(rows_a: list[list[float]], rows_b: Optional[list[list[float]]] = None,
                      op: str = "add") -> list[list[float]]:
    """Add, multiply, or transpose matrices (2D lists)."""
    A = sp.Matrix(rows_a)
    if op == "transpose":
        return [list(row) for row in A.T.tolist()]
    if rows_b is None:
        raise ValueError(f"op '{op}' requires a second matrix")
    B = sp.Matrix(rows_b)
    if op == "add":
        C = A + B
    elif op == "multiply":
        C = A * B
    elif op == "subtract":
        C = A - B
    else:
        raise ValueError(f"Unknown matrix operation: {op}")
    return [list(row) for row in C.tolist()]


def matrix_determinant(rows: list[list[float]]) -> float:
    return float(sp.Matrix(rows).det())


def matrix_inverse(rows: list[list[float]]) -> list[list[float]]:
    M = sp.Matrix(rows)
    if M.det() == 0:
        raise ValueError("Matrix is singular; inverse does not exist.")
    return [list(row) for row in M.inv().tolist()]


def vector_dot(a: list[float], b: list[float]) -> float:
    return float(np.dot(a, b))


def vector_cross(a: list[float], b: list[float]) -> list[float]:
    return np.cross(a, b).tolist()


def vector_norm(a: list[float]) -> float:
    return float(np.linalg.norm(a))


def complex_operations(a: complex, b: complex, op: str) -> complex:
    if op == "add":
        return a + b
    if op == "subtract":
        return a - b
    if op == "multiply":
        return a * b
    if op == "divide":
        if b == 0:
            raise ValueError("division by zero")
        return a / b
    raise ValueError(f"Unknown complex operation: {op}")


def roots_of_unity(n: int) -> list[complex]:
    """The n complex n-th roots of unity."""
    if n <= 0:
        raise ValueError("n must be positive")
    return [complex(np.exp(2j * np.pi * k / n)) for k in range(n)]


# -- Numerical methods ----------------------------------------------------
def bisection_root(func_expr: str, a: float, b: float, tol: float = 1e-10,
                   max_iter: int = 200) -> dict:
    """Find a root of func_expr (in x) on [a, b] by bisection."""
    x = sp.Symbol("x")
    f = sp.lambdify(x, _parse_expr(func_expr), "numpy")
    fa, fb = f(a), f(b)
    if fa * fb > 0:
        raise ValueError("Function must have opposite signs at a and b")
    for _ in range(max_iter):
        c = 0.5 * (a + b)
        fc = f(c)
        if abs(fc) < tol or (b - a) / 2 < tol:
            return {"root": c, "iterations": _ + 1, "converged": True}
        if fa * fc < 0:
            b, fb = c, fc
        else:
            a, fa = c, fc
    return {"root": 0.5 * (a + b), "iterations": max_iter, "converged": False}


def numerical_integral(expr: str, a: float, b: float, n: int = 1000) -> float:
    """Definite integral via Simpson's rule using scipy."""
    from scipy.integrate import simpson
    x = sp.Symbol("x")
    f = sp.lambdify(x, _parse_expr(expr), "numpy")
    xs = np.linspace(a, b, n)
    ys = f(xs)
    return float(simpson(ys, x=xs))


def plot_function_samples(expr: str, x_min: float, x_max: float, n: int = 400
                          ) -> tuple[np.ndarray, np.ndarray]:
    """Sample a function for plotting; returns (x, y) arrays (NaN-safe)."""
    x = sp.Symbol("x")
    f = sp.lambdify(x, _parse_expr(expr), "numpy")
    xs = np.linspace(x_min, x_max, n)
    with np.errstate(all="ignore"):
        ys = f(xs)
    ys = np.asarray(ys, dtype=float)
    ys[~np.isfinite(ys)] = np.nan
    return xs, ys