"""P0 金额展示：Wallet 余额遮罩、余额汇总一致性、币种列表。只读。"""
from decimal import Decimal

import pytest
from playwright.sync_api import expect

from pages.dashboard_page import DashboardPage
from utils.money import assert_amount

CURRENCIES = ["USDC", "USDT", "USD", "EUR", "GBP"]


@pytest.mark.p0
@pytest.mark.dashboard
def test_balance_mask_toggle(logged_in_page):
    """点击 Available Balance 旁的眼睛可以在遮罩 / 明文之间切换。"""
    wallet = DashboardPage(logged_in_page)
    wallet.goto()
    logged_in_page.locator(DashboardPage.CURRENCY_ROW).first.wait_for(state="visible")
    masked = wallet.is_balance_masked()
    print(f"\n[Wallet] 当前余额{'已遮罩' if masked else '明文显示'}，点击眼睛切换")
    wallet.balance_eye.click()
    card = expect(logged_in_page.locator(".wallet .content").first)
    if masked:
        card.not_to_contain_text(DashboardPage.MASK)
    else:
        card.to_contain_text(DashboardPage.MASK)
    print("[Wallet] 再次点击恢复原状态")
    wallet.balance_eye.click()
    assert wallet.is_balance_masked() == masked


@pytest.mark.p0
@pytest.mark.dashboard
def test_total_balance_equals_currencies_plus_treasury(logged_in_page):
    """Total Balance = 各币种折合 USD 之和 + Treasury Balance（逐项按 2 位小数展示，允许每项 0.01 的舍入误差）。"""
    wallet = DashboardPage(logged_in_page)
    wallet.goto()
    wallet.show_balances()
    s = wallet.summary()
    rows = wallet.currency_rows()
    currencies_usd = sum((r["usd"] for r in rows), Decimal(0))
    print(f"\n[Wallet] Total={s['total']} Treasury={s['treasury']} 币种折合合计={currencies_usd}（{len(rows)} 个币种）")
    tolerance = Decimal("0.01") * (len(rows) + 1)
    diff = s["total"] - (currencies_usd + s["treasury"])
    assert abs(diff) <= tolerance, f"Total Balance 不等于币种合计 + Treasury：差值 {diff}（容差 {tolerance}）"
    print("[Wallet] Available / Treasury / Last-Day 均不为负")
    assert s["available"] >= 0 and s["treasury"] >= 0 and s["last_day"] >= 0, s


@pytest.mark.p0
@pytest.mark.dashboard
def test_currency_rows_and_usd_equivalent(logged_in_page):
    """币种列表包含 5 个币种；USD 行无折算；稳定币折算值与余额基本一致（偏差 < 5%）。"""
    wallet = DashboardPage(logged_in_page)
    wallet.goto()
    wallet.show_balances()
    rows = {r["currency"]: r for r in wallet.currency_rows()}
    print(f"\n[Wallet] 币种：{list(rows)}")
    assert list(rows) == CURRENCIES
    assert_amount(rows["USD"]["usd"], rows["USD"]["amount"], 2)
    for ccy in ("USDC", "USDT"):
        r = rows[ccy]
        if r["amount"]:
            ratio = r["usd"] / r["amount"]
            print(f"[Wallet] {ccy} 折算比例 {ratio:.4f}")
            assert Decimal("0.95") < ratio < Decimal("1.05"), f"{ccy} 折算 USD 比例异常：{ratio}"


@pytest.mark.p0
@pytest.mark.dashboard
def test_currency_row_actions(logged_in_page):
    """币种行 ··· 菜单包含 Deposit / Withdraw / Detail。"""
    wallet = DashboardPage(logged_in_page)
    wallet.goto()
    menu = wallet.open_row_actions("USDT")
    print("\n[Wallet] USDT 行操作菜单：", menu.inner_text().split())
    for item in ("Deposit", "Withdraw", "Detail"):
        expect(menu.get_by_text(item, exact=True)).to_be_visible()
    logged_in_page.keyboard.press("Escape")
