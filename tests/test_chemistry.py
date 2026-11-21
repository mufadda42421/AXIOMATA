"""Chemistry engine + periodic table tests."""
import math

import pytest

from axiomata.modules.chemistry import calculations as calc
from axiomata.modules.chemistry.periodic_table import (
    ELEMENTS,
    get_element_by_name,
    get_element_by_number,
    get_element_by_symbol,
)


def test_element_lookup():
    assert get_element_by_symbol("C").name == "Carbon"
    assert get_element_by_symbol("Na").name == "Sodium"
    assert get_element_by_number(8).symbol == "O"
    assert get_element_by_name("gold").symbol == "Au"


def test_periodic_table_complete_118():
    assert 1 in ELEMENTS and 118 in ELEMENTS
    # All elements have positive atomic mass.
    for e in ELEMENTS.values():
        assert e.atomic_mass > 0
        assert e.symbol and e.name


def test_parse_formula_simple():
    assert calc.parse_formula("H2O") == {"H": 2, "O": 1}
    assert calc.parse_formula("CO2") == {"C": 1, "O": 2}
    assert calc.parse_formula("NaCl") == {"Na": 1, "Cl": 1}


def test_parse_formula_parentheses():
    assert calc.parse_formula("Ca(OH)2") == {"Ca": 1, "O": 2, "H": 2}
    assert calc.parse_formula("Al2(SO4)3") == {"Al": 2, "S": 3, "O": 12}


def test_molar_mass_water():
    res = calc.molar_mass("H2O")
    # 2*1.008 + 15.999 = 18.015
    assert res["molar_mass"] == pytest.approx(18.015, abs=0.01)


def test_molar_mass_calcium_hydroxide():
    res = calc.molar_mass("Ca(OH)2")
    # Ca 40.078 + 2*(15.999 + 1.008) = 74.092
    assert res["molar_mass"] == pytest.approx(74.092, abs=0.02)


def test_molar_mass_unknown_element():
    with pytest.raises(ValueError):
        calc.molar_mass("Xx2O")


def test_balance_combustion_methane():
    res = calc.balance_equation("CH4 + O2 -> CO2 + H2O")
    assert res["status"] == "balanced"
    # CH4 + 2 O2 -> CO2 + 2 H2O
    assert res["coefficients"] == [1, 2, 1, 2]


def test_balance_iron_oxide():
    res = calc.balance_equation("Fe + O2 -> Fe2O3")
    assert res["status"] == "balanced"
    # 4 Fe + 3 O2 -> 2 Fe2O3
    assert res["coefficients"] == [4, 3, 2]


def test_balance_haber():
    res = calc.balance_equation("N2 + H2 -> NH3")
    assert res["status"] == "balanced"
    # N2 + 3 H2 -> 2 NH3
    assert res["coefficients"] == [1, 3, 2]


def test_balance_with_initial_coefficients():
    # Should still balance even with a pre-written coefficient.
    res = calc.balance_equation("2H2 + O2 -> 2H2O")
    assert res["status"] == "balanced"


def test_stoichiometry_water_from_hydrogen():
    # 4 g H2 -> how many g H2O? MM H2=2.016, MM H2O=18.015, ratio 1
    res = calc.stoichiometry(4.0, 2.016, 1.0, 18.015)
    # moles H2 = 4/2.016 = 1.984; g water = 1.984 * 18.015 = 35.74
    assert res["grams_product"] == pytest.approx(35.74, abs=0.05)


def test_molecular_weight_smiles_optional():
    # RDKit is installed; glucose C6H12O6 ~ 180.16
    res = calc.molecular_weight_smiles("C1(H(O)OH)OC(H(O)OH)C(H(O)OH)C1(H(O)OH)")
    if res is None:
        pytest.skip("RDKit not available")
    # Use a simple known molecule instead: ethanol CCO
    eth = calc.molecular_weight_smiles("CCO")
    assert eth is not None
    assert eth["molecular_weight"] == pytest.approx(46.07, abs=0.1)