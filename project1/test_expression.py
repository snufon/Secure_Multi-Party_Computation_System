"""
Unit tests for expressions.
Testing expressions is not obligatory.

MODIFY THIS FILE.
"""

from expression import Secret, Scalar


# Example test, you can adapt it to your needs.
def test_expr_construction():
    a = Secret()
    b = Secret()
    c = Secret()
    expr = (a + b) * c * Scalar(4) + Scalar(3)
    assert repr(expr) == "((Secret() + Secret()) * (Secret())) * (Scalar(4)) + Scalar(3)"
