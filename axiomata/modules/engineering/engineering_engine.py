"""Engineering calculations: mechanics, electrical, civil (structural)."""
from __future__ import annotations

import math
import numpy as np


# --------------------------------------------------------------------------
# Mechanical
# --------------------------------------------------------------------------
def rotational_dynamics(torque: float, moment_of_inertia: float, time: float) -> dict:
    """Rotational motion from rest under constant torque.

    alpha = tau / I
    omega(t) = alpha t
    theta(t) = 0.5 alpha t^2
    """
    if moment_of_inertia <= 0:
        raise ValueError("moment of inertia must be positive")
    alpha = torque / moment_of_inertia
    omega = alpha * time
    theta = 0.5 * alpha * time**2
    return {"alpha": alpha, "omega": omega, "theta": theta}


def lever_balancing(force1: float, distance1: float, force2: float) -> dict:
    """Balance a lever: find distance2 so that F1 d1 = F2 d2."""
    if force2 == 0:
        raise ValueError("force2 must be non-zero")
    distance2 = force1 * distance1 / force2
    return {"distance2": distance2, "torque1": force1 * distance1}


def spring_period(mass: float, k: float) -> dict:
    """Mass-spring period: T = 2 pi sqrt(m/k)."""
    if k <= 0:
        raise ValueError("spring constant must be positive")
    omega = math.sqrt(k / mass)
    return {"omega": omega, "period": 2 * math.pi / omega,
            "frequency": omega / (2 * math.pi)}


def simple_harmonic_oscillator(mass: float, k: float, amplitude: float,
                               duration: float = 10.0, steps: int = 500
                               ) -> tuple[np.ndarray, np.ndarray]:
    """Sample x(t) = A cos(omega t) for a mass-spring system."""
    omega = math.sqrt(k / mass)
    t = np.linspace(0, duration, steps)
    return t, amplitude * np.cos(omega * t)


# --------------------------------------------------------------------------
# Electrical
# --------------------------------------------------------------------------
def ohms_law(voltage: float | None = None, current: float | None = None,
             resistance: float | None = None) -> dict:
    provided = sum(x is not None for x in (voltage, current, resistance))
    if provided != 2:
        raise ValueError("Provide exactly two of voltage, current, resistance")
    if voltage is None:
        voltage = current * resistance
    elif current is None:
        current = voltage / resistance
    else:
        resistance = voltage / current
    return {"voltage": voltage, "current": current, "resistance": resistance}


def series_resistance(*r: float) -> float:
    return float(sum(r))


def parallel_resistance(*r: float) -> float:
    if any(x <= 0 for x in r):
        raise ValueError("resistances must be positive")
    return 1.0 / sum(1.0 / x for x in r)


def voltage_divider(v_in: float, r1: float, r2: float) -> dict:
    """Output voltage across r2 in a two-resistor divider."""
    if (r1 + r2) == 0:
        raise ValueError("total resistance must be non-zero")
    v_out = v_in * r2 / (r1 + r2)
    return {"v_out": v_out, "total_r": r1 + r2,
            "current": v_in / (r1 + r2)}


def power_dissipation(voltage: float, resistance: float) -> float:
    """P = V^2 / R."""
    if resistance <= 0:
        raise ValueError("resistance must be positive")
    return voltage**2 / resistance


# --------------------------------------------------------------------------
# Civil / structural (simplified beam theory)
# --------------------------------------------------------------------------
def simply_supported_beam_point_load(
    length: float, load: float, position: float,
    youngs_modulus: float, moment_of_inertia: float,
) -> dict:
    """Simply supported beam, single point load at distance a from left.

    Returns max deflection, reactions, and max bending moment.
    Deflection at load point (Euler-Bernoulli):
        delta = P a^2 b^2 / (3 E I L), where b = L - a
    """
    if length <= 0 or youngs_modulus <= 0 or moment_of_inertia <= 0:
        raise ValueError("length, E, I must be positive")
    if not (0 <= position <= length):
        raise ValueError("load position must be within the beam")
    a = position
    b = length - a
    P = load
    L = length
    E = youngs_modulus
    I = moment_of_inertia
    R_left = P * b / L
    R_right = P * a / L
    max_moment = P * a * b / L  # under the load
    max_deflection = P * a**2 * b**2 / (3 * E * I * L)
    return {
        "reaction_left": R_left,
        "reaction_right": R_right,
        "max_bending_moment": max_moment,
        "max_deflection": max_deflection,
        "deflection_sign": "downward",
    }


def beam_deflection_curve(
    length: float, load: float, position: float,
    youngs_modulus: float, moment_of_inertia: float, n: int = 200,
) -> tuple[np.ndarray, np.ndarray]:
    """Euler-Bernoulli deflection curve for a simply supported beam.

    Solves EI y'' = M(x) by numeric integration with boundary conditions
    y(0) = 0 and y(L) = 0 (shooting method). Returns (x, y) arrays.
    """
    return _beam_deflection_numeric(length, load, position, youngs_modulus,
                                    moment_of_inertia, n)


def _beam_deflection_numeric(length: float, load: float, position: float,
                             youngs_modulus: float, moment_of_inertia: float,
                             n: int = 200) -> tuple[np.ndarray, np.ndarray]:
    """Robust numeric deflection via direct integration of moment curvature."""
    from scipy.integrate import solve_ivp

    a = position
    b = length - a
    P = load
    L = length
    E = youngs_modulus
    I = moment_of_inertia

    def moment(x):
        # Reactions R_left = P b / L; moment = R_left x for x<a,
        # and R_left x - P (x-a) for x>=a.
        R_left = P * b / L
        if x <= a:
            return R_left * x
        return R_left * x - P * (x - a)

    # Solve EI y'' = M(x) with boundary y(0)=0 and y(L)=0.
    # Convert to system: y' = theta, theta' = M/EI.
    def deriv(x, state):
        y, theta = state
        return [theta, moment(x) / (E * I)]

    # We need a shooting method: y(0)=0, guess theta0, require y(L)=0.
    from scipy.optimize import brentq

    def shoot(theta0):
        sol = solve_ivp(deriv, (0, L), [0.0, theta0], dense_output=True,
                        rtol=1e-8, atol=1e-10)
        return sol.y[0][-1]

    try:
        theta0 = brentq(shoot, -1e3, 1e3)
    except Exception:  # noqa: BLE001
        theta0 = 0.0
    sol = solve_ivp(deriv, (0, L), [0.0, theta0], t_eval=np.linspace(0, L, n),
                    rtol=1e-8, atol=1e-10)
    return sol.t, sol.y[0]


def stress_strain(force: float, area: float, original_length: float,
                  youngs_modulus: float) -> dict:
    """Basic stress/strain for axial loading.

    stress = F/A; strain = stress/E; elongation = strain * L
    """
    if area <= 0 or youngs_modulus <= 0:
        raise ValueError("area and Young's modulus must be positive")
    stress = force / area
    strain = stress / youngs_modulus
    return {
        "stress": stress,
        "strain": strain,
        "elongation": strain * original_length,
    }