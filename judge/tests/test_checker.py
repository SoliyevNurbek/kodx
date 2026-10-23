"""Chiqishni solishtirish testlari."""

from django.test import SimpleTestCase

from judge.checker import check_output
from judge.types import CheckerMode


class CheckerTests(SimpleTestCase):
    def test_exact_ignores_trailing_spaces_and_crlf(self) -> None:
        self.assertTrue(check_output("a b  \r\nc\r\n\r\n", "a b\nc", CheckerMode.EXACT))
        self.assertFalse(check_output("a  b\nc", "a b\nc", CheckerMode.EXACT))
        self.assertFalse(check_output("a b c", "a b\nc", CheckerMode.EXACT))

    def test_whitespace_compares_tokens(self) -> None:
        self.assertTrue(check_output("1   2\n\n3", "1 2 3\n", CheckerMode.WHITESPACE))
        self.assertFalse(check_output("1 2", "1 2 3", CheckerMode.WHITESPACE))
        self.assertFalse(check_output("1 2 4", "1 2 3", CheckerMode.WHITESPACE))

    def test_float_epsilon(self) -> None:
        self.assertTrue(check_output("3.1415927", "3.14159265", CheckerMode.FLOAT, 1e-6))
        self.assertFalse(check_output("3.14", "3.14159265", CheckerMode.FLOAT, 1e-6))
        self.assertTrue(check_output("3.14", "3.14159265", CheckerMode.FLOAT, 1e-2))
        self.assertTrue(check_output("xato 2.50", "xato 2.5", CheckerMode.FLOAT))

    def test_float_text_tokens_and_nan(self) -> None:
        self.assertFalse(check_output("xato 2.5", "XATO 2.5", CheckerMode.FLOAT))
        self.assertFalse(check_output("1", "nan", CheckerMode.FLOAT))
        self.assertFalse(check_output("1 2", "1", CheckerMode.FLOAT))
