from playwright.sync_api import Page
from pages.base_page import BasePage


class TreasuryPage(BasePage):
    TREASURY_HEADING = "text=Treasury"
    MY_POSITIONS_BUTTON = "text=My Positions"
    SUBSCRIBE_BUTTON = "button:has-text('Subscribe')"
    RECOMMENDED_PRODUCTS = "text=Recommended Products"
    TABLE_HEADER = "table.el-table__header"
    PRODUCT_NAME_COL = "th:has-text('Product Name')"
    APR_COL = "th:has-text('Reference APR')"
    TERM_COL = "th:has-text('Term')"
    MIN_AMOUNT_COL = "th:has-text('Minimum Amount')"

    def __init__(self, page: Page) -> None:
        super().__init__(page)

    def goto(self) -> None:
        super().goto("/treasury/index")
        self.page.wait_for_load_state("networkidle")

    def is_page_loaded(self) -> bool:
        return self.page.locator(self.RECOMMENDED_PRODUCTS).is_visible()

    def is_table_visible(self) -> bool:
        return self.page.locator(self.TABLE_HEADER).first.is_visible()

    def is_my_positions_visible(self) -> bool:
        return self.page.locator(self.MY_POSITIONS_BUTTON).first.is_visible()

    def is_subscribe_button_visible(self) -> bool:
        return self.page.locator(self.SUBSCRIBE_BUTTON).first.is_visible()

    def are_table_columns_correct(self) -> bool:
        return (
            self.page.locator(self.PRODUCT_NAME_COL).is_visible()
            and self.page.locator(self.APR_COL).is_visible()
            and self.page.locator(self.TERM_COL).is_visible()
            and self.page.locator(self.MIN_AMOUNT_COL).is_visible()
        )

    def click_my_positions(self) -> None:
        self.page.locator(self.MY_POSITIONS_BUTTON).first.click()
        self.page.wait_for_load_state("networkidle")
