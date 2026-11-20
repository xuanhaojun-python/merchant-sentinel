"""P1 交易查询：筛选项、按条件筛选、重置、分页、详情字段、按交易号查询。只读。"""
from decimal import Decimal

import pytest
from playwright.sync_api import expect

from pages.transaction_page import TransactionPage
from utils.money import assert_amount


@pytest.fixture
def tx(logged_in_page):
    t = TransactionPage(logged_in_page)
    t.goto()
    t.row_count(timeout=30000)
    return t


@pytest.mark.p1
@pytest.mark.transaction
@pytest.mark.parametrize("name,expected", [("Currency", TransactionPage.CURRENCIES), ("Type", TransactionPage.TYPES),
                                           ("Status", TransactionPage.STATUSES)])
def test_filter_options(tx, name, expected):
    opts = tx.filter_options(name)
    print(f"\n[Transaction] {name} 选项：{opts}")
    assert opts == expected


@pytest.mark.p1
@pytest.mark.transaction
@pytest.mark.parametrize("name,value,field", [("Type", "Withdraw", "type"), ("Type", "Deposit", "type"),
                                              ("Status", "Succeeded", "status")])
def test_filter_results_match(tx, name, value, field):
    tx.choose(name, value)
    tx.search_and_wait()
    rows = tx.rows()
    print(f"\n[Transaction] {name}={value} → 本页 {len(rows)} 条，{tx.total_text().splitlines()[0] if rows else '无数据'}")
    if not rows:
        pytest.skip(f"账号下没有 {name}={value} 的交易")
    bad = [r for r in rows if r[field] != value]
    assert not bad, f"筛选 {name}={value} 结果中混入其它记录：{bad[:3]}"


@pytest.mark.p1
@pytest.mark.transaction
def test_filter_by_currency(tx):
    tx.choose("Currency", "USDT")
    tx.search_and_wait()
    rows = tx.rows()
    print(f"\n[Transaction] Currency=USDT → 本页 {len(rows)} 条")
    assert rows
    bad = [r for r in rows if "USDT" not in r["amount"]]
    assert not bad, f"金额中不含 USDT：{bad[:3]}"


@pytest.mark.p1
@pytest.mark.transaction
def test_amount_sign_matches_type(tx):
    """Withdraw 为负数，Deposit 为正数。"""
    rows = tx.rows()
    for r in rows:
        if r["type"] == "Withdraw":
            assert r["amount"].startswith("-"), r
        elif r["type"] == "Deposit":
            assert r["amount"].startswith("+"), r
    print(f"\n[Transaction] 本页 {len(rows)} 条的金额符号与类型一致")


@pytest.mark.p1
@pytest.mark.transaction
def test_reset_clears_filters(tx):
    tx.choose("Type", "Withdraw")
    tx.choose("Status", "Succeeded")
    print(f"\n[Transaction] 选择后：Type={tx.filter_value('Type')} Status={tx.filter_value('Status')}")
    tx.click_reset()
    tx.page.wait_for_timeout(1500)
    assert tx.filter_value("Type") in ("", "Type") and tx.filter_value("Status") in ("", "Status")


@pytest.mark.p1
@pytest.mark.transaction
def test_pagination(tx):
    first_page = [r["id"] for r in tx.rows()]
    print(f"\n[Transaction] 第 1 页 {len(first_page)} 条，分页：{tx.total_text().replace(chr(10), ' ')}")
    assert len(first_page) == 10
    tx.next_page.click()
    tx.wait_table_loaded()
    second_page = [r["id"] for r in tx.rows()]
    print(f"[Transaction] 第 2 页首条 {second_page[0]}")
    assert second_page and not set(first_page) & set(second_page)


@pytest.mark.p1
@pytest.mark.transaction
def test_withdraw_detail_amounts(tx):
    """提现详情：金额 = 手续费 + 到账金额；完整交易号与列表中的缩略交易号一致。"""
    tx.choose("Type", "Withdraw")
    tx.choose("Status", "Succeeded")
    tx.search_and_wait()
    rows = tx.rows()
    if not rows:
        pytest.skip("没有成功的提现记录")
    short = rows[0]["id"]
    dialog = tx.open_detail(0)
    f = TransactionPage.detail_fields(dialog)
    print(f"\n[Transaction] 详情：{ {k: f.get(k) for k in ('title', 'amount', 'Withdrawal Fee', 'Receive amount', 'Transaction ID', 'Status')} }")
    amount = abs(TransactionPage.amount_of(f["amount"])[0])
    if "Withdrawal Fee" in f and "Receive amount" in f:
        fee = TransactionPage.amount_of(f["Withdrawal Fee"])[0]
        receive = TransactionPage.amount_of(f["Receive amount"])[0]
        assert_amount(fee + receive, amount, 6)
    head, tail = short.split("...")
    assert f["Transaction ID"].startswith(head) and f["Transaction ID"].endswith(tail), (short, f["Transaction ID"])
    assert f["Status"] == "Succeeded"
    tx.close_detail(dialog)


@pytest.mark.p1
@pytest.mark.transaction
def test_search_by_transaction_id(tx):
    dialog = tx.open_detail(0)
    full_id = TransactionPage.detail_fields(dialog)["Transaction ID"]
    tx.close_detail(dialog)
    print(f"\n[Transaction] 按交易号 {full_id} 查询")
    tx.transaction_id_input.fill(full_id)
    tx.search_and_wait()
    rows = tx.rows()
    assert len(rows) == 1, rows
    head, tail = rows[0]["id"].split("...")
    assert full_id.startswith(head) and full_id.endswith(tail)
