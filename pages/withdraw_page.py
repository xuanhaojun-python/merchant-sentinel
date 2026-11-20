import re

from playwright.sync_api import Locator, TimeoutError as PlaywrightTimeoutError
from decimal import Decimal

from pages.base_page import BasePage
from utils.money import parse_amount


class WithdrawPage(BasePage):
    # 直接进 fiat 子路由，确保 tab 高亮
    PATH = "/withdraw/fiat"
    TWO_FA_INPUT = "input[placeholder*='Google Authenticator']"
    AMOUNT_BLOCK = ".select-origin-ccy"
    PAYMENT_NOTE = ".payment-note textarea"
    PAYMENT_NOTE_COUNTER = ".payment-note .textarea-num"
    FREE_LIMIT_TIPS = ".withdraw-tips:visible"
    STEP = ".el-step"
    AVAILABLE_TEXT = ".select-origin-ccy .amount-text"
    PACK_RATE = ".rate-info .rate-style"
    RATE_INFO = ".rate-info"
    GENIUS_PACK = ".genius-pack-select"
    TOTAL_FEE_TEXT = ".title-style span"
    FEE_HELP_ICON = ".question-filled"
    FIAT_TAB = "a[href='/withdraw/fiat']"
    CRYPTO_TAB = "a[href='/withdraw/crypto']"
    DIALOG = ".dialog-content"
    AMOUNT_INPUT = "input[placeholder^='Min:']"
    SUBMIT_BUTTON_NAME = "Withdraw Authentication"

    FIAT_URL = re.compile(r"/withdraw/fiat")
    CRYPTO_URL = re.compile(r"/withdraw/crypto")

    def goto(self) -> None:
        super().goto()
        self.fiat_tab.wait_for(state="visible")
        self._close_dialog_if_present(timeout=2000)

    def _close_dialog_if_present(self, timeout: int = 1000) -> None:
        dialog = self.page.locator(self.DIALOG).first
        try:
            dialog.wait_for(state="visible", timeout=timeout)
        except PlaywrightTimeoutError:
            return
        self.page.keyboard.press("Escape")
        dialog.wait_for(state="hidden", timeout=3000)

    @property
    def fiat_tab(self) -> Locator:
        return self.page.locator(self.FIAT_TAB).first

    @property
    def crypto_tab(self) -> Locator:
        return self.page.locator(self.CRYPTO_TAB).first

    def click_crypto_tab(self) -> None:
        self.crypto_tab.click()
        self.page.wait_for_url("**/withdraw/crypto")
        self._close_dialog_if_present()

    def click_fiat_tab(self) -> None:
        self.fiat_tab.click()
        self.page.wait_for_url("**/withdraw/fiat")
        self._close_dialog_if_present()

    # ── 下单表单 ──
    @property
    def amount_input(self) -> Locator:
        return self.page.locator(self.AMOUNT_INPUT).first

    @property
    def submit_button(self) -> Locator:
        """表单完整前为禁用状态；点击后弹出 Withdrawal Confirmation（含 2FA），不会直接下单。"""
        return self.page.get_by_role("button", name=self.SUBMIT_BUTTON_NAME)

    def select_first_beneficiary(self) -> None:
        item = self.page.locator(self.FORM_ITEM, has_text="Beneficiary Account").first
        item.locator(self.SELECT_TRIGGER).first.click()
        self.page.locator(self.DROPDOWN_ITEM).first.click()

    # ── Withdrawal Confirmation 弹窗 ──
    @property
    def confirm_dialog(self) -> Locator:
        return self.page.get_by_role("dialog").filter(has_text="Withdrawal Confirmation")

    @property
    def two_fa_input(self) -> Locator:
        return self.confirm_dialog.locator(self.TWO_FA_INPUT).first

    @property
    def confirm_button(self) -> Locator:
        return self.confirm_dialog.get_by_role("button", name="Confirm")

    @property
    def cancel_button(self) -> Locator:
        return self.confirm_dialog.get_by_role("button", name="Cancel")

    def field_error(self, scope: Locator | None = None) -> Locator:
        return (scope or self.page).locator(self.FIELD_ERROR_VISIBLE).first

    # ── Fiat 表单金额区（2026-11-19 SIT 实测）──
    MSG_MIN_AMOUNT = "Please note, the minimum withdrawal amount is 0.100000 USDT. Adjust accordingly."
    MSG_OVER_FREE_LIMIT = "Insufficient remaining limit. The excess portion will be charged at the standard rate."

    @property
    def max_button(self) -> Locator:
        return self.page.locator(self.AMOUNT_BLOCK).first.get_by_text("Max", exact=True)

    @property
    def payment_note(self) -> Locator:
        return self.page.locator(self.PAYMENT_NOTE).first

    @property
    def payment_note_counter(self) -> Locator:
        return self.page.locator(self.PAYMENT_NOTE_COUNTER).first

    @property
    def withdraw_tips(self) -> Locator:
        return self.page.locator(self.FREE_LIMIT_TIPS).first

    @property
    def fee_step(self) -> Locator:
        return self.page.locator(self.STEP, has_text="Total Fee").first

    @property
    def recipient_input(self) -> Locator:
        return self.page.locator(self.AMOUNT_BLOCK, has_text="Recipient Gets").locator("input").first

    def available_balance(self) -> Decimal:
        text = self.page.locator(self.AVAILABLE_TEXT).first.inner_text()
        return parse_amount(text.split(":", 1)[1])[0]

    def pack_rate(self) -> Decimal:
        """Genius 套餐免费额度内的汇率：「1 USDT = 1.0 USD」。"""
        text = self.page.locator(self.PACK_RATE).first.inner_text()
        return parse_amount(text.split("=", 1)[1])[0]

    def market_rate(self) -> Decimal:
        """市场参考汇率：「1 USDT ≈ 0.987901 USD」，约 15s 刷新一次。"""
        text = self.page.locator(self.RATE_INFO).first.inner_text()
        m = re.search(r"≈\s*([\d.,]+)\s*USD", text)
        assert m, f"找不到参考汇率：{text!r}"
        return parse_amount(m.group(1))[0]

    def rate_countdown(self) -> int | None:
        m = re.search(r"(\d+)s", self.page.locator(self.RATE_INFO).first.inner_text())
        return int(m.group(1)) if m else None

    def remaining_free(self) -> tuple[Decimal, Decimal]:
        """套餐免费额度：(剩余, 总额)。"""
        text = self.page.locator(self.GENIUS_PACK).first.inner_text()
        m = re.search(r"Remaining Free:\s*([\d.,]+)\s*/\s*([\d.,]+)\s*USD", text)
        assert m, f"找不到免费额度：{text!r}"
        return parse_amount(m.group(1))[0], parse_amount(m.group(2))[0]

    def total_fee(self) -> Decimal | None:
        """Total Fee；未选收款账户 / 未输入金额时显示「-」，返回 None。"""
        text = self.fee_step.locator(self.TOTAL_FEE_TEXT).first.inner_text()
        m = re.search(r"Total Fee:\s*([\d.,]+)\s*USD", text)
        return parse_amount(m.group(1))[0] if m else None

    def fee_breakdown(self) -> dict[str, Decimal]:
        """悬停 Total Fee 旁的问号，解析 Processing fee / Leptage fee。"""
        self.fee_step.locator(self.FEE_HELP_ICON).first.hover()
        tip = self.page.locator(self.POPPER_VISIBLE, has_text="Fees include").first
        tip.wait_for(state="visible")
        text = tip.inner_text()
        out = {k: parse_amount(v)[0] for k, v in re.findall(r"(\w+) fee:\s*([\d.,]+)\s*USD", text)}
        self.page.mouse.move(0, 0)
        return out

    def recipient_gets(self) -> Decimal | None:
        value = self.recipient_input.input_value().strip()
        return parse_amount(value)[0] if value else None

    def enter_amount(self, amount: str) -> None:
        """逐字输入金额并等待费用 / 到账金额重新计算（页面有防抖）。"""
        self.amount_input.fill("")
        self.amount_input.type(amount, delay=30)
        self.page.wait_for_timeout(1500)


class CryptoWithdrawPage(BasePage):
    """Withdraw → Crypto 表单。"""
    PATH = "/withdraw/crypto"
    FORM_ITEM_IN_FORM = "form .el-form-item"
    RECEIVE_INPUT = ".receive-amount-section input"
    WHITELIST_NOTICE = ".enable-whitelist-notice"
    ADDRESS_BLOCK = ".address-input"
    FEE_LABEL = ".account-tips .account-label"
    AVAILABLE_TEXT = ".max-amount"
    MSG_SELECT_WALLET_FIRST = "Please select the withdrawal wallet first"
    MSG_MAX_AMOUNT = "Please note, the maximum withdrawal amount is 10,000.000000 USDT. Adjust accordingly."

    def goto(self) -> None:
        super().goto()
        self.currency_select.wait_for(state="visible")
        WithdrawPage(self.page)._close_dialog_if_present(timeout=2000)

    def _item(self, label: str) -> Locator:
        return self.page.locator(self.FORM_ITEM_IN_FORM, has_text=label).first

    @property
    def currency_select(self) -> Locator:
        return self._item("Select Withdrawal Currency").locator(self.SELECT_TRIGGER).first

    @property
    def amount_input(self) -> Locator:
        return self._item("Enter Withdrawal Amount").locator("input").first

    @property
    def receive_input(self) -> Locator:
        return self.page.locator(self.RECEIVE_INPUT).first

    @property
    def next_button(self) -> Locator:
        return self.page.get_by_role("button", name="Next step")

    @property
    def whitelist_notice(self) -> Locator:
        return self.page.locator(self.WHITELIST_NOTICE).first

    @property
    def address_management_link(self) -> Locator:
        return self.page.locator(self.ADDRESS_BLOCK).get_by_text("Address Management", exact=True)

    @property
    def fee_text(self) -> Locator:
        return self.page.locator(self.FEE_LABEL).first

    def field_error(self) -> Locator:
        return self.page.locator(self.FIELD_ERROR_VISIBLE).first

    def currency_options(self) -> dict[str, Decimal]:
        """展开币种下拉，返回 {币种: 可用余额}。"""
        self.currency_select.click()
        items = self.page.locator(self.DROPDOWN_ITEM)
        items.first.wait_for(state="visible")
        out = {}
        for text in items.all_inner_texts():
            parts = [p.strip() for p in text.split("\n") if p.strip()]
            out[parts[0]] = parse_amount(parts[2])[0]
        self.page.keyboard.press("Escape")
        items.first.wait_for(state="hidden")
        return out

    def select_currency(self, currency: str) -> None:
        self.currency_select.click()
        self.page.locator(self.DROPDOWN_ITEM, has_text=currency).first.click()
        self.page.locator(self.AVAILABLE_TEXT, has_text=currency).first.wait_for(state="visible")

    def available_balance(self) -> Decimal:
        text = self.page.locator(self.AVAILABLE_TEXT).first.inner_text()
        return parse_amount(text.split(":", 1)[1])[0]
