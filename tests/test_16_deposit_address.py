"""P0 充值地址：币种 / 网络选项，以及地址格式与所选网络匹配（错网充值会丢币）。只读。"""
import re

import pytest
from playwright.sync_api import expect

from pages.deposit_page import DepositPage

EVM = re.compile(r"^0x[0-9a-fA-F]{40}$")
TRON = re.compile(r"^T[1-9A-HJ-NP-Za-km-z]{33}$")
SOLANA = re.compile(r"^[1-9A-HJ-NP-Za-km-z]{32,44}$")


def address_pattern(network: str) -> re.Pattern:
    if "Tron" in network:
        return TRON
    if "Solana" in network:
        return SOLANA
    return EVM  # Ethereum / BSC / OPTIMISM / BASE / ARBITRUM


@pytest.fixture
def deposit(logged_in_page):
    d = DepositPage(logged_in_page)
    d.goto()
    d.dismiss_dialog_if_present(timeout=1500)
    expect(d.deposit_address).to_be_visible()
    return d


@pytest.mark.p0
@pytest.mark.deposit
def test_crypto_currency_options(deposit):
    opts = deposit.options(0)
    print(f"\n[Deposit] 充值币种：{opts}")
    assert opts == ["USDT", "USDC"]


@pytest.mark.p0
@pytest.mark.deposit
@pytest.mark.parametrize("currency", ["USDT", "USDC"])
def test_address_matches_network(deposit, currency):
    deposit.choose(0, currency)
    networks = deposit.options(1)
    print(f"\n[Deposit] {currency} 支持网络：{networks}")
    assert networks
    for net in networks:
        deposit.choose(1, net)
        addr = deposit.address()
        print(f"[Deposit] {currency} / {net} → {addr}")
        assert address_pattern(net).match(addr), f"{net} 的充值地址格式不正确：{addr!r}"
        assert f"{currency}- {net}" in deposit.page_text() or net in deposit.page_text(), "网络提示未同步为所选网络"


@pytest.mark.p0
@pytest.mark.deposit
def test_fiat_currency_options(deposit):
    deposit.click_fiat_tab()
    deposit.page.wait_for_timeout(1500)
    opts = deposit.options(0)
    print(f"\n[Deposit] 法币充值币种：{opts}")
    assert opts == ["USD", "EUR", "GBP"]
