import pytest
from pages.orders_page import OrdersPage


@pytest.mark.smoke
@pytest.mark.orders
def test_orders(logged_in_page):
    orders = OrdersPage(logged_in_page)
    orders.goto()
    orders.wait_for_orders_loaded()

    print("\n[Orders] 订单列表表格可见")
    assert orders.page.locator(orders.ORDER_TABLE).first.is_visible()

    print("[Orders] 点击 Search 后表格正常")
    orders.search("TEST")
    assert orders.page.locator(orders.ORDER_TABLE).first.is_visible()

    count = orders.get_order_count()
    if count > 0:
        print(f"[Orders] 点击第一条订单查看详情（共 {count} 条）")
        orders.click_first_order()
        logged_in_page.wait_for_load_state("networkidle")
        assert orders.is_detail_visible() or "/transaction" in logged_in_page.url
    else:
        print("[Orders] 暂无订单数据，跳过详情检查")
