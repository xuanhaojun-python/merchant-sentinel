import pytest
from playwright.sync_api import expect
from pages.treasury_page import TreasuryPage


@pytest.mark.smoke
@pytest.mark.treasury
def test_treasury(logged_in_page):
    treasury = TreasuryPage(logged_in_page)
    treasury.goto()

    print("\n[Treasury] Recommended Products 可见")
    expect(treasury.recommended_products).to_be_visible()

    print("[Treasury] 产品列表表格可见")
    expect(treasury.table_header).to_be_visible()

    print("[Treasury] 表格列正确（Product Name / APR / Term / Minimum Amount）")
    for name in TreasuryPage.TABLE_COLUMNS:
        expect(treasury.column(name), f"缺少列: {name}").to_be_visible()

    print("[Treasury] My Positions 按钮可见")
    expect(treasury.my_positions_button).to_be_visible()

    print("[Treasury] Subscribe 按钮可见")
    expect(treasury.subscribe_button).to_be_visible()
