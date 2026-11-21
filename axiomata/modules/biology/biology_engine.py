"""Biology models: genetics, population growth, ecosystems."""
from __future__ import annotations

import math
from typing import Optional

import numpy as np


# --------------------------------------------------------------------------
# Mendelian genetics
# --------------------------------------------------------------------------
def mendelian_cross(parent1: str, parent2: str) -> dict:
    """Punnett square for a single biallelic gene.

    Each parent is a 2-letter genotype like "Aa". Returns genotype counts,
    phenotype ratios (assuming A dominant over a), and the Punnett grid.
    """
    if len(parent1) != 2 or len(parent2) != 2:
        raise ValueError("Genotypes must be two letters, e.g. 'Aa'")
    p1 = [parent1[0], parent1[1]]
    p2 = [parent2[0], parent2[1]]
    grid = [[a + b for b in p2] for a in p1]
    counts: dict[str, int] = {}
    for row in grid:
        for cell in row:
            key = "".join(sorted(cell))
            counts[key] = counts.get(key, 0) + 1
    # Phenotypes: dominant if at least one uppercase allele.
    dominant = sum(v for k, v in counts.items() if any(c.isupper() for c in k))
    recessive = sum(v for k, v in counts.items() if k.islower())
    return {
        "grid": grid,
        "genotypes": counts,
        "dominant_phenotype": dominant,
        "recessive_phenotype": recessive,
        "total": 4,
    }


# --------------------------------------------------------------------------
# Population growth
# --------------------------------------------------------------------------
def exponential_growth(n0: float, r: float, t: np.ndarray) -> np.ndarray:
    """Unlimited exponential growth: N(t) = N0 e^(r t)."""
    return n0 * np.exp(r * np.asarray(t, dtype=float))


def logistic_growth(n0: float, r: float, k: float, t: np.ndarray) -> np.ndarray:
    """Logistic growth: N(t) = K / (1 + ((K-N0)/N0) e^(-r t))."""
    t = np.asarray(t, dtype=float)
    a = (k - n0) / n0
    return k / (1 + a * np.exp(-r * t))


def lotka_volterra_prey_predator(
    prey0: float, pred0: float, alpha: float, beta: float, delta: float, gamma: float,
    duration: float = 50.0, steps: int = 1000,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Lotka-Volterra predator-prey model.

    dx/dt = alpha x - beta x y        (prey)
    dy/dt = delta x y - gamma y       (predator)

    Integrated with scipy RK45. Returns (t, prey, predator).
    """
    from scipy.integrate import solve_ivp

    def deriv(t, state):
        x, y = state
        dx = alpha * x - beta * x * y
        dy = delta * x * y - gamma * y
        return [dx, dy]

    t = np.linspace(0, duration, steps)
    sol = solve_ivp(deriv, (0, duration), [prey0, pred0], t_eval=t, max_step=0.05)
    return sol.t, sol.y[0], sol.y[1]


# --------------------------------------------------------------------------
# Natural selection / allele frequency (Hardy-Weinberg)
# --------------------------------------------------------------------------
def hardy_weinberg(p: float) -> dict:
    """Hardy-Weinberg genotype frequencies from allele frequency p.

    q = 1 - p
    f(AA) = p^2, f(Aa) = 2pq, f(aa) = q^2
    """
    if not (0.0 <= p <= 1.0):
        raise ValueError("allele frequency p must be in [0, 1]")
    q = 1.0 - p
    return {
        "p": p,
        "q": q,
        "AA": p**2,
        "Aa": 2 * p * q,
        "aa": q**2,
    }


def selection_change(p: float, w_AA: float, w_Aa: float, w_aa: float) -> dict:
    """One generation of viability selection on a biallelic locus.

    w_* are relative fitnesses (0..1). Returns new allele frequency p'.
    """
    q = 1 - p
    mean_w = p**2 * w_AA + 2 * p * q * w_Aa + q**2 * w_aa
    if mean_w == 0:
        raise ValueError("Mean fitness is zero; cannot compute selection.")
    p_next = (p**2 * w_AA + p * q * w_Aa) / mean_w
    return {"p": p, "p_next": p_next, "mean_fitness": mean_w, "q": q}


def iterate_selection(p0: float, w_AA: float, w_Aa: float, w_aa: float,
                      generations: int) -> tuple[np.ndarray, np.ndarray]:
    """Iterate viability selection for N generations. Returns (gens, p)."""
    p = p0
    gens = np.arange(generations + 1)
    ps = [p]
    for _ in range(generations):
        p = selection_change(p, w_AA, w_Aa, w_aa)["p_next"]
        ps.append(p)
    return gens, np.array(ps)