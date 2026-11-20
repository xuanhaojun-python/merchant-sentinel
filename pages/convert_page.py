import re
from decimal import Decimal

from playwright.sync_api import Locator
from pages.base_page import BasePage
from utils.money import parse_amount


class ConvertPage(BasePage):
    PATH = "/convert"
    SUBMIT_BUTTON = "button:has-text('Submit')"
    SELL_LABEL = "text=Sell"
    BUY_LABEL = "text=Buy"
    AVAILABLE_LABEL = "text=Available Balance"
    NOTICE_BANNER = "text=Please note that this final convert"
    AMOUNT_BLOCK = ".sell-info"
    AMOUNT_INPUT = "input.el-input__inner"
    MAX_BUTTON = ".max-text"
    QUOTE_COUNTDOWN = ".transform-right .count-down"
    AVAILABLE_VALUE = ".ava-balance .value"
    QUOTE_PARTS = ".transform-right span"
    SELL_AMOUNT_INPUT = "input[placeholder^='Min:']"

    @property
    def submit_button(self) -> Locator:
        return self.page.locator(self.SUBMIT_BUTTON).first

    @property
    def sell_section(self) -> Locator:
        return self.page.locator(self.SELL_LABEL).first

    @property
    def buy_section(self) -> Locator:
        return self.page.locator(self.BUY_LABEL).first

    @property
    def available_balance(self) -> Locator:
        return self.page.locator(self.AVAILABLE_LABEL).first

    @property
    def notice_banner(self) -> Locator:
        return self.page.locator(self.NOTICE_BANNER).first

    def fill_sell_amount(self, amount: str) -> None:
        self.wait_for_element(self.SELL_AMOUNT_INPUT).fill(amount)

    # ── 报价区（2026-11-19 SIT 实测）──
    MSG_MIN_AMOUNT = "Please note, the minimum exchange amount is 1.000000 USDT. Adjust accordingly."
    MSG_MAX_AMOUNT = "Please note, the maximum exchange amount is 2,000,000.000000 USDT. Adjust accordingly."

    @property
    def sell_input(self) -> Locator:
        return self.page.locator(self.SELL_AMOUNT_INPUT).first

    @property
    def buy_input(self) -> Locator:
        return self.page.locator(self.AMOUNT_BLOCK).nth(1).locator(self.AMOUNT_INPUT).first

    @property
    def max_button(self) -> Locator:
        return self.page.locator(self.MAX_BUTTON).first

    @property
    def countdown(self) -> Locator:
        return self.page.locator(self.QUOTE_COUNTDOWN).first

    def field_error(self) -> Locator:
        return self.page.locator(self.FIELD_ERROR_VISIBLE).first

    def available(self) -> tuple[Decimal, str]:
        """余额接口返回前显示 "undefined USDT"，等到数字出现再读。"""
        value = self.page.locator(self.AVAILABLE_VALUE).first
        value.wait_for(state="visible")
        self.page.wait_for_function("e => /\\d/.test(e.innerText)", arg=value.element_handle())
        return parse_amount(value.inner_text())

    def quote(self) -> tuple[Decimal, str]:
        """报价「1 USDT → 0.987901 USD」：返回 (汇率, 买入币种)。"""
        spans = self.page.locator(self.QUOTE_PARTS).all_inner_texts()
        rate, ccy = parse_amount(spans[1])
        return rate, ccy

    def countdown_seconds(self) -> int:
        return int(re.sub(r"\D", "", self.countdown.inner_text()) or 0)

    def _select(self, idx: int) -> Locator:
        return self.page.locator(self.AMOUNT_BLOCK).nth(idx).locator(self.SELECT_TRIGGER).first

    def options(self, idx: int) -> dict[str, Decimal]:
        """idx=0 卖出币种，1 买入币种；返回 {币种: 余额}。"""
        self._select(idx).click()
        items = self.page.locator(self.DROPDOWN_ITEM)
        items.first.wait_for(state="visible")
        out = {}
        for text in items.all_inner_texts():
            parts = [p.strip() for p in text.split("\n") if p.strip()]
            out[parts[0]] = parse_amount(parts[1])[0]
        self.page.keyboard.press("Escape")
        items.first.wait_for(state="hidden")
        return out

    def enter_sell(self, amount: str) -> None:
        self.sell_input.fill("")
        self.sell_input.type(amount, delay=30)
        self.page.wait_for_timeout(1200)

    def buy_amount(self) -> Decimal | None:
        v = self.buy_input.input_value().strip()
        return parse_amount(v)[0] if v else None
