import pytest
from playwright.sync_api import expect
from pages.transaction_page import TransactionPage


@pytest.mark.smoke
@pytest.mark.transaction
def test_transaction(logged_in_page):
    tx = TransactionPage(logged_in_page)
    tx.goto()

    print("\n[Transaction] Search 按钮可见")
    expect(tx.search_button).to_be_visible()

    print("[Transaction] 列表表格可见")
    expect(tx.table).to_be_visible()

    print("[Transaction] 点击 Search 后表格正常")
    tx.click_search()
    expect(tx.table).to_be_visible()

    print("[Transaction] 点击 Reset 后页面正常")
    tx.click_reset()
    expect(tx.search_button).to_be_visible()
