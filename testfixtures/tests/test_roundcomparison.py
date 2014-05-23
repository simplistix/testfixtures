# Copyright (c) 2014 Simplistix Ltd
# See license.txt for license details.

from decimal import Decimal
from testfixtures import RoundComparison as R, compare, ShouldRaise
from unittest import TestCase

from ..compat import PY2, PY3

class Tests(TestCase):

    def test_equal_yes_rhs(self):
        self.assertTrue(0.123457 == R(0.123456, 5))

    def test_equal_yes_lhs(self):
        self.assertTrue(R(0.123456, 5) == 0.123457)

    def test_equal_no_rhs(self):
        self.assertFalse(0.123453 == R(0.123456, 5))

    def test_equal_no_lhs(self):
        self.assertFalse(R(0.123456, 5) == 0.123453)

    def test_not_equal_yes_rhs(self):
        self.assertFalse(0.123457 != R(0.123456, 5))

    def test_not_equal_yes_lhs(self):
        self.assertFalse(R(0.123456, 5) != 0.123457)

    def test_not_equal_no_rhs(self):
        self.assertTrue(0.123453 != R(0.123456, 5))

    def test_not_equal_no_lhs(self):
        self.assertTrue(R(0.123456, 5) != 0.123453)

    def test_comp_in_sequence_rhs(self):
        self.assertTrue((1, 2, 0.123457) == (1, 2, R(0.123456, 5)))

    def test_comp_in_sequence_lhs(self):
        self.assertTrue((1, 2, R(0.123456, 5)) == (1, 2, 0.123457))

    def test_not_numeric_rhs(self):
        with ShouldRaise(TypeError):
            'abc' == R(0.123456, 5)

    def test_not_numeric_lhs(self):
        with ShouldRaise(TypeError):
            R(0.123456, 5)  ==  'abc'

    def test_repr(self):
        compare('<R:0.12346>',
                repr(R(0.123456, 5)))

    def test_str(self):
        compare('<R:0.12346>',
                repr(R(0.123456, 5)))
    
    def test_equal_yes_decimal_to_float_rhs(self):
        self.assertTrue(Decimal("0.123457") == R(0.123456, 5))

    def test_equal_yes_decimal_to_float_lhs(self):
        self.assertTrue(R(0.123456, 5) == Decimal("0.123457"))

    def test_equal_no_decimal_to_float_rhs(self):
        self.assertFalse(Decimal("0.123453") == R(0.123456, 5))

    def test_equal_no_decimal_to_float_lhs(self):
        self.assertFalse(R(0.123456, 5) == Decimal("0.123453"))

    def test_equal_yes_float_to_decimal_rhs(self):
        self.assertTrue(0.123457 == R(Decimal("0.123456"), 5))

    def test_equal_yes_float_to_decimal_lhs(self):
        self.assertTrue(R(Decimal("0.123456"), 5) == 0.123457)

    def test_equal_no_float_to_decimal_rhs(self):
        self.assertFalse(0.123453 == R(Decimal("0.123456"), 5))

    def test_equal_no_float_to_decimal_lhs(self):
        self.assertFalse(R(Decimal("0.123456"), 5) == 0.123453)

    def test_equal_yes_integer_other_rhs(self):
        self.assertTrue(1 == R(1.000001, 5))

    def test_equal_yes_integer_lhs(self):
        self.assertTrue(R(1.000001, 5) == 1)

    def test_equal_no_integer_rhs(self):
        self.assertFalse(1 == R(1.000009, 5))

    def test_equal_no_integer_lhs(self):
        self.assertFalse(R(1.000009, 5) == 1)

    def test_equal_integer_zero_precision(self):
        self.assertTrue(1 == R(1.000001, 0))

    def test_equal_yes_negative_precision(self):
        self.assertTrue(149.123 == R(101.123, -2))

    def test_equal_no_negative_precision(self):
        self.assertFalse(149.123 == R(150.001, -2))

