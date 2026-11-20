"""金额解析与比较。所有金额计算统一使用 Decimal，禁止 float。"""
import re
from decimal import ROUND_DOWN, ROUND_HALF_UP, Decimal, InvalidOperation

# 例："2,001.553656 USDT"、"+ 0.030000 USDT"、"- 2.000000 USDT"、"1.0 USD"、"100,000.00"
_AMOUNT_RE = re.compile(r"^\s*([+-]?)\s*([\d,]+(?:\.\d+)?)\s*([A-Za-z]{2,10})?\s*$")


def parse_amount(text: str) -> tuple[Decimal, str | None]:
    """把页面上的金额文本解析为 (Decimal, 币种)。无币种时币种为 None。"""
    m = _AMOUNT_RE.match(text or "")
    if not m:
        raise ValueError(f"无法解析金额：{text!r}")
    sign, number, currency = m.groups()
    if not re.fullmatch(r"\d{1,3}(,\d{3})*(\.\d+)?|\d+(\.\d+)?", number):
        raise ValueError(f"千分位格式错误：{text!r}")
    try:
        value = Decimal(number.replace(",", ""))
    except InvalidOperation as e:  # pragma: no cover - 正则已保证格式
        raise ValueError(f"无法解析金额：{text!r}") from e
    if sign == "-":
        value = -value
    return value, currency.upper() if currency else None


def quantize(value: Decimal, places: int) -> Decimal:
    return value.quantize(Decimal(1).scaleb(-places))


def assert_amount(actual: Decimal, expected: Decimal, places: int) -> None:
    """按 places 位小数量化后比较，失败时给出两者与差值。"""
    if not isinstance(actual, Decimal) or not isinstance(expected, Decimal):
        raise TypeError("assert_amount 只接受 Decimal，避免 float 精度问题")
    a, e = quantize(actual, places), quantize(expected, places)
    assert a == e, f"金额不一致：实际 {a}，期望 {e}，差值 {a - e}（精度 {places} 位）"


def round_down(value: Decimal, places: int) -> Decimal:
    """向零截断到 places 位（Convert 买入金额的展示规则：10 × 0.987911 = 9.879 → 9.87）。"""
    return value.quantize(Decimal(1).scaleb(-places), rounding=ROUND_DOWN)


def round_half_up(value: Decimal, places: int) -> Decimal:
    return value.quantize(Decimal(1).scaleb(-places), rounding=ROUND_HALF_UP)
