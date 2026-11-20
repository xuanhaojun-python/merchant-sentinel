import re
from decimal import Decimal

from playwright.sync_api import Locator
from pages.base_page import BasePage
from utils.money import parse_amount


class DashboardPage(BasePage):
    PATH = "/wallet/index"
    WELCOME_HEADING = "h1"
    BALANCE_CARD = "[class*=balance]"
    DEPOSIT_BUTTON = "button:has-text('Deposit')"
    ALL_CURRENCIES = "text=All Currencies"
    BALANCE_CONTENT = ".wallet .content"
    ROW_ACTION_TRIGGER = "svg, .el-dropdown, div"
    ROW_ACTION_MENU = ".el-dropdown-menu:visible, .el-popper:visible .el-dropdown-menu"
    ACTION_DEPOSIT = ".btn-wrap button:has-text('Deposit')"
    ACTION_CONVERT = ".btn-wrap button:has-text('Convert')"
    ACTION_WITHDRAW = ".btn-wrap button:has-text('Withdraw')"

    def goto(self) -> None:
        super().goto()
        self.dismiss_dialog_if_present()

    @property
    def welcome_heading(self) -> Locator:
        return self.page.locator(self.WELCOME_HEADING).first

    @property
    def balance_card(self) -> Locator:
        return self.page.locator(self.BALANCE_CARD).first

    @property
    def deposit_button(self) -> Locator:
        return self.page.locator(self.DEPOSIT_BUTTON).first

    @property
    def currencies_section(self) -> Locator:
        return self.page.locator(self.ALL_CURRENCIES).first

    def click_action_deposit(self) -> None:
        self.page.locator(self.ACTION_DEPOSIT).click()
        self.page.wait_for_url("**/deposit/**", timeout=10000)

    def click_action_convert(self) -> None:
        self.page.locator(self.ACTION_CONVERT).click()
        self.page.wait_for_url("**/convert**", timeout=10000)

    def click_action_withdraw(self) -> None:
        self.page.locator(self.ACTION_WITHDRAW).click()
        self.page.wait_for_url("**/withdraw/**", timeout=10000)

    # ── 余额区（2026-11-19 SIT 实测：余额默认以 * * * * * 遮罩，点 Available Balance 旁的眼睛切换）──
    MASK = "* * * * *"
    CURRENCY_ROW = ".wallet tbody tr"

    @property
    def balance_eye(self) -> Locator:
        return self.page.get_by_text("Available Balance", exact=True).first.locator("svg").first

    def balance_text(self) -> str:
        return self.page.locator(self.BALANCE_CONTENT).first.inner_text()

    def is_balance_masked(self) -> bool:
        return self.MASK in self.balance_text()

    def show_balances(self) -> None:
        """余额被遮罩时点击眼睛显示，并等到数字出现。"""
        self.page.locator(self.CURRENCY_ROW).first.wait_for(state="visible")
        if self.is_balance_masked():
            self.balance_eye.click()
            self.page.wait_for_function(
                "m => !document.querySelector('.wallet .content').innerText.includes(m)", arg=self.MASK)

    def summary(self) -> dict[str, Decimal]:
        """解析余额卡片：Available / Total / Treasury / Last-Day（单位 USD）。需先 show_balances()。"""
        text = self.balance_text()
        out = {}
        for key, label in (("available", "Available Balance"), ("total", "Total Balance"),
                           ("treasury", "Treasury Balance"), ("last_day", "Last-Day Earnings")):
            # Available 下方还有一行 "Balance updated: ..."，跳过非金额行
            m = re.search(rf"{label}\s*>?\s*(?:Balance updated:[^\n]*\n)?\s*([\d,]+\.\d+)\s*\n?\s*USD", text)
            if not m:
                raise AssertionError(f"余额卡片中找不到 {label}：{text[:300]!r}")
            out[key] = parse_amount(m.group(1))[0]
        return out

    def currency_rows(self) -> list[dict]:
        """All Currencies 表格：[{currency, amount, usd}]；USD 行没有折算值，usd = amount。"""
        rows = []
        for tr in self.page.locator(self.CURRENCY_ROW).all():
            cells = [c.inner_text().strip() for c in tr.locator("td").all()]
            currency = cells[0].split("\n")[0].strip()
            parts = [p.strip() for p in cells[1].split("\n") if p.strip() and p.strip() != "≈"]
            amount = parse_amount(parts[0])[0]
            usd = parse_amount(parts[1])[0] if len(parts) > 1 and parts[1] != "USD" else amount
            rows.append({"currency": currency, "amount": amount, "usd": usd})
        return rows

    def open_row_actions(self, currency: str) -> Locator:
        """点击币种行的 ··· 并返回弹出的菜单。"""
        row = self.page.locator(self.CURRENCY_ROW).filter(has_text=currency).first
        row.locator("td").last.locator(self.ROW_ACTION_TRIGGER).first.click()
        menu = self.page.locator(self.ROW_ACTION_MENU).first
        menu.wait_for(state="visible")
        return menu
