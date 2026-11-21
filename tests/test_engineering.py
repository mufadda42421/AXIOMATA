"""Engineering engine tests."""
import numpy as np
import pytest

from axiomata.modules.engineering import engineering_engine as eng


def test_ohms_law():
    assert eng.ohms_law(voltage=12, resistance=4)["current"] == pytest.approx(3.0)
    assert eng.ohms_law(current=2, resistance=5)["voltage"] == pytest.approx(10.0)
    assert eng.ohms_law(voltage=12, current=3)["resistance"] == pytest.approx(4.0)


def test_resistor_series_parallel():
    assert eng.series_resistance(10, 20, 30) == pytest.approx(60)
    assert eng.parallel_resistance(60, 60) == pytest.approx(30)


def test_voltage_divider():
    res = eng.voltage_divider(12, 1000, 2000)
    assert res["v_out"] == pytest.approx(8.0)
    assert res["current"] == pytest.approx(12 / 3000)


def test_rotational_dynamics():
    res = eng.rotational_dynamics(10, 2, 3)
    assert res["alpha"] == pytest.approx(5.0)
    assert res["omega"] == pytest.approx(15.0)
    assert res["theta"] == pytest.approx(22.5)


def test_spring_period():
    import math
    res = eng.spring_period(1.0, 4.0)
    assert res["omega"] == pytest.approx(2.0)
    assert res["period"] == pytest.approx(math.pi, rel=1e-6)


def test_lever_balancing():
    res = eng.lever_balancing(10, 2, 20)
    assert res["distance2"] == pytest.approx(1.0)


def test_beam_central_load_deflection():
    # Simply supported beam, central point load.
    # delta_max = P L^3 / (48 E I)
    L, P, E, I = 4.0, 1000.0, 200e9, 1e-4
    res = eng.simply_supported_beam_point_load(L, P, L / 2, E, I)
    expected = P * L**3 / (48 * E * I)
    assert res["max_deflection"] == pytest.approx(expected, rel=1e-3)
    assert res["reaction_left"] == pytest.approx(P / 2)
    assert res["reaction_right"] == pytest.approx(P / 2)


def test_beam_reactions_sum_to_load():
    res = eng.simply_supported_beam_point_load(6.0, 600.0, 2.0, 200e9, 1e-4)
    assert res["reaction_left"] + res["reaction_right"] == pytest.approx(600.0)


def test_beam_deflection_curve_zero_at_supports():
    x, y = eng.beam_deflection_curve(4.0, 1000.0, 2.0, 200e9, 1e-4, n=50)
    # Deflection should be ~0 at both supports.
    assert y[0] == pytest.approx(0.0, abs=1e-6)
    assert y[-1] == pytest.approx(0.0, abs=1e-6)
    # Max deflection near centre is negative (downward).
    assert np.min(y) < 0


def test_stress_strain():
    res = eng.stress_strain(1000, 0.01, 2.0, 200e9)
    assert res["stress"] == pytest.approx(100000.0)  # 1000/0.01
    assert res["strain"] == pytest.approx(100000.0 / 200e9)