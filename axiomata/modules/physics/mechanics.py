"""Classical mechanics calculations.

All functions use SI units (metres, kilograms, seconds, radians) and document
the governing equations. Functions return plain floats or numpy arrays and never
mutate their inputs.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np

G = 9.80665  # standard gravity, m/s^2


# --------------------------------------------------------------------------
# Kinematics & Newton's laws
# --------------------------------------------------------------------------
def uniformly_accelerated(
    s0: float, v0: float, a: float, t: np.ndarray
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Constant-acceleration kinematics.

    Equations:
        v(t) = v0 + a t
        s(t) = s0 + v0 t + 1/2 a t^2
    Returns (s, v, t).
    """
    t = np.asarray(t, dtype=float)
    v = v0 + a * t
    s = s0 + v0 * t + 0.5 * a * t**2
    return s, v, t


def projectile_motion(
    v0: float, angle_deg: float, h0: float = 0.0, g: float = G
) -> dict[str, float]:
    """Ideal projectile motion (no air resistance).

    Equations:
        vx = v0 cos(theta), vy0 = v0 sin(theta)
        x(t) = vx t
        y(t) = h0 + vy0 t - 1/2 g t^2

    Returns range, max height, and flight time.
    """
    theta = math.radians(angle_deg)
    vx = v0 * math.cos(theta)
    vy0 = v0 * math.sin(theta)
    # Flight time: solve y(t)=0 with quadratic formula.
    # 1/2 g t^2 - vy0 t - h0 = 0  -> t = (vy0 + sqrt(vy0^2 + 2 g h0)) / g
    disc = vy0**2 + 2 * g * h0
    t_flight = (vy0 + math.sqrt(disc)) / g
    rng = vx * t_flight
    h_max = h0 + (vy0**2) / (2 * g) if vy0 > 0 else h0
    return {
        "range": rng,
        "max_height": h_max,
        "flight_time": t_flight,
        "vx": vx,
        "vy0": vy0,
    }


def projectile_trajectory(
    v0: float, angle_deg: float, h0: float = 0.0, g: float = G, n: int = 200
) -> tuple[np.ndarray, np.ndarray]:
    """Return (x, y) trajectory arrays for plotting."""
    theta = math.radians(angle_deg)
    vx = v0 * math.cos(theta)
    vy0 = v0 * math.sin(theta)
    disc = vy0**2 + 2 * g * h0
    t_flight = (vy0 + math.sqrt(disc)) / g
    t = np.linspace(0, t_flight, n)
    x = vx * t
    y = h0 + vy0 * t - 0.5 * g * t**2
    return x, y


def pendulum_period(length: float, g: float = G, amplitude_deg: float = 0.0) -> float:
    """Simple pendulum period.

    Small-angle: T = 2 pi sqrt(L/g).
    For finite amplitude, a series correction is applied:
        T ~= T0 (1 + (1/16) theta0^2 + (11/3072) theta0^4 + ...)

    Amplitude must be < 90 degrees for the series to be meaningful.
    """
    T0 = 2 * math.pi * math.sqrt(length / g)
    theta0 = math.radians(amplitude_deg)
    correction = 1 + (1 / 16) * theta0**2 + (11 / 3072) * theta0**4
    return T0 * correction


def pendulum_trajectory(
    length: float,
    theta0_deg: float,
    g: float = G,
    duration: float = 10.0,
    steps: int = 500,
) -> tuple[np.ndarray, np.ndarray]:
    """Integrate the *full* nonlinear pendulum ODE.

    Equation: theta'' + (g/L) sin(theta) = 0
    Integrated with scipy's high-accuracy solver; small-angle period is not
    assumed, so large-amplitude behaviour is captured correctly.
    """
    from scipy.integrate import solve_ivp

    theta0 = math.radians(theta0_deg)
    omega0 = 0.0

    def deriv(t, y):
        return [y[1], -(g / length) * math.sin(y[0])]

    t = np.linspace(0, duration, steps)
    sol = solve_ivp(
        deriv,
        (0, duration),
        [theta0, omega0],
        t_eval=t,
        rtol=1e-9,
        atol=1e-12,
        max_step=0.01,
    )
    return sol.t, sol.y[0]


def momentum_collision_1d(
    m1: float, v1: float, m2: float, v2: float, restitution: float = 1.0
) -> tuple[float, float]:
    """1D collision with coefficient of restitution e.

    e = 1 -> perfectly elastic; e = 0 -> perfectly inelastic.
    Equations (conservation of momentum + restitution):
        v1' = (m1 v1 + m2 v2 - m2 e (v1 - v2)) / (m1 + m2)
        v2' = (m1 v1 + m2 v2 + m1 e (v1 - v2)) / (m1 + m2)
    Returns (v1', v2').
    """
    total_p = m1 * v1 + m2 * v2
    v1f = (total_p - m2 * restitution * (v1 - v2)) / (m1 + m2)
    v2f = (total_p + m1 * restitution * (v1 - v2)) / (m1 + m2)
    return v1f, v2f


def friction_force(mass: float, mu: float, g: float = G, theta_deg: float = 0.0) -> dict:
    """Friction on an inclined plane.

    Equations:
        N = m g cos(theta)
        friction_max = mu N
    Returns normal force and maximum static friction.
    """
    theta = math.radians(theta_deg)
    normal = mass * g * math.cos(theta)
    return {"normal_force": normal, "max_friction": mu * normal}


# --------------------------------------------------------------------------
# Gravitation (Newtonian)
# --------------------------------------------------------------------------
def gravitational_force(m1: float, m2: float, r: float, g_const: float = 6.67430e-11) -> float:
    """Newton's law of universal gravitation: F = G m1 m2 / r^2."""
    if r == 0:
        raise ValueError("distance must be non-zero")
    return g_const * m1 * m2 / r**2