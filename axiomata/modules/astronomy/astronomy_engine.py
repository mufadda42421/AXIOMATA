"""Astronomy calculations using Astropy and analytic orbital mechanics."""
from __future__ import annotations

import math
from typing import Optional

import numpy as np

try:
    import astropy.units as u
    from astropy.constants import G as G_const, M_sun, au
    ASTROPY_AVAILABLE = True
except Exception:  # noqa: BLE001
    ASTROPY_AVAILABLE = False

# Fallback constants (SI) if Astropy import fails.
G_SI = 6.67430e-11
AU_M = 1.495978707e11
DAY_S = 86400.0
YEAR_S = 365.25 * DAY_S
M_EARTH = 5.9722e24
M_SUN = 1.98892e30


# --------------------------------------------------------------------------
# Orbital mechanics (two-body Keplerian)
# --------------------------------------------------------------------------
def orbital_period_semi_major_axis(a_m: float, m_central_kg: float,
                                   g: float = G_SI) -> float:
    """Kepler's third law: T = 2 pi sqrt(a^3 / (G M)). Returns seconds."""
    if a_m <= 0 or m_central_kg <= 0:
        raise ValueError("a and central mass must be positive")
    return 2 * math.pi * math.sqrt(a_m**3 / (g * m_central_kg))


def orbital_velocity_circular(r_m: float, m_central_kg: float, g: float = G_SI) -> float:
    """Circular orbital speed: v = sqrt(G M / r)."""
    return math.sqrt(g * m_central_kg / r_m)


def escape_velocity(r_m: float, m_central_kg: float, g: float = G_SI) -> float:
    """Escape velocity: v = sqrt(2 G M / r)."""
    return math.sqrt(2 * g * m_central_kg / r_m)


def vis_viva(r_m: float, a_m: float, m_central_kg: float, g: float = G_SI) -> float:
    """Vis-viva equation: v^2 = G M (2/r - 1/a)."""
    return math.sqrt(g * m_central_kg * (2 / r_m - 1 / a_m))


def kepler_solve_mean_anomaly(M: float, e: float, tol: float = 1e-12,
                              max_iter: int = 100) -> float:
    """Solve Kepler's equation M = E - e sin E for eccentric anomaly E (Newton)."""
    E = M if e < 0.8 else math.pi
    for _ in range(max_iter):
        f = E - e * math.sin(E) - M
        fp = 1 - e * math.cos(E)
        d = f / fp
        E -= d
        if abs(d) < tol:
            break
    return E


def orbit_position(a_m: float, e: float, true_anomaly_deg: float) -> dict:
    """Position in an elliptical orbit at a given true anomaly.

    Returns radius r and (x, y) in the orbital plane (focus at origin).
    """
    nu = math.radians(true_anomaly_deg)
    r = a_m * (1 - e**2) / (1 + e * math.cos(nu))
    x = r * math.cos(nu)
    y = r * math.sin(nu)
    return {"r": r, "x": x, "y": y, "true_anomaly_deg": true_anomaly_deg}


def orbit_sample(a_m: float, e: float, n: int = 360) -> tuple[np.ndarray, np.ndarray]:
    """Sample an ellipse (x, y) arrays for plotting."""
    nu = np.linspace(0, 2 * math.pi, n)
    r = a_m * (1 - e**2) / (1 + e * np.cos(nu))
    return r * np.cos(nu), r * np.sin(nu)


# --------------------------------------------------------------------------
# Moon phases (synodic approximation)
# --------------------------------------------------------------------------
def moon_phase_illumination(days_since_new_moon: float,
                            synodic_month: float = 29.530588853) -> dict:
    """Approximate lunar phase from days since new moon.

    Returns illumination fraction (0..1) and a phase name. This is an
    approximation assuming a circular, coplanar lunar orbit.
    """
    phase_frac = (days_since_new_moon % synodic_month) / synodic_month  # 0..1
    illum = 0.5 * (1 - math.cos(2 * math.pi * phase_frac))
    names = [
        (0.0, "New Moon"), (0.25, "First Quarter"), (0.5, "Full Moon"),
        (0.75, "Last Quarter"),
    ]
    # Determine nearest principal phase / intermediate.
    if phase_frac < 0.03 or phase_frac > 0.97:
        name = "New Moon"
    elif abs(phase_frac - 0.25) < 0.03:
        name = "First Quarter"
    elif abs(phase_frac - 0.5) < 0.03:
        name = "Full Moon"
    elif abs(phase_frac - 0.75) < 0.03:
        name = "Last Quarter"
    elif phase_frac < 0.25:
        name = "Waxing Crescent"
    elif phase_frac < 0.5:
        name = "Waxing Gibbous"
    elif phase_frac < 0.75:
        name = "Waning Gibbous"
    else:
        name = "Waning Crescent"
    return {
        "illumination": illum,
        "phase_name": name,
        "phase_fraction": phase_frac,
    }


# --------------------------------------------------------------------------
# Planetary reference data (approximate mean orbital elements)
# --------------------------------------------------------------------------
PLANETS = [
    # name, a (AU), e, radius (km), mass (kg), orbital period (days), color
    {"name": "Mercury", "a_au": 0.387, "e": 0.2056, "radius_km": 2439.7,
     "mass_kg": 3.301e23, "period_days": 87.97, "color": "#9c8f84"},
    {"name": "Venus", "a_au": 0.723, "e": 0.0068, "radius_km": 6051.8,
     "mass_kg": 4.867e24, "period_days": 224.7, "color": "#e6c98a"},
    {"name": "Earth", "a_au": 1.000, "e": 0.0167, "radius_km": 6371.0,
     "mass_kg": 5.972e24, "period_days": 365.25, "color": "#4a90d9"},
    {"name": "Mars", "a_au": 1.524, "e": 0.0934, "radius_km": 3389.5,
     "mass_kg": 6.417e23, "period_days": 686.98, "color": "#c1440e"},
    {"name": "Jupiter", "a_au": 5.203, "e": 0.0489, "radius_km": 69911,
     "mass_kg": 1.898e27, "period_days": 4332.59, "color": "#d8a47f"},
    {"name": "Saturn", "a_au": 9.537, "e": 0.0565, "radius_km": 58232,
     "mass_kg": 5.683e26, "period_days": 10759.22, "color": "#e3d9a3"},
    {"name": "Uranus", "a_au": 19.191, "e": 0.0457, "radius_km": 25362,
     "mass_kg": 8.681e25, "period_days": 30688.5, "color": "#9fe5e5"},
    {"name": "Neptune", "a_au": 30.069, "e": 0.0113, "radius_km": 24622,
     "mass_kg": 1.024e26, "period_days": 60182, "color": "#3f54ba"},
]


def planet_subsets():
    return PLANETS


def planet_period_check(planet: dict) -> float:
    """Compute orbital period from Kepler's third law and compare to tabulated."""
    a_m = planet["a_au"] * AU_M
    T = orbital_period_semi_major_axis(a_m, M_SUN)
    return T / DAY_S


def light_travel_time_from_sun(distance_au: float) -> float:
    """Light travel time from the Sun to a distance in AU, in minutes."""
    c = 299792458.0
    return (distance_au * AU_M) / c / 60.0