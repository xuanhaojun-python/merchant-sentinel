import pytest
from pages.treasury_page import TreasuryPage


@pytest.mark.smoke
@pytest.mark.treasury
def test_treasury(logged_in_page):
    treasury = TreasuryPage(logged_in_page)
    treasury.goto()

    print("\n[Treasury] Recommended Products 可见")
    assert treasury.is_page_loaded()

    print("[Treasury] 产品列表表格可见")
    assert treasury.is_table_visible()

    print("[Treasury] 表格列正确（Product Name / APR / Term / Minimum Amount）")
    assert treasury.are_table_columns_correct()

    print("[Treasury] My Positions 按钮可见")
    assert treasury.is_my_positions_visible()

    print("[Treasury] Subscribe 按钮可见")
    assert treasury.is_subscribe_button_visible()
