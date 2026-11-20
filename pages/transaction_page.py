from playwright.sync_api import Locator, TimeoutError as PlaywrightTimeoutError
from pages.base_page import BasePage
from utils.money import parse_amount


class TransactionPage(BasePage):
    PATH = "/transaction"
    SEARCH_BUTTON = "button:has-text('Search')"
    RESET_BUTTON = "button:has-text('Reset')"
    EXPORT_BUTTON = "button:has-text('Export')"
    INPUT_BOX = ".el-input"
    ROW_ACTION_ICON = ".icon-box"
    DETAIL_CLOSE = ".el-dialog__header .close-icon"
    TABLE_ROW = "table.el-table__body tbody tr"

    @property
    def search_button(self) -> Locator:
        return self.page.locator(self.SEARCH_BUTTON).first

    @property
    def reset_button(self) -> Locator:
        return self.page.locator(self.RESET_BUTTON).first

    @property
    def export_button(self) -> Locator:
        return self.page.locator(self.EXPORT_BUTTON).first

    @property
    def table(self) -> Locator:
        return self.page.locator(self.TABLE_HEADER).first

    def row_count(self, timeout: int = 10000) -> int:
        """等待数据行渲染后返回行数；超时仍无数据行且显示"无数据"提示则返回 0。

        注意：Search 后表格重新加载期间会短暂出现空状态，因此优先等待数据行，而不是二者取先。
        """
        rows = self.page.locator(self.TABLE_ROW)
        try:
            rows.first.wait_for(state="visible", timeout=timeout)
        except PlaywrightTimeoutError:
            self.page.locator(self.TABLE_EMPTY).first.wait_for(state="visible")
            return 0
        return rows.count()

    def click_search(self) -> None:
        self.search_button.click()

    def click_reset(self) -> None:
        self.reset_button.click()

    # ── 筛选 / 列表 / 详情（2026-11-19 SIT 实测）──
    FILTERS = {"Currency": 0, "Type": 1, "Status": 2}
    TYPES = ["Withdraw", "Deposit", "Funds In", "Adjustment", "Conversion", "Refund", "Address Pre-Check", "Reward", "Plan Purchase"]
    STATUSES = ["Failed", "Processing", "Succeeded", "Action Required"]
    CURRENCIES = ["USDC", "USDT", "USD", "EUR", "GBP"]

    def _filter(self, name: str) -> Locator:
        return self.page.locator(self.SELECT_BOX).nth(self.FILTERS[name]).locator(self.SELECT_TRIGGER).first

    def filter_options(self, name: str) -> list[str]:
        self._filter(name).click()
        items = self.page.locator(self.DROPDOWN_ITEM)
        items.first.wait_for(state="visible")
        opts = [t.strip() for t in items.all_inner_texts()]
        self.page.keyboard.press("Escape")
        items.first.wait_for(state="hidden")
        return opts

    def choose(self, name: str, value: str) -> None:
        self._filter(name).click()
        self.page.locator(self.DROPDOWN_ITEM).get_by_text(value, exact=True).first.click()
        self.page.keyboard.press("Escape")

    def filter_value(self, name: str) -> str:
        return self._filter(name).inner_text().strip()

    @property
    def transaction_id_input(self) -> Locator:
        return self.page.locator(self.FORM_ITEM, has_text="Transaction ID").locator(self.INPUT_BOX).locator("input").first

    def wait_table_loaded(self) -> None:
        """表格请求期间显示 el-loading-mask：先等它出现（可能一闪而过），再等它消失。"""
        mask = self.page.locator(self.TABLE_LOADING).first
        try:
            mask.wait_for(state="visible", timeout=1500)
        except PlaywrightTimeoutError:
            pass
        mask.wait_for(state="hidden", timeout=30000)
        self.page.wait_for_timeout(300)

    def search_and_wait(self) -> None:
        self.click_search()
        self.wait_table_loaded()

    def rows(self) -> list[dict]:
        """当前页数据：[{id, date, type, amount, status}]（id 是列表中的缩略形式，如 POT212...040832）。"""
        self.row_count(timeout=30000)
        out = []
        for tr in self.page.locator(self.TABLE_ROW).all():
            cells = [c.strip() for c in tr.locator("td").all_inner_texts()]
            if len(cells) >= 5 and cells[0]:
                out.append({"id": cells[0], "date": cells[1], "type": cells[2], "amount": cells[3], "status": cells[4]})
        return out

    def total_text(self) -> str:
        return self.page.locator(self.PAGINATION).first.inner_text()

    @property
    def next_page(self) -> Locator:
        return self.page.locator(self.PAGINATION).get_by_role("button", name="Next")

    def open_detail(self, index: int = 0) -> Locator:
        """点击第 index 行操作列图标 → Detail，返回详情弹窗。"""
        cell = self.page.locator(self.TABLE_ROW).nth(index).locator("td").last
        cell.locator(self.ROW_ACTION_ICON).first.click()
        menu = self.page.locator(self.DROPDOWN_MENU).first
        menu.wait_for(state="visible")
        menu.get_by_text("Detail", exact=True).click()
        dialog = self.page.get_by_role("dialog").filter(has_text="Transaction ID").first
        dialog.wait_for(state="visible")
        return dialog

    def close_detail(self, dialog: Locator) -> None:
        """详情弹窗不响应 Escape，点右上角关闭按钮。"""
        dialog.locator(self.DETAIL_CLOSE).first.click()
        dialog.wait_for(state="hidden")

    @staticmethod
    def detail_fields(dialog: Locator) -> dict[str, str]:
        """把详情弹窗中「标签\n值」的行解析为字典。"""
        lines = [l.strip() for l in dialog.inner_text().split("\n") if l.strip()]
        labels = {"Status", "Time", "Network", "Address", "Withdrawal Fee", "Receive amount", "Transaction ID",
                  "Operator", "Transaction Hash", "Amount", "Fee", "Currency"}
        out = {"title": lines[0], "amount": lines[1] if len(lines) > 1 else ""}
        for i, l in enumerate(lines[:-1]):
            if l in labels and l not in out:
                out[l] = lines[i + 1]
        return out

    @staticmethod
    def amount_of(text: str):
        return parse_amount(text)
