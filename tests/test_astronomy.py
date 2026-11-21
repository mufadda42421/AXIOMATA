"""Astronomy engine tests."""
import math

import pytest

from axiomata.modules.astronomy import astronomy_engine as astro


def test_kepler_third_law_earth():
    # Earth: a = 1 AU, central mass = Sun -> T ~ 365.25 days
    a_m = astro.AU_M
    T_days = astro.orbital_period_semi_major_axis(a_m, astro.M_SUN) / astro.DAY_S
    assert T_days == pytest.approx(365.25, rel=0.01)


def test_planet_period_check_matches_table():
    for p in astro.PLANETS:
        T = astro.planet_period_check(p)
        # Should be within a few percent of tabulated value.
        assert T == pytest.approx(p["period_days"], rel=0.05)


def test_circular_orbit_velocity_earth():
    v = astro.orbital_velocity_circular(astro.AU_M, astro.M_SUN)
    # ~29.78 km/s
    assert v == pytest.approx(29780, rel=0.01)


def test_escape_velocity_earth_surface():
    v = astro.escape_velocity(6.371e6, astro.M_EARTH)
    # ~11.2 km/s
    assert v == pytest.approx(11186, rel=0.01)


def test_vis_viva_circular():
    # Circular orbit: r = a -> v = sqrt(GM/r)
    r = astro.AU_M
    v = astro.vis_viva(r, r, astro.M_SUN)
    assert v == pytest.approx(astro.orbital_velocity_circular(r, astro.M_SUN))


def test_kepler_equation_roundtrip():
    # For e=0, E should equal M.
    E = astro.kepler_solve_mean_anomaly(1.0, 0.0)
    assert E == pytest.approx(1.0)
    # For e=0.5, verify M = E - e sin E.
    M = 1.0
    E = astro.kepler_solve_mean_anomaly(M, 0.5)
    assert E - 0.5 * math.sin(E) == pytest.approx(M, abs=1e-9)


def test_moon_phase_new():
    res = astro.moon_phase_illumination(0.0)
    assert res["illumination"] == pytest.approx(0.0, abs=1e-3)
    assert res["phase_name"] == "New Moon"


def test_moon_phase_full():
    res = astro.moon_phase_illumination(14.765)  # half a synodic month
    assert res["illumination"] == pytest.approx(1.0, abs=0.01)
    assert res["phase_name"] == "Full Moon"


def test_light_travel_time():
    # 1 AU ~ 8.3 light-minutes
    t = astro.light_travel_time_from_sun(1.0)
    assert t == pytest.approx(8.317, rel=0.01)


def test_orbit_position_r():
    res = astro.orbit_position(1.0, 0.0, 0.0)
    # Circular: r = a = 1
    assert res["r"] == pytest.approx(1.0)