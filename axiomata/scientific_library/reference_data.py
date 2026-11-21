"""Scientific reference data: physical constants, SI units, formulas.

All values are standard, well-established scientific references. Sources are
noted per section so the UI can attribute them. Nothing here is fabricated;
constants use CODATA/SI defined values and formulas are textbook-standard.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Constant:
    name: str
    symbol: str
    value: float
    unit: str
    source: str = "CODATA / SI (2019 redefinition)"


PHYSICAL_CONSTANTS: list[Constant] = [
    Constant("Speed of light in vacuum", "c", 299792458.0, "m/s", "SI defined"),
    Constant("Planck constant", "h", 6.62607015e-34, "J·s", "SI defined"),
    Constant("Reduced Planck constant", "ħ", 1.054571817e-34, "J·s", "h / 2π"),
    Constant("Elementary charge", "e", 1.602176634e-19, "C", "SI defined"),
    Constant("Boltzmann constant", "k_B", 1.380649e-23, "J/K", "SI defined"),
    Constant("Avogadro constant", "N_A", 6.02214076e23, "1/mol", "SI defined"),
    Constant("Universal gas constant", "R", 8.314462618, "J/(mol·K)", "N_A · k_B"),
    Constant("Gravitational constant", "G", 6.67430e-11, "m³/(kg·s²)", "CODATA 2018"),
    Constant("Standard gravity", "g_n", 9.80665, "m/s²", "Conventional"),
    Constant("Vacuum permittivity", "ε₀", 8.8541878128e-12, "F/m", "CODATA 2018"),
    Constant("Vacuum permeability", "μ₀", 1.25663706212e-6, "H/m", "CODATA 2018"),
    Constant("Coulomb constant", "k_e", 8.9875517923e9, "N·m²/C²", "1/(4πε₀)"),
    Constant("Stefan-Boltzmann constant", "σ", 5.670374419e-8, "W/(m²·K⁴)", "CODATA 2018"),
    Constant("Electron mass", "m_e", 9.1093837015e-31, "kg", "CODATA 2018"),
    Constant("Proton mass", "m_p", 1.67262192369e-27, "kg", "CODATA 2018"),
    Constant("Neutron mass", "m_n", 1.67492749804e-27, "kg", "CODATA 2018"),
    Constant("Atomic mass constant", "m_u", 1.66053906660e-27, "kg", "CODATA 2018"),
    Constant("Faraday constant", "F", 96485.33212, "C/mol", "N_A · e"),
    Constant("Molar gas constant (alt)", "R", 0.082057366, "L·atm/(mol·K)", "Common chemistry value"),
    Constant("Standard atmosphere", "atm", 101325.0, "Pa", "Conventional"),
]


@dataclass
class Formula:
    name: str
    expression: str
    category: str
    description: str


FORMULAS: list[Formula] = [
    # Mechanics
    Formula("Newton's second law", "F = m a", "Mechanics",
            "Force equals mass times acceleration."),
    Formula("Kinetic energy", "KE = ½ m v²", "Mechanics",
            "Translational kinetic energy."),
    Formula("Gravitational potential energy", "U = m g h", "Mechanics",
            "Potential energy near Earth's surface."),
    Formula("Momentum", "p = m v", "Mechanics",
            "Linear momentum."),
    Formula("Kinematic (constant a)", "v = v₀ + a t ; s = v₀ t + ½ a t²", "Mechanics",
            "Constant-acceleration equations."),
    Formula("Universal gravitation", "F = G m₁ m₂ / r²", "Mechanics",
            "Newton's law of universal gravitation."),
    Formula("Pendulum period (small angle)", "T = 2π √(L/g)", "Mechanics",
            "Simple pendulum, small amplitude."),
    Formula("Centripetal force", "F = m v² / r", "Mechanics",
            "Force for circular motion."),
    # Thermodynamics
    Formula("Ideal gas law", "P V = n R T", "Thermodynamics",
            "Equation of state for an ideal gas."),
    Formula("Sensible heat", "Q = m c ΔT", "Thermodynamics",
            "Heat to change temperature (no phase change)."),
    Formula("Latent heat", "Q = m L", "Thermodynamics",
            "Heat for phase change at constant temperature."),
    Formula("First law of thermodynamics", "ΔU = Q − W", "Thermodynamics",
            "Energy conservation for thermodynamic systems."),
    Formula("Thermal expansion (linear)", "ΔL = α L₀ ΔT", "Thermodynamics",
            "Linear expansion with temperature."),
    Formula("Heat conduction (Fourier)", "Q/t = k A ΔT / d", "Thermodynamics",
            "Rate of conductive heat flow."),
    # E&M
    Formula("Ohm's law", "V = I R", "Electricity & Magnetism",
            "Voltage, current, resistance relation."),
    Formula("Electric power", "P = V I", "Electricity & Magnetism",
            "Electrical power dissipated."),
    Formula("Coulomb's law", "F = k_e q₁ q₂ / r²", "Electricity & Magnetism",
            "Force between two point charges."),
    Formula("Electric field (point charge)", "E = k_e q / r²", "Electricity & Magnetism",
            "Field of a point charge."),
    Formula("Capacitor energy", "E = ½ C V²", "Electricity & Magnetism",
            "Energy stored in a capacitor."),
    Formula("RC time constant", "τ = R C", "Electricity & Magnetism",
            "Charging/discharging timescale."),
    Formula("Magnetic force (wire)", "F = B I L sin θ", "Electricity & Magnetism",
            "Force on a current-carrying conductor."),
    Formula("Faraday's law (emf)", "ε = − dΦ_B/dt", "Electricity & Magnetism",
            "Induced emf from changing flux."),
    # Optics & Waves
    Formula("Wave speed", "v = f λ", "Waves & Optics",
            "Speed = frequency × wavelength."),
    Formula("Photon energy", "E = h f = h c / λ", "Waves & Optics",
            "Energy of a photon."),
    Formula("Snell's law", "n₁ sin θ₁ = n₂ sin θ₂", "Waves & Optics",
            "Refraction at an interface."),
    Formula("Thin lens equation", "1/f = 1/d_o + 1/d_i", "Waves & Optics",
            "Gaussian lens formula."),
    Formula("Magnification", "m = − d_i / d_o", "Waves & Optics",
            "Lateral magnification of a lens."),
    # Fluids
    Formula("Pressure", "P = F / A", "Fluids",
            "Pressure is force per unit area."),
    Formula("Bernoulli's equation", "P + ½ρv² + ρgh = const", "Fluids",
            "Energy conservation for flowing fluid."),
    Formula("Continuity equation", "A₁ v₁ = A₂ v₂", "Fluids",
            "Conservation of mass flow."),
    # Modern / Quantum
    Formula("Mass-energy equivalence", "E = m c²", "Modern Physics",
            "Einstein's mass-energy relation."),
    Formula("de Broglie wavelength", "λ = h / p", "Modern Physics",
            "Matter wave wavelength."),
    Formula("Radioactive decay", "N = N₀ e^(−λ t)", "Modern Physics",
            "Exponential decay of unstable nuclei."),
    # Mathematics
    Formula("Quadratic formula", "x = (−b ± √(b²−4ac)) / (2a)", "Mathematics",
            "Roots of a x² + b x + c = 0."),
    Formula("Pythagorean theorem", "c² = a² + b²", "Mathematics",
            "Right-triangle relationship."),
    Formula("Euler's identity", "e^(iπ) + 1 = 0", "Mathematics",
            "Euler's famous identity."),
]


@dataclass
class UnitConversion:
    name: str
    from_unit: str
    to_unit: str
    factor: float   # multiply from_unit value by factor to get to_unit
    category: str


UNIT_CONVERSIONS: list[UnitConversion] = [
    # Length
    UnitConversion("km -> m", "km", "m", 1000.0, "Length"),
    UnitConversion("cm -> m", "cm", "m", 0.01, "Length"),
    UnitConversion("mm -> m", "mm", "m", 0.001, "Length"),
    UnitConversion("mile -> m", "mile", "m", 1609.344, "Length"),
    UnitConversion("foot -> m", "ft", "m", 0.3048, "Length"),
    UnitConversion("inch -> m", "in", "m", 0.0254, "Length"),
    UnitConversion("AU -> m", "AU", "m", 1.495978707e11, "Length"),
    UnitConversion("light-year -> m", "ly", "m", 9.4607304725808e15, "Length"),
    # Mass
    UnitConversion("g -> kg", "g", "kg", 0.001, "Mass"),
    UnitConversion("mg -> kg", "mg", "kg", 1e-6, "Mass"),
    UnitConversion("tonne -> kg", "t", "kg", 1000.0, "Mass"),
    UnitConversion("pound -> kg", "lb", "kg", 0.45359237, "Mass"),
    UnitConversion("atomic mass unit -> kg", "u", "kg", 1.66053906660e-27, "Mass"),
    # Time
    UnitConversion("min -> s", "min", "s", 60.0, "Time"),
    UnitConversion("hour -> s", "h", "s", 3600.0, "Time"),
    UnitConversion("day -> s", "day", "s", 86400.0, "Time"),
    UnitConversion("year -> s", "yr", "s", 31557600.0, "Time"),
    # Temperature (special: handled separately in UI)
    # Energy
    UnitConversion("kJ -> J", "kJ", "J", 1000.0, "Energy"),
    UnitConversion("cal -> J", "cal", "J", 4.184, "Energy"),
    UnitConversion("kcal -> J", "kcal", "J", 4184.0, "Energy"),
    UnitConversion("eV -> J", "eV", "J", 1.602176634e-19, "Energy"),
    UnitConversion("kWh -> J", "kWh", "J", 3.6e6, "Energy"),
    # Pressure
    UnitConversion("bar -> Pa", "bar", "Pa", 1e5, "Pressure"),
    UnitConversion("atm -> Pa", "atm", "Pa", 101325.0, "Pressure"),
    UnitConversion("mmHg -> Pa", "mmHg", "Pa", 133.322, "Pressure"),
    UnitConversion("psi -> Pa", "psi", "Pa", 6894.76, "Pressure"),
    # Power
    UnitConversion("kW -> W", "kW", "W", 1000.0, "Power"),
    UnitConversion("MW -> W", "MW", "W", 1e6, "Power"),
    UnitConversion("hp -> W", "hp", "W", 745.7, "Power"),
    # Angle
    UnitConversion("degree -> radian", "deg", "rad", 0.017453292519943295, "Angle"),
]


def convert_temperature(value: float, from_scale: str, to_scale: str) -> float:
    """Convert between Celsius, Fahrenheit, Kelvin."""
    # Convert to Celsius first.
    if from_scale == "C":
        c = value
    elif from_scale == "F":
        c = (value - 32.0) * 5.0 / 9.0
    elif from_scale == "K":
        c = value - 273.15
    else:
        raise ValueError(f"Unknown temperature scale: {from_scale}")
    if to_scale == "C":
        return c
    if to_scale == "F":
        return c * 9.0 / 5.0 + 32.0
    if to_scale == "K":
        return c + 273.15
    raise ValueError(f"Unknown temperature scale: {to_scale}")


SI_BASE_UNITS = [
    ("Length", "metre", "m"),
    ("Mass", "kilogram", "kg"),
    ("Time", "second", "s"),
    ("Electric current", "ampere", "A"),
    ("Temperature", "kelvin", "K"),
    ("Amount of substance", "mole", "mol"),
    ("Luminous intensity", "candela", "cd"),
]

SI_DERIVED_UNITS = [
    ("Force", "newton", "N", "kg·m/s²"),
    ("Energy", "joule", "J", "kg·m²/s²"),
    ("Power", "watt", "W", "kg·m²/s³"),
    ("Pressure", "pascal", "Pa", "kg/(m·s²)"),
    ("Frequency", "hertz", "Hz", "1/s"),
    ("Electric charge", "coulomb", "C", "A·s"),
    ("Voltage", "volt", "V", "kg·m²/(A·s³)"),
    ("Resistance", "ohm", "Ω", "kg·m²/(A²·s³)"),
    ("Capacitance", "farad", "F", "A²·s⁴/(kg·m²)"),
    ("Magnetic flux", "weber", "Wb", "kg·m²/(A·s²)"),
    ("Magnetic flux density", "tesla", "T", "kg/(A·s²)"),
    ("Inductance", "henry", "H", "kg·m²/(A²·s²)"),
]