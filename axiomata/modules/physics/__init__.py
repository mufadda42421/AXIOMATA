"""Physics department: classical mechanics, thermodynamics, E&M, optics.

All calculations are real, SI-unit, and unit-tested. This package exposes a
registry of simulation modules consumed by the Physics Lab UI.
"""
from . import electromagnetism, mechanics, optics, thermodynamics

MODULES = {
    "mechanics": mechanics,
    "thermodynamics": thermodynamics,
    "electromagnetism": electromagnetism,
    "optics": optics,
}

__all__ = ["MODULES", "mechanics", "thermodynamics", "electromagnetism", "optics"]