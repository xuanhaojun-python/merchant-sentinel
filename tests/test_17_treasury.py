"""P2 Treasury：推荐产品列表、产品详情、我的持仓。只读，不点击 Subscribe / Redeem。"""
import re

import pytest
from playwright.sync_api import expect

from pages.treasury_page import TreasuryPage


@pytest.mark.p2
@pytest.mark.treasury
def test_recommended_products_fields(logged_in_page):
    t = TreasuryPage(logged_in_page)
    t.goto()
    rows = t.product_rows()
    print(f"\n[Treasury] 推荐产品 {len(rows)} 个：{[r[0] for r in rows]}")
    assert rows
    for r in rows:
        assert re.fullmatch(r"\d+(\.\d+)?%( ~ \d+(\.\d+)?%)?", r[1]), f"APR 格式异常：{r}"
        assert re.fullmatch(r"\d+ Day|None", r[2]), f"期限格式异常：{r}"
        assert re.fullmatch(r"[\d,.]+ USDT", r[3]), f"最低金额格式异常：{r}"


@pytest.mark.p2
@pytest.mark.treasury
def test_product_detail_opens(logged_in_page):
    t = TreasuryPage(logged_in_page)
    t.goto()
    t.product_rows()
    print("\n[Treasury] 点击第一个产品的 Detail → 进入产品详情页")
    t.open_first_detail()
    expect(logged_in_page.get_by_text("Back", exact=True).first).to_be_visible()


@pytest.mark.p2
@pytest.mark.treasury
def test_my_positions_page(logged_in_page):
    t = TreasuryPage(logged_in_page)
    t.goto()
    print("\n[Treasury] 点击 My Positions → 进入持仓页")
    t.my_positions_button.click()
    logged_in_page.wait_for_url(f"**{TreasuryPage.HOLDING_PATH}")
    for col in TreasuryPage.HOLDING_COLUMNS:
        expect(t.column(col)).to_be_visible()
    for tab in ("Positions", "Transaction History"):
        expect(logged_in_page.get_by_text(tab, exact=True).first).to_be_visible()
