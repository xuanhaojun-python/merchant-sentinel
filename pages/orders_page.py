from playwright.sync_api import Locator
from pages.transaction_page import TransactionPage


class OrdersPage(TransactionPage):
    """订单列表（当前与 Transaction 共用 /transaction 页面，待确认独立入口）

    详情入口：每行 Action 列的「⋯」下拉菜单 → Detail，弹出详情 dialog。
    """

    ROW_ACTION = ".el-dropdown [role='button']"

    @property
    def detail_dialog(self) -> Locator:
        return self.page.get_by_role("dialog").filter(has_text="Transaction Amount")

    def open_first_order_detail(self) -> None:
        self.page.locator(self.TABLE_ROW).first.locator(self.ROW_ACTION).click()
        self.page.locator("[role='menuitem']:visible", has_text="Detail").first.click()

    def detail_field(self, label: str) -> Locator:
        return self.detail_dialog.get_by_text(label, exact=True).first

    def close_detail(self) -> None:
        self.detail_dialog.locator(".el-dialog__headerbtn, [aria-label='Close'], [class*='close']").first.click()
