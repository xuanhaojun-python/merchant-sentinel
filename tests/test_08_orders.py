import pytest
from playwright.sync_api import expect
from pages.orders_page import OrdersPage


@pytest.mark.smoke
@pytest.mark.orders
def test_orders(logged_in_page):
    orders = OrdersPage(logged_in_page)
    orders.goto()

    print("\n[Orders] 订单列表表格可见")
    expect(orders.table).to_be_visible()

    print("[Orders] 点击 Search 后表格正常")
    orders.click_search()
    expect(orders.table).to_be_visible()

    count = orders.row_count()
    if count == 0:
        pytest.skip("暂无订单数据，跳过详情检查")

    print(f"[Orders] 打开第一条订单详情（共 {count} 条）")
    orders.open_first_order_detail()
    expect(orders.detail_dialog).to_be_visible()

    print("[Orders] 详情包含 Status / Time / Type / Transaction Amount 字段")
    for label in ("Status", "Time", "Type", "Transaction Amount"):
        expect(orders.detail_field(label), f"详情缺少字段: {label}").to_be_visible()

    print("[Orders] 关闭详情弹窗")
    orders.close_detail()
    expect(orders.detail_dialog).to_be_hidden()
