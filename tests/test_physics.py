"""Scientific correctness tests for the physics engine."""
import math

import numpy as np
import pytest

from axiomata.modules.physics import (
    electromagnetism as em,
    mechanics as mech,
    optics,
    thermodynamics as thermo,
)


def test_projectile_range_known_value():
    # v0=20, 45 deg, level ground -> range = v0^2/g
    r = mech.projectile_motion(20.0, 45.0)
    expected = 20.0**2 / mech.G
    assert r["range"] == pytest.approx(expected, rel=1e-9)
    # At 45 deg max range; height should be range/4
    assert r["max_height"] == pytest.approx(expected / 4.0, rel=1e-9)


def test_projectile_max_height_formula():
    # Straight up (90 deg): max height = v0^2/(2g)
    r = mech.projectile_motion(10.0, 90.0)
    assert r["max_height"] == pytest.approx(10.0**2 / (2 * mech.G), rel=1e-9)
    assert r["range"] == pytest.approx(0.0, abs=1e-9)


def test_uniformly_accelerated_matches_kinematics():
    s, v, t = mech.uniformly_accelerated(0.0, 0.0, 2.0, np.array([0, 1, 2, 3]))
    # s = 0.5*2*t^2 = t^2
    assert np.allclose(s, np.array([0, 1, 4, 9]))
    assert np.allclose(v, np.array([0, 2, 4, 6]))


def test_pendulum_small_angle_period():
    # T = 2 pi sqrt(L/g)
    L = 1.0
    T = mech.pendulum_period(L, amplitude_deg=0.0)
    assert T == pytest.approx(2 * math.pi * math.sqrt(L / mech.G), rel=1e-9)


def test_pendulum_large_amplitude_longer_period():
    T_small = mech.pendulum_period(1.0, amplitude_deg=1.0)
    T_large = mech.pendulum_period(1.0, amplitude_deg=60.0)
    assert T_large > T_small  # larger amplitude -> longer period


def test_elastic_collision_conserves_momentum_and_energy():
    m1, v1, m2, v2 = 2.0, 3.0, 3.0, -1.0
    v1f, v2f = mech.momentum_collision_1d(m1, v1, m2, v2, restitution=1.0)
    p_before = m1 * v1 + m2 * v2
    p_after = m1 * v1f + m2 * v2f
    ke_before = 0.5 * m1 * v1**2 + 0.5 * m2 * v2**2
    ke_after = 0.5 * m1 * v1f**2 + 0.5 * m2 * v2f**2
    assert p_after == pytest.approx(p_before)
    assert ke_after == pytest.approx(ke_before)


def test_inelastic_collision_conserves_momentum_only():
    m1, v1, m2, v2 = 2.0, 3.0, 3.0, -1.0
    v1f, v2f = mech.momentum_collision_1d(m1, v1, m2, v2, restitution=0.0)
    assert v1f == pytest.approx(v2f)  # they stick together
    p_before = m1 * v1 + m2 * v2
    assert (m1 * v1f + m2 * v2f) == pytest.approx(p_before)


def test_gravitational_force_known_value():
    # Two 1 kg masses 1 m apart -> F = G (6.67430e-11)
    f = mech.gravitational_force(1.0, 1.0, 1.0)
    assert f == pytest.approx(6.67430e-11, rel=1e-4)


def test_ideal_gas_law_solve_pressure():
    # 1 mol, 22.4 L at 273.15 K ~ 101325 Pa (approx at STP with real R)
    res = thermo.ideal_gas_law(v=0.022414, n=1.0, t=273.15)
    assert res["p"] == pytest.approx(101325, rel=0.01)


def test_ideal_gas_law_roundtrip():
    res = thermo.ideal_gas_law(p=100000.0, v=0.01, n=1.0)
    t = res["t"]
    # re-solve using computed t should return the original p
    res2 = thermo.ideal_gas_law(v=0.01, n=1.0, t=t)
    assert res2["p"] == pytest.approx(100000.0)


def test_sensible_heat():
    # Q = m c dT ; water c=4186, 1 kg, +10 K -> 41860 J
    q = thermo.sensible_heat(1.0, 4186.0, 10.0)
    assert q == pytest.approx(41860.0)


def test_thermal_expansion():
    res = thermo.thermal_expansion_linear(1.0, 1.7e-5, 100.0)
    assert res["delta_length"] == pytest.approx(1.7e-3)


def test_coulomb_force_known_value():
    # 1 C and 1 C at 1 m -> k
    res = em.coulombs_law(1.0, 1.0, 1.0)
    assert res["force"] == pytest.approx(em.COULOMB_K, rel=1e-9)
    assert res["direction"] == "repulsive"
    res2 = em.coulombs_law(1.0, -1.0, 1.0)
    assert res2["direction"] == "attractive"


def test_ohms_law_solve():
    assert em.ohms_law(i=2.0, r=5.0)["v"] == pytest.approx(10.0)
    assert em.ohms_law(v=10.0, r=5.0)["i"] == pytest.approx(2.0)
    assert em.ohms_law(v=10.0, i=2.0)["r"] == pytest.approx(5.0)


def test_resistor_series_parallel():
    assert em.resistor_series(10.0, 20.0) == pytest.approx(30.0)
    assert em.resistor_parallel(10.0, 10.0) == pytest.approx(5.0)


def test_capacitor_energy():
    # E = 0.5 C V^2 ; C=1F, V=2V -> 2 J
    assert em.capacitor_energy(1.0, 2.0) == pytest.approx(2.0)


def test_rc_time_constant():
    # After 1 tau (t=RC), charge reaches ~63.2% of V0
    r, c, v0 = 1000.0, 1e-3, 5.0
    tau = r * c
    vc = em.rc_charge(tau, r, c, v0)
    assert vc == pytest.approx(v0 * (1 - math.exp(-1)))


def test_snell_refraction_known():
    # air->glass n1=1, n2=1.5, 30 deg incidence
    res = optics.snell_refraction(1.0, 1.5, 30.0)
    expected = math.degrees(math.asin(math.sin(math.radians(30)) / 1.5))
    assert res["refracted_deg"] == pytest.approx(expected)
    assert res["total_internal_reflection"] is False


def test_total_internal_reflection():
    res = optics.snell_refraction(1.5, 1.0, 60.0)  # glass->air, > critical
    assert res["total_internal_reflection"] is True


def test_critical_angle():
    crit = optics.critical_angle(1.5, 1.0)
    assert crit == pytest.approx(math.degrees(math.asin(1.0 / 1.5)))


def test_thin_lens_real_image():
    # f=0.1m, do=0.3m -> 1/f - 1/do = 1/di -> di = 0.15
    res = optics.thin_lens(0.1, 0.3)
    assert res["image_distance"] == pytest.approx(0.15)
    assert res["image_type"] == "real"
    assert res["magnification"] == pytest.approx(-0.5)


def test_photon_energy():
    # 500 nm photon ~ 3.97e-19 J
    e = optics.photon_energy(500.0)
    assert e == pytest.approx(3.973e-19, rel=0.01)