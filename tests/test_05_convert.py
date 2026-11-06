import pytest
from playwright.sync_api import expect
from pages.convert_page import ConvertPage


@pytest.mark.smoke
@pytest.mark.convert
def test_convert(logged_in_page):
    convert = ConvertPage(logged_in_page)
    convert.goto()

    print("\n[Convert] Submit 按钮可见")
    expect(convert.submit_button).to_be_visible()

    print("[Convert] Sell 区域可见")
    expect(convert.sell_section).to_be_visible()

    print("[Convert] Buy 区域可见")
    expect(convert.buy_section).to_be_visible()

    print("[Convert] Available Balance 可见")
    expect(convert.available_balance).to_be_visible()

    print("[Convert] 价格提示说明可见")
    expect(convert.notice_banner).to_be_visible()
