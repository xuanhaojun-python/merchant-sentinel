import pytest
from pages.transaction_page import TransactionPage


@pytest.mark.transaction
def test_transaction_page_loads(logged_in_page):
    """Transaction 页面正常加载，Search 按钮可见"""
    tx = TransactionPage(logged_in_page)
    tx.goto()
    assert tx.is_page_loaded()


@pytest.mark.transaction
def test_transaction_table_visible(logged_in_page):
    """Transaction 页面表格可见"""
    tx = TransactionPage(logged_in_page)
    tx.goto()
    assert tx.is_table_visible()


@pytest.mark.transaction
def test_transaction_search_click(logged_in_page):
    """点击 Search 后表格仍可见"""
    tx = TransactionPage(logged_in_page)
    tx.goto()
    tx.click_search()
    assert tx.is_table_visible()


@pytest.mark.transaction
def test_transaction_reset_click(logged_in_page):
    """点击 Reset 不崩溃"""
    tx = TransactionPage(logged_in_page)
    tx.goto()
    tx.click_reset()
    assert tx.is_page_loaded()
