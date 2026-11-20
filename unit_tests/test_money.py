from decimal import Decimal

import pytest

from utils.money import assert_amount, parse_amount


@pytest.mark.parametrize("text, value, ccy", [
    ("2,001.553656 USDT", Decimal("2001.553656"), "USDT"),
    ("+ 0.030000 USDT", Decimal("0.030000"), "USDT"),
    ("- 2.000000 USDT", Decimal("-2.000000"), "USDT"),
    ("100,000.00", Decimal("100000.00"), None),
    ("1.0 usd", Decimal("1.0"), "USD"),
    ("  0.987834 USD ", Decimal("0.987834"), "USD"),
])
def test_parse_amount(text, value, ccy):
    assert parse_amount(text) == (value, ccy)


@pytest.mark.parametrize("text", ["", "abc", "1,00.5 USD", "- USD", "1.2.3"])
def test_parse_amount_invalid(text):
    with pytest.raises(ValueError):
        parse_amount(text)


def test_assert_amount_quantizes():
    assert_amount(Decimal("1.0049"), Decimal("1.00"), 2)


def test_assert_amount_reports_diff():
    with pytest.raises(AssertionError, match="差值 0.01"):
        assert_amount(Decimal("1.01"), Decimal("1.00"), 2)


def test_assert_amount_rejects_float():
    with pytest.raises(TypeError):
        assert_amount(1.0, Decimal("1"), 2)


def test_round_down_and_half_up():
    from decimal import Decimal as D
    from utils.money import round_down, round_half_up
    assert round_down(D("9.87911"), 2) == D("9.87")
    assert round_down(D("1876.0466"), 2) == D("1876.04")
    assert round_down(D("-0.019"), 2) == D("-0.01")
    assert round_half_up(D("0.0888"), 2) == D("0.09")
    assert round_half_up(D("0.985"), 2) == D("0.99")
