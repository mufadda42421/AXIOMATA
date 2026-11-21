"""Electricity & magnetism calculations."""
from __future__ import annotations

import math

COULOMB_K = 8.9875517923e9  # N m^2 / C^2
EPSILON_0 = 8.8541878128e-12  # F/m


def coulombs_law(q1: float, q2: float, r: float) -> dict:
    """Force between two point charges.

    F = k q1 q2 / r^2. Positive result -> repulsive (same sign).
    Returns force magnitude and direction ('repulsive'|'attractive').
    """
    if r == 0:
        raise ValueError("distance must be non-zero")
    f = COULOMB_K * q1 * q2 / r**2
    direction = "repulsive" if f >= 0 else "attractive"
    return {"force": abs(f), "direction": direction}


def electric_field_point_charge(q: float, r: float) -> float:
    """E = k q / r^2 (N/C or V/m)."""
    if r == 0:
        raise ValueError("distance must be non-zero")
    return COULOMB_K * q / r**2


def ohms_law(v: float | None = None, i: float | None = None, r: float | None = None) -> dict:
    """Solve V = I R for the missing variable. Provide exactly two."""
    provided = sum(x is not None for x in (v, i, r))
    if provided != 2:
        raise ValueError("Provide exactly two of v, i, r")
    if v is None:
        v = i * r
    elif i is None:
        i = v / r
    else:
        r = v / i
    return {"v": v, "i": i, "r": r}


def resistor_series(*resistances: float) -> float:
    """Series resistance: R = sum(Ri)."""
    return float(sum(resistances))


def resistor_parallel(*resistances: float) -> float:
    """Parallel resistance: 1/R = sum(1/Ri)."""
    if any(r <= 0 for r in resistances):
        raise ValueError("resistances must be positive")
    return 1.0 / sum(1.0 / r for r in resistances)


def electric_power(v: float, i: float) -> float:
    """P = V I (watts)."""
    return v * i


def capacitor_energy(capacitance: float, voltage: float) -> float:
    """E = 1/2 C V^2 (joules)."""
    return 0.5 * capacitance * voltage**2


def capacitor_series(*capacitances: float) -> float:
    """Series capacitance: 1/C = sum(1/Ci)."""
    if any(c <= 0 for c in capacitances):
        raise ValueError("capacitances must be positive")
    return 1.0 / sum(1.0 / c for c in capacitances)


def capacitor_parallel(*capacitances: float) -> float:
    """Parallel capacitance: C = sum(Ci)."""
    return float(sum(capacitances))


def rc_charge(t: float, r: float, c: float, v0: float) -> float:
    """Charging an RC circuit: Vc(t) = V0 (1 - e^(-t/RC))."""
    tau = r * c
    return v0 * (1 - math.exp(-t / tau))


def rc_discharge(t: float, r: float, c: float, v0: float) -> float:
    """Discharging an RC circuit: Vc(t) = V0 e^(-t/RC)."""
    tau = r * c
    return v0 * math.exp(-t / tau)


def magnetic_force_wire(
    current: float, length: float, field: float, angle_deg: float = 90.0
) -> float:
    """Force on a current-carrying wire: F = B I L sin(theta)."""
    return field * current * length * math.sin(math.radians(angle_deg))


def solenoid_field(
    n_turns: float, current: float, length: float, mu0: float = 4 * math.pi * 1e-7
) -> float:
    """Ideal solenoid field: B = mu0 n I, n = N/L (turns per metre)."""
    if length <= 0:
        raise ValueError("length must be positive")
    n = n_turns / length
    return mu0 * n * current