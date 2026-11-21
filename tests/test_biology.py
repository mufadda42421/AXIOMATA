"""Biology engine tests."""
import numpy as np
import pytest

from axiomata.modules.biology import biology_engine as bio


def test_mendelian_mono_hybrid():
    res = bio.mendelian_cross("Aa", "Aa")
    # Genotypes: AA, Aa, Aa, aa -> 1:2:1
    assert res["genotypes"]["AA"] == 1
    assert res["genotypes"]["Aa"] == 2
    assert res["genotypes"]["aa"] == 1
    assert res["dominant_phenotype"] == 3
    assert res["recessive_phenotype"] == 1


def test_mendelian_test_cross():
    res = bio.mendelian_cross("Aa", "aa")
    assert res["genotypes"]["Aa"] == 2
    assert res["genotypes"]["aa"] == 2
    assert res["dominant_phenotype"] == 2
    assert res["recessive_phenotype"] == 2


def test_exponential_growth():
    t = np.array([0, 1, 2])
    n = bio.exponential_growth(100, 0.5, t)
    assert n[0] == pytest.approx(100)
    assert n[1] == pytest.approx(100 * np.exp(0.5))


def test_logistic_growth_carrying_capacity():
    t = np.array([0, 10, 50, 200])
    n = bio.logistic_growth(10, 0.5, 1000, t)
    # As t grows, approaches K=1000.
    assert n[0] == pytest.approx(10)
    assert n[-1] == pytest.approx(1000, rel=1e-3)


def test_hardy_weinberg():
    res = bio.hardy_weinberg(0.7)
    assert res["AA"] == pytest.approx(0.49)
    assert res["Aa"] == pytest.approx(0.42)
    assert res["aa"] == pytest.approx(0.09)
    assert res["AA"] + res["Aa"] + res["aa"] == pytest.approx(1.0)


def test_lotka_volterra_runs():
    t, prey, pred = bio.lotka_volterra_prey_predator(
        10, 5, 0.1, 0.02, 0.01, 0.1, duration=20, steps=200)
    assert len(t) == 200
    assert np.all(prey >= 0) and np.all(pred >= 0)


def test_selection_increases_favored_allele():
    # A is favored (w_AA highest).
    res = bio.selection_change(0.5, 1.0, 0.8, 0.5)
    assert res["p_next"] > res["p"]


def test_iterate_selection_converges():
    gens, ps = bio.iterate_selection(0.1, 1.0, 0.9, 0.6, 50)
    assert ps[-1] > ps[0]  # favored allele increases
    assert np.all((ps >= 0) & (ps <= 1))