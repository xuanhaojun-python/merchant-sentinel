import pytest
from pages.convert_page import ConvertPage


@pytest.mark.smoke
@pytest.mark.convert
def test_convert(logged_in_page):
    convert = ConvertPage(logged_in_page)
    convert.goto()

    print("\n[Convert] Submit 按钮可见")
    assert convert.is_page_loaded()

    print("[Convert] Sell 区域可见")
    assert convert.is_sell_section_visible()

    print("[Convert] Buy 区域可见")
    assert convert.is_buy_section_visible()

    print("[Convert] Available Balance 可见")
    assert convert.is_available_balance_visible()

    print("[Convert] 价格提示说明可见")
    assert convert.is_notice_visible()
