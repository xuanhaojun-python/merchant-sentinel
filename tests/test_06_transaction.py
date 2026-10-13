import pytest
from pages.transaction_page import TransactionPage


@pytest.mark.smoke
@pytest.mark.transaction
def test_transaction(logged_in_page):
    tx = TransactionPage(logged_in_page)
    tx.goto()

    print("\n[Transaction] Search 按钮可见")
    assert tx.is_page_loaded()

    print("[Transaction] 列表表格可见")
    assert tx.is_table_visible()

    print("[Transaction] 点击 Search 后表格正常")
    tx.click_search()
    assert tx.is_table_visible()

    print("[Transaction] 点击 Reset 后页面正常")
    tx.click_reset()
    assert tx.is_page_loaded()
