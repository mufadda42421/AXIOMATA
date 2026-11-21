"""A compact periodic table dataset with essential element data.

Data is stored as plain Python structures (no external downloads needed) and is
sufficient for atomic structure viewing, molar-mass calculation, and element
information. Atomic weights are standard conventional values (IUPAC-inspired).
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Element:
    number: int
    symbol: str
    name: str
    atomic_mass: float      # standard atomic weight (u / g/mol)
    group: int              # 1-18 (0 for lanthanides/actinides placeholder)
    period: int
    category: str           # e.g. "alkali metal", "nonmetal", "noble gas"
    electron_config: str


# number, symbol, name, atomic_mass, group, period, category, config
_RAW: list[tuple] = [
    (1, "H", "Hydrogen", 1.008, 1, 1, "nonmetal", "1s1"),
    (2, "He", "Helium", 4.0026, 18, 1, "noble gas", "1s2"),
    (3, "Li", "Lithium", 6.94, 1, 2, "alkali metal", "[He] 2s1"),
    (4, "Be", "Beryllium", 9.0122, 2, 2, "alkaline earth metal", "[He] 2s2"),
    (5, "B", "Boron", 10.81, 13, 2, "metalloid", "[He] 2s2 2p1"),
    (6, "C", "Carbon", 12.011, 14, 2, "nonmetal", "[He] 2s2 2p2"),
    (7, "N", "Nitrogen", 14.007, 15, 2, "nonmetal", "[He] 2s2 2p3"),
    (8, "O", "Oxygen", 15.999, 16, 2, "nonmetal", "[He] 2s2 2p4"),
    (9, "F", "Fluorine", 18.998, 17, 2, "halogen", "[He] 2s2 2p5"),
    (10, "Ne", "Neon", 20.180, 18, 2, "noble gas", "[He] 2s2 2p6"),
    (11, "Na", "Sodium", 22.990, 1, 3, "alkali metal", "[Ne] 3s1"),
    (12, "Mg", "Magnesium", 24.305, 2, 3, "alkaline earth metal", "[Ne] 3s2"),
    (13, "Al", "Aluminium", 26.982, 13, 3, "post-transition metal", "[Ne] 3s2 3p1"),
    (14, "Si", "Silicon", 28.085, 14, 3, "metalloid", "[Ne] 3s2 3p2"),
    (15, "P", "Phosphorus", 30.974, 15, 3, "nonmetal", "[Ne] 3s2 3p3"),
    (16, "S", "Sulfur", 32.06, 16, 3, "nonmetal", "[Ne] 3s2 3p4"),
    (17, "Cl", "Chlorine", 35.45, 17, 3, "halogen", "[Ne] 3s2 3p5"),
    (18, "Ar", "Argon", 39.948, 18, 3, "noble gas", "[Ne] 3s2 3p6"),
    (19, "K", "Potassium", 39.098, 1, 4, "alkali metal", "[Ar] 4s1"),
    (20, "Ca", "Calcium", 40.078, 2, 4, "alkaline earth metal", "[Ar] 4s2"),
    (21, "Sc", "Scandium", 44.956, 3, 4, "transition metal", "[Ar] 3d1 4s2"),
    (22, "Ti", "Titanium", 47.867, 4, 4, "transition metal", "[Ar] 3d2 4s2"),
    (23, "V", "Vanadium", 50.942, 5, 4, "transition metal", "[Ar] 3d3 4s2"),
    (24, "Cr", "Chromium", 51.996, 6, 4, "transition metal", "[Ar] 3d5 4s1"),
    (25, "Mn", "Manganese", 54.938, 7, 4, "transition metal", "[Ar] 3d5 4s2"),
    (26, "Fe", "Iron", 55.845, 8, 4, "transition metal", "[Ar] 3d6 4s2"),
    (27, "Co", "Cobalt", 58.933, 9, 4, "transition metal", "[Ar] 3d7 4s2"),
    (28, "Ni", "Nickel", 58.693, 10, 4, "transition metal", "[Ar] 3d8 4s2"),
    (29, "Cu", "Copper", 63.546, 11, 4, "transition metal", "[Ar] 3d10 4s1"),
    (30, "Zn", "Zinc", 65.38, 12, 4, "transition metal", "[Ar] 3d10 4s2"),
    (31, "Ga", "Gallium", 69.723, 13, 4, "post-transition metal", "[Ar] 3d10 4s2 4p1"),
    (32, "Ge", "Germanium", 72.630, 14, 4, "metalloid", "[Ar] 3d10 4s2 4p2"),
    (33, "As", "Arsenic", 74.922, 15, 4, "metalloid", "[Ar] 3d10 4s2 4p3"),
    (34, "Se", "Selenium", 78.971, 16, 4, "nonmetal", "[Ar] 3d10 4s2 4p4"),
    (35, "Br", "Bromine", 79.904, 17, 4, "halogen", "[Ar] 3d10 4s2 4p5"),
    (36, "Kr", "Krypton", 83.798, 18, 4, "noble gas", "[Ar] 3d10 4s2 4p6"),
    (37, "Rb", "Rubidium", 85.468, 1, 5, "alkali metal", "[Kr] 5s1"),
    (38, "Sr", "Strontium", 87.62, 2, 5, "alkaline earth metal", "[Kr] 5s2"),
    (39, "Y", "Yttrium", 88.906, 3, 5, "transition metal", "[Kr] 4d1 5s2"),
    (40, "Zr", "Zirconium", 91.224, 4, 5, "transition metal", "[Kr] 4d2 5s2"),
    (41, "Nb", "Niobium", 92.906, 5, 5, "transition metal", "[Kr] 4d4 5s1"),
    (42, "Mo", "Molybdenum", 95.95, 6, 5, "transition metal", "[Kr] 4d5 5s1"),
    (43, "Tc", "Technetium", 98.0, 7, 5, "transition metal", "[Kr] 4d5 5s2"),
    (44, "Ru", "Ruthenium", 101.07, 8, 5, "transition metal", "[Kr] 4d7 5s1"),
    (45, "Rh", "Rhodium", 102.91, 9, 5, "transition metal", "[Kr] 4d8 5s1"),
    (46, "Pd", "Palladium", 106.42, 10, 5, "transition metal", "[Kr] 4d10"),
    (47, "Ag", "Silver", 107.87, 11, 5, "transition metal", "[Kr] 4d10 5s1"),
    (48, "Cd", "Cadmium", 112.41, 12, 5, "transition metal", "[Kr] 4d10 5s2"),
    (49, "In", "Indium", 114.82, 13, 5, "post-transition metal", "[Kr] 4d10 5s2 5p1"),
    (50, "Sn", "Tin", 118.71, 14, 5, "post-transition metal", "[Kr] 4d10 5s2 5p2"),
    (51, "Sb", "Antimony", 121.76, 15, 5, "metalloid", "[Kr] 4d10 5s2 5p3"),
    (52, "Te", "Tellurium", 127.60, 16, 5, "metalloid", "[Kr] 4d10 5s2 5p4"),
    (53, "I", "Iodine", 126.90, 17, 5, "halogen", "[Kr] 4d10 5s2 5p5"),
    (54, "Xe", "Xenon", 131.29, 18, 5, "noble gas", "[Kr] 4d10 5s2 5p6"),
    (55, "Cs", "Caesium", 132.91, 1, 6, "alkali metal", "[Xe] 6s1"),
    (56, "Ba", "Barium", 137.33, 2, 6, "alkaline earth metal", "[Xe] 6s2"),
    (72, "Hf", "Hafnium", 178.49, 4, 6, "transition metal", "[Xe] 4f14 5d2 6s2"),
    (73, "Ta", "Tantalum", 180.95, 5, 6, "transition metal", "[Xe] 4f14 5d3 6s2"),
    (74, "W", "Tungsten", 183.84, 6, 6, "transition metal", "[Xe] 4f14 5d4 6s2"),
    (75, "Re", "Rhenium", 186.21, 7, 6, "transition metal", "[Xe] 4f14 5d5 6s2"),
    (76, "Os", "Osmium", 190.23, 8, 6, "transition metal", "[Xe] 4f14 5d6 6s2"),
    (77, "Ir", "Iridium", 192.22, 9, 6, "transition metal", "[Xe] 4f14 5d7 6s2"),
    (78, "Pt", "Platinum", 195.08, 10, 6, "transition metal", "[Xe] 4f14 5d9 6s1"),
    (79, "Au", "Gold", 196.97, 11, 6, "transition metal", "[Xe] 4f14 5d10 6s1"),
    (80, "Hg", "Mercury", 200.59, 12, 6, "transition metal", "[Xe] 4f14 5d10 6s2"),
    (81, "Tl", "Thallium", 204.38, 13, 6, "post-transition metal", "[Xe] 4f14 5d10 6s2 6p1"),
    (82, "Pb", "Lead", 207.2, 14, 6, "post-transition metal", "[Xe] 4f14 5d10 6s2 6p2"),
    (83, "Bi", "Bismuth", 208.98, 15, 6, "post-transition metal", "[Xe] 4f14 5d10 6s2 6p3"),
    (84, "Po", "Polonium", 209.0, 16, 6, "post-transition metal", "[Xe] 4f14 5d10 6s2 6p4"),
    (85, "At", "Astatine", 210.0, 17, 6, "halogen", "[Xe] 4f14 5d10 6s2 6p5"),
    (86, "Rn", "Radon", 222.0, 18, 6, "noble gas", "[Xe] 4f14 5d10 6s2 6p6"),
    (87, "Fr", "Francium", 223.0, 1, 7, "alkali metal", "[Rn] 7s1"),
    (88, "Ra", "Radium", 226.0, 2, 7, "alkaline earth metal", "[Rn] 7s2"),
    (104, "Rf", "Rutherfordium", 267.0, 4, 7, "transition metal", "[Rn] 5f14 6d2 7s2"),
    (105, "Db", "Dubnium", 268.0, 5, 7, "transition metal", "[Rn] 5f14 6d3 7s2"),
    (106, "Sg", "Seaborgium", 269.0, 6, 7, "transition metal", "[Rn] 5f14 6d4 7s2"),
    (107, "Bh", "Bohrium", 270.0, 7, 7, "transition metal", "[Rn] 5f14 6d5 7s2"),
    (108, "Hs", "Hassium", 269.0, 8, 7, "transition metal", "[Rn] 5f14 6d6 7s2"),
    (109, "Mt", "Meitnerium", 278.0, 9, 7, "transition metal", "[Rn] 5f14 6d7 7s2"),
    (110, "Ds", "Darmstadtium", 281.0, 10, 7, "transition metal", "[Rn] 5f14 6d8 7s2"),
    (111, "Rg", "Roentgenium", 282.0, 11, 7, "transition metal", "[Rn] 5f14 6d9 7s2"),
    (112, "Cn", "Copernicium", 285.0, 12, 7, "transition metal", "[Rn] 5f14 6d10 7s2"),
    (113, "Nh", "Nihonium", 286.0, 13, 7, "post-transition metal", "[Rn] 5f14 6d10 7s2 7p1"),
    (114, "Fl", "Flerovium", 289.0, 14, 7, "post-transition metal", "[Rn] 5f14 6d10 7s2 7p2"),
    (115, "Mc", "Moscovium", 290.0, 15, 7, "post-transition metal", "[Rn] 5f14 6d10 7s2 7p3"),
    (116, "Lv", "Livermorium", 293.0, 16, 7, "post-transition metal", "[Rn] 5f14 6d10 7s2 7p4"),
    (117, "Ts", "Tennessine", 294.0, 17, 7, "halogen", "[Rn] 5f14 6d10 7s2 7p5"),
    (118, "Og", "Oganesson", 294.0, 18, 7, "noble gas", "[Rn] 5f14 6d10 7s2 7p6"),
]

# Lanthanides and actinides (f-block, placed separately in the table view).
_LANTHANIDES = [
    (57, "La", "Lanthanum", 138.91, "5d1 6s2"),
    (58, "Ce", "Cerium", 140.12, "4f1 5d1 6s2"),
    (59, "Pr", "Praseodymium", 140.91, "4f3 6s2"),
    (60, "Nd", "Neodymium", 144.24, "4f4 6s2"),
    (61, "Pm", "Promethium", 145.0, "4f5 6s2"),
    (62, "Sm", "Samarium", 150.36, "4f6 6s2"),
    (63, "Eu", "Europium", 151.96, "4f7 6s2"),
    (64, "Gd", "Gadolinium", 157.25, "4f7 5d1 6s2"),
    (65, "Tb", "Terbium", 158.93, "4f9 6s2"),
    (66, "Dy", "Dysprosium", 162.50, "4f10 6s2"),
    (67, "Ho", "Holmium", 164.93, "4f11 6s2"),
    (68, "Er", "Erbium", 167.26, "4f12 6s2"),
    (69, "Tm", "Thulium", 168.93, "4f13 6s2"),
    (70, "Yb", "Ytterbium", 173.05, "4f14 6s2"),
    (71, "Lu", "Lutetium", 174.97, "4f14 5d1 6s2"),
]
_ACTINIDES = [
    (89, "Ac", "Actinium", 227.0, "6d1 7s2"),
    (90, "Th", "Thorium", 232.04, "6d2 7s2"),
    (91, "Pa", "Protactinium", 231.04, "5f2 6d1 7s2"),
    (92, "U", "Uranium", 238.03, "5f3 6d1 7s2"),
    (93, "Np", "Neptunium", 237.0, "5f4 6d1 7s2"),
    (94, "Pu", "Plutonium", 244.0, "5f6 7s2"),
    (95, "Am", "Americium", 243.0, "5f7 7s2"),
    (96, "Cm", "Curium", 247.0, "5f7 6d1 7s2"),
    (97, "Bk", "Berkelium", 247.0, "5f9 7s2"),
    (98, "Cf", "Californium", 251.0, "5f10 7s2"),
    (99, "Es", "Einsteinium", 252.0, "5f11 7s2"),
    (100, "Fm", "Fermium", 257.0, "5f12 7s2"),
    (101, "Md", "Mendelevium", 258.0, "5f13 7s2"),
    (102, "No", "Nobelium", 259.0, "5f14 7s2"),
    (103, "Lr", "Lawrencium", 266.0, "5f14 7s2 7p1"),
]


def _build_elements() -> dict[int, Element]:
    table: dict[int, Element] = {}
    for num, sym, name, mass, group, period, cat, cfg in _RAW:
        table[num] = Element(num, sym, name, mass, group, period, cat, cfg)
    for num, sym, name, mass, cfg in _LANTHANIDES:
        table[num] = Element(num, sym, name, mass, 0, 6, "lanthanide", f"[Xe] {cfg}")
    for num, sym, name, mass, cfg in _ACTINIDES:
        table[num] = Element(num, sym, name, mass, 0, 7, "actinide", f"[Rn] {cfg}")
    return table


ELEMENTS: dict[int, Element] = _build_elements()

SYMBOL_TO_NUMBER: dict[str, int] = {e.symbol: e.number for e in ELEMENTS.values()}
NAME_TO_NUMBER: dict[str, int] = {e.name.lower(): e.number for e in ELEMENTS.values()}


def get_element_by_symbol(symbol: str) -> Element | None:
    return ELEMENTS.get(SYMBOL_TO_NUMBER.get(symbol.capitalize() if len(symbol) > 1 else symbol.upper(), -1))


def get_element_by_number(number: int) -> Element | None:
    return ELEMENTS.get(number)


def get_element_by_name(name: str) -> Element | None:
    num = NAME_TO_NUMBER.get(name.strip().lower())
    return ELEMENTS.get(num) if num else None


# Category -> display colour for the periodic table.
CATEGORY_COLORS: dict[str, str] = {
    "alkali metal": "#f97316",
    "alkaline earth metal": "#f59e0b",
    "transition metal": "#eab308",
    "post-transition metal": "#84cc16",
    "metalloid": "#22c55e",
    "nonmetal": "#06b6d4",
    "halogen": "#3b82f6",
    "noble gas": "#8b5cf6",
    "lanthanide": "#ec4899",
    "actinide": "#ef4444",
}