"""Optics calculations: reflection, refraction, thin lenses."""
from __future__ import annotations

import math


def reflection_angle(incident_deg: float) -> float:
    """Law of reflection: angle of reflection equals angle of incidence."""
    return incident_deg


def snell_refraction(
    n1: float, n2: float, incident_deg: float
) -> dict:
    """Snell's law: n1 sin(theta1) = n2 sin(theta2).

    Returns refracted angle in degrees and whether total internal reflection
    occurs (valid when n1 > n2 and the angle exceeds the critical angle).
    """
    theta1 = math.radians(incident_deg)
    sin_theta2 = (n1 / n2) * math.sin(theta1)
    tir = False
    if abs(sin_theta2) > 1.0:
        tir = True
        theta2 = math.nan
    else:
        theta2 = math.degrees(math.asin(sin_theta2))
    return {"refracted_deg": theta2, "total_internal_reflection": tir}


def critical_angle(n1: float, n2: float) -> float:
    """Critical angle for total internal reflection (n1 > n2), degrees.

    theta_c = asin(n2/n1). Returns NaN if n1 <= n2 (no TIR possible).
    """
    if n1 <= n2:
        return math.nan
    return math.degrees(math.asin(n2 / n1))


def thin_lens(
    focal_length: float, object_distance: float
) -> dict:
    """Thin lens equation: 1/f = 1/do + 1/di.

    Returns image distance di and magnification m = -di/do.
    Sign convention: f>0 converging, do>0 real object.
    """
    if focal_length == 0:
        raise ValueError("focal length must be non-zero")
    image_distance = 1.0 / (1.0 / focal_length - 1.0 / object_distance)
    magnification = -image_distance / object_distance
    return {
        "image_distance": image_distance,
        "magnification": magnification,
        "image_type": "real" if image_distance > 0 else "virtual",
    }


def lens_maker(
    n_lens: float, r1: float, r2: float
) -> float:
    """Lensmaker's equation (thin lens in air).

    1/f = (n - 1)(1/R1 - 1/R2). Radii in metres, sign convention applies.
    """
    inv_f = (n_lens - 1) * (1.0 / r1 - 1.0 / r2)
    if inv_f == 0:
        return math.inf
    return 1.0 / inv_f


def wavelength_in_medium(vacuum_wavelength_nm: float, n: float) -> float:
    """lambda_medium = lambda_vacuum / n."""
    return vacuum_wavelength_nm / n


def photon_energy(wavelength_nm: float, h: float = 6.62607015e-34, c: float = 299792458.0) -> float:
    """Photon energy E = h c / lambda (joules)."""
    wavelength_m = wavelength_nm * 1e-9
    return h * c / wavelength_m