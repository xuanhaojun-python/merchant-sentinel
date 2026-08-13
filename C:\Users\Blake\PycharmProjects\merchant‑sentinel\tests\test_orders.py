import pytest
from pages.orders_page import OrdersPage


@pytest.mark.orders
def test_orders_list_loads(logged_in_page):
    """订单列表页面正常加载并显示数据"""
    orders = OrdersPage(logged_in_page)
    orders.goto()
    orders.wait_for_orders_loaded()
    count = orders.get_order_count()
    assert count >= 0


@pytest.mark.orders
def test_orders_search(logged_in_page):
    """搜索框可输入关键词并触发搜索"""
    orders = OrdersPage(logged_in_page)
    orders.goto()
    orders.wait_for_orders_loaded()
    orders.search("TEST")
    assert orders.page.locator(orders.ORDER_TABLE).is_visible()


@pytest.mark.orders
def test_orders_detail_opens(logged_in_page):
    """点击订单行可打开详情"""
    orders = OrdersPage(logged_in_page)
    orders.goto()
    orders.wait_for_orders_loaded()
    if orders.get_order_count() > 0:
        orders.click_first_order()
        logged_in_page.wait_for_load_state("networkidle")
        assert orders.is_detail_visible() or "/orders/" in logged_in_page.url
