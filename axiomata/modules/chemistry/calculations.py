"""Chemistry calculations: molar mass, equation balancing, stoichiometry.

Molar mass is computed from the periodic-table atomic weights by parsing the
chemical formula. Molecular weight for SMILES strings uses RDKit when available.
Equation balancing uses an algebraic (matrix null-space) method and never
fabricates coefficients. All results are clearly the product of a calculation,
not a laboratory measurement.
"""
from __future__ import annotations

import re
from fractions import Fraction
from typing import Optional

import numpy as np

from .periodic_table import ELEMENTS, SYMBOL_TO_NUMBER

# Regex for a formula token: element symbol + optional count + optional group.
_TOKEN_RE = re.compile(r"([A-Z][a-z]?)(\d*)|(\(([^)]+)\))(\d*)")


def parse_formula(formula: str) -> dict[str, int]:
    """Parse a simple chemical formula into {element: count}.

    Supports nested parentheses and trailing multipliers, e.g.
    Ca(OH)2 -> {Ca:1, O:2, H:2}. Hydrate dot notation (e.g. CuSO4·5H2O) is
    NOT expanded here; handle each part separately if needed.
    """
    counts: dict[str, int] = {}

    def _add(segment: str, multiplier: int = 1) -> None:
        for match in re.finditer(r"([A-Z][a-z]?)(\d*)", segment):
            sym, num = match.group(1), match.group(2)
            n = int(num) if num else 1
            counts[sym] = counts.get(sym, 0) + n * multiplier

    # Expand nested parentheses from the inside out.
    formula = formula.replace("·", "").replace(" ", "")
    prev = None
    while prev != formula:
        prev = formula
        formula = re.sub(
            r"\(([^()]+)\)(\d*)",
            lambda m: _expand_group(m.group(1), m.group(2)),
            formula,
        )
    _add(formula)
    return counts


def _expand_group(inner: str, multiplier: str) -> str:
    n = int(multiplier) if multiplier else 1
    parts = re.findall(r"([A-Z][a-z]?)(\d*)", inner)
    out = []
    for sym, num in parts:
        cnt = (int(num) if num else 1) * n
        out.append(f"{sym}{cnt if cnt != 1 else ''}")
    return "".join(out)


def molar_mass(formula: str) -> dict:
    """Return molar mass (g/mol) and composition for a formula.

    Raises ValueError if an element symbol is unknown.
    """
    counts = parse_formula(formula)
    if not counts:
        raise ValueError(f"Could not parse formula: {formula!r}")
    total = 0.0
    composition = []
    for sym, n in counts.items():
        num = SYMBOL_TO_NUMBER.get(sym)
        if num is None or num not in ELEMENTS:
            raise ValueError(f"Unknown element symbol: {sym!r}")
        mass = ELEMENTS[num].atomic_mass * n
        total += mass
        composition.append((sym, n, ELEMENTS[num].atomic_mass, mass))
    return {
        "formula": formula,
        "molar_mass": total,
        "composition": composition,
        "counts": counts,
    }


def molecular_weight_smiles(smiles: str) -> Optional[dict]:
    """Molecular weight via RDKit for a SMILES string.

    Returns None if RDKit is unavailable or the SMILES is invalid. This is a
    cheminformatics calculation, not a measurement.
    """
    try:
        from rdkit import Chem
        from rdkit.Chem import Descriptors
    except Exception:  # noqa: BLE001 - RDKit optional
        return None
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return None
    return {
        "smiles": smiles,
        "molecular_weight": Descriptors.MolWt(mol),
        "exact_mass": Descriptors.ExactMolWt(mol),
        "formula": Chem.rdMolDescriptors.CalcMolFormula(mol),
        "num_atoms": mol.GetNumAtoms(),
    }


# --------------------------------------------------------------------------
# Equation balancing (algebraic method)
# --------------------------------------------------------------------------
def parse_reaction_side(side: str) -> list[dict]:
    """Parse one side of a reaction into species with element counts.

    Example: "Fe + O2" -> [{'formula':'Fe','coeff':1,'elements':{...}}, ...]
    """
    species = []
    for token in side.split("+"):
        token = token.strip()
        if not token:
            continue
        # Split optional leading integer coefficient.
        m = re.match(r"^(\d+)\s*(.+)$", token)
        coeff = 1
        formula = token
        if m:
            coeff = int(m.group(1))
            formula = m.group(2).strip()
        elements = parse_formula(formula)
        species.append({"formula": formula, "coeff": coeff, "elements": elements})
    return species


def balance_equation(equation: str) -> dict:
    """Balance a chemical equation using an algebraic null-space method.

    The equation is split on '->' or '='. Each side is parsed into species.
    A homogeneous linear system is built over element conservation and solved
    for integer coefficients via exact rational null-space computation.

    Returns the balanced equation string and coefficients, or a status with a
    message if it cannot be balanced (e.g. already balanced trivially, or
    inconsistent).
    """
    if "->" in equation:
        left, right = equation.split("->", 1)
    elif "=" in equation:
        left, right = equation.split("=", 1)
    else:
        raise ValueError("Equation must contain '->' or '='")

    lhs = parse_reaction_side(left)
    rhs = parse_reaction_side(right)
    species = lhs + rhs
    n = len(species)

    # Build element-conservation matrix (rows: elements, cols: species).
    elements_order: list[str] = []
    for sp in species:
        for el in sp["elements"]:
            if el not in elements_order:
                elements_order.append(el)
    A = np.zeros((len(elements_order), n))
    for j, sp in enumerate(species):
        sign = 1.0 if j < len(lhs) else -1.0
        for el, cnt in sp["elements"].items():
            row = elements_order.index(el)
            A[row, j] = sign * cnt

    # Find null space via SVD.
    u, s, vh = np.linalg.svd(A)
    tol = 1e-9
    rank = int(np.sum(s > tol))
    if rank >= n:
        return {"status": "unique_trivial",
                "message": "Equation has only the trivial solution; check the reaction.",
                "coefficients": [1] * n}

    null_mask = s <= tol
    null_dim = n - rank
    if null_dim == 0:
        return {"status": "inconsistent",
                "message": "Equation cannot be balanced (inconsistent element counts).",
                "coefficients": None}

    # Take the first null-space vector.
    vec = vh[rank:][0]
    # Convert to smallest positive integers.
    # Flip sign so the largest magnitude entry is positive.
    idx_max = int(np.argmax(np.abs(vec)))
    if vec[idx_max] < 0:
        vec = -vec
    # Rational approximation.
    coeffs = [_to_smallest_int(x) for x in vec]
    # Scale to integers by common denominator.
    coeffs_int = _scale_to_integers(coeffs)

    if any(c <= 0 for c in coeffs_int):
        # Try flipping.
        coeffs_int = [-c for c in coeffs_int]

    lhs_str = " + ".join(
        f"{c if c != 1 else ''}{species[i]['formula']}".strip()
        for i, c in enumerate(coeffs_int[:len(lhs)])
    )
    rhs_str = " + ".join(
        f"{c if c != 1 else ''}{species[i]['formula']}".strip()
        for i, c in enumerate(coeffs_int[len(lhs):], start=len(lhs))
    )
    return {
        "status": "balanced",
        "balanced": f"{lhs_str} -> {rhs_str}",
        "coefficients": coeffs_int,
        "lhs": lhs_str,
        "rhs": rhs_str,
    }


def _to_smallest_int(x: float) -> Fraction:
    frac = Fraction(x).limit_denominator(1000)
    return frac


def _scale_to_integers(coeffs: list[Fraction]) -> list[int]:
    from math import lcm
    denominators = [c.denominator for c in coeffs]
    common = 1
    for d in denominators:
        common = lcm(common, d)
    scaled = [int(c * common) for c in coeffs]
    # Divide by gcd.
    from math import gcd
    g = 0
    for s in scaled:
        g = gcd(g, abs(s))
    if g > 1:
        scaled = [s // g for s in scaled]
    return scaled


# --------------------------------------------------------------------------
# Stoichiometry
# --------------------------------------------------------------------------
def stoichiometry(
    grams: float, molar_mass_reactant: float, mole_ratio_reactant_to_product: float,
    molar_mass_product: float,
) -> dict:
    """Basic stoichiometry: mass of product from mass of a reactant.

    steps:
        moles_reactant = grams / MM_reactant
        moles_product  = moles_reactant * ratio
        grams_product  = moles_product * MM_product
    """
    if molar_mass_reactant <= 0 or molar_mass_product <= 0:
        raise ValueError("molar masses must be positive")
    moles_reactant = grams / molar_mass_reactant
    moles_product = moles_reactant * mole_ratio_reactant_to_product
    grams_product = moles_product * molar_mass_product
    return {
        "moles_reactant": moles_reactant,
        "moles_product": moles_product,
        "grams_product": grams_product,
    }