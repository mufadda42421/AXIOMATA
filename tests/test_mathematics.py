"""Mathematics engine tests."""
import math

import pytest

from axiomata.modules.mathematics import math_engine as m


def test_differentiate_power():
    assert m.differentiate("x**2") == "2*x"
    assert m.differentiate("x**3", order=2) == "6*x"


def test_integrate_indefinite():
    assert m.integrate("2*x") == "x**2"


def test_integrate_definite():
    import sympy as sp
    # integral of x from 0 to 1 = 0.5
    assert float(sp.sympify(m.integrate("x", lower=0, upper=1))) == pytest.approx(0.5)


def test_solve_linear():
    sols = m.solve_equation("2*x + 4 = 0")
    assert float(sols[0]) == pytest.approx(-2.0)


def test_solve_quadratic():
    sols = m.solve_equation("x**2 - 5*x + 6 = 0")
    vals = sorted(float(s) for s in sols)
    assert vals == pytest.approx([2.0, 3.0])


def test_evaluate_numeric():
    assert m.evaluate_numeric("x**2 + 1", 3) == pytest.approx(10.0)


def test_simplify():
    assert m.simplify("(x + 1)**2 - x**2") == "2*x + 1"


def test_matrix_add():
    res = m.matrix_operations([[1, 2], [3, 4]], [[5, 6], [7, 8]], "add")
    assert res == [[6, 8], [10, 12]]


def test_matrix_multiply():
    res = m.matrix_operations([[1, 2], [3, 4]], [[5, 6], [7, 8]], "multiply")
    assert res == [[19, 22], [43, 50]]


def test_matrix_transpose():
    res = m.matrix_operations([[1, 2, 3], [4, 5, 6]], op="transpose")
    assert res == [[1, 4], [2, 5], [3, 6]]


def test_matrix_determinant():
    assert m.matrix_determinant([[1, 2], [3, 4]]) == pytest.approx(-2.0)


def test_matrix_inverse():
    inv = m.matrix_inverse([[4, 7], [2, 6]])
    # det = 24-14 = 10; inv = 1/10 [[6,-7],[-2,4]]
    assert inv[0][0] == pytest.approx(0.6)
    assert inv[0][1] == pytest.approx(-0.7)
    assert inv[1][0] == pytest.approx(-0.2)
    assert inv[1][1] == pytest.approx(0.4)


def test_matrix_inverse_singular():
    with pytest.raises(ValueError):
        m.matrix_inverse([[1, 2], [2, 4]])


def test_vector_ops():
    assert m.vector_dot([1, 2, 3], [4, 5, 6]) == pytest.approx(32)
    assert m.vector_cross([1, 0, 0], [0, 1, 0]) == [0, 0, 1]
    assert m.vector_norm([3, 4]) == pytest.approx(5.0)


def test_complex_ops():
    a, b = complex(1, 2), complex(3, 4)
    assert m.complex_operations(a, b, "add") == complex(4, 6)
    assert m.complex_operations(a, b, "multiply") == complex(-5, 10)


def test_bisection_root():
    # root of x^2 - 2 on [0, 2] = sqrt(2)
    res = m.bisection_root("x**2 - 2", 0, 2)
    assert res["root"] == pytest.approx(math.sqrt(2), abs=1e-6)
    assert res["converged"] is True


def test_bisection_wrong_bracket():
    with pytest.raises(ValueError):
        m.bisection_root("x**2 + 1", 0, 2)  # no sign change


def test_numerical_integral():
    # integral of x^2 from 0 to 1 = 1/3
    res = m.numerical_integral("x**2", 0, 1)
    assert res == pytest.approx(1 / 3, rel=1e-3)


def test_roots_of_unity():
    roots = m.roots_of_unity(4)
    assert len(roots) == 4
    for r in roots:
        assert abs(abs(r) - 1.0) < 1e-9