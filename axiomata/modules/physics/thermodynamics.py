"""Thermodynamics calculations (ideal gases, heat, thermal expansion)."""
from __future__ import annotations

import math

R = 8.314462618  # universal gas constant, J/(mol K)


def ideal_gas_law(
    p: float | None = None,
    v: float | None = None,
    n: float | None = None,
    t: float | None = None,
) -> dict:
    """Solve the ideal gas law PV = nRT for the missing variable.

    Provide exactly three of the four values (p, v, n, t); the fourth is
    returned. Pressure in Pa, volume in m^3, amount in mol, temperature in K.
    """
    provided = {k: val for k, val in (("p", p), ("v", v), ("n", n), ("t", t)) if val is not None}
    if len(provided) != 3:
        raise ValueError("Provide exactly three of p, v, n, t")
    if p is None:
        p = n * R * t / v
    elif v is None:
        v = n * R * t / p
    elif n is None:
        n = p * v / (R * t)
    else:  # t is None
        t = p * v / (n * R)
    return {"p": p, "v": v, "n": n, "t": t}


def sensible_heat(mass: float, specific_heat: float, delta_t: float) -> float:
    """Q = m c deltaT (no phase change)."""
    return mass * specific_heat * delta_t


def latent_heat(mass: float, latent_heat_coeff: float) -> float:
    """Q = m L (phase change at constant temperature)."""
    return mass * latent_heat_coeff


def thermal_expansion_linear(
    length0: float, alpha: float, delta_t: float
) -> dict:
    """Linear thermal expansion.

    Equation: deltaL = alpha L0 deltaT
    Returns new length and change.
    """
    delta_l = alpha * length0 * delta_t
    return {"delta_length": delta_l, "new_length": length0 + delta_l}


def thermal_expansion_volumetric(
    volume0: float, beta: float, delta_t: float
) -> dict:
    """Volumetric expansion: deltaV = beta V0 deltaT (beta ~= 3 alpha)."""
    delta_v = beta * volume0 * delta_t
    return {"delta_volume": delta_v, "new_volume": volume0 + delta_v}


def heat_transfer_conduction(
    area: float,
    thermal_conductivity: float,
    delta_t: float,
    thickness: float,
) -> float:
    """Fourier's law of conduction.

    Q/t = k A deltaT / d  (rate of heat flow in watts).
    """
    if thickness <= 0:
        raise ValueError("thickness must be positive")
    return thermal_conductivity * area * delta_t / thickness


def stefan_boltzmann_radiation(
    emissivity: float, area: float, temp_k: float, surroundings_k: float = 0.0
) -> float:
    """Net radiated power via Stefan-Boltzmann.

    P = e sigma A (T^4 - T_surr^4), sigma = 5.670374e-8 W/m^2/K^4.
    """
    sigma = 5.670374419e-8
    return emissivity * sigma * area * (temp_k**4 - surroundings_k**4)