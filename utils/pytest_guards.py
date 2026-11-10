"""pytest 插件：优先级标记检查、资金类用例保护闸、proto / TOTP fixtures。

由 tests/conftest.py 通过 `pytest_plugins` 加载。
"""
import os
import warnings
from decimal import Decimal

import pytest

PRIORITIES = ("p0", "p1", "p2")


class PriorityMarkerWarning(pytest.PytestWarning):
    """用例缺少或重复了优先级标记。"""


def _allow_fund() -> bool:
    # 每次读取环境变量（而不是读 Settings 类属性），平台注入与测试切换都能即时生效
    return os.getenv("MS_ALLOW_FUND", "").strip().lower() in ("1", "true", "yes")


def pytest_collection_modifyitems(config, items):
    skip_fund = pytest.mark.skip(reason="资金类用例未开启：设置 MS_ALLOW_FUND=1")
    allow = _allow_fund()
    for item in items:
        priorities = [p for p in PRIORITIES if item.get_closest_marker(p)]
        if len(priorities) != 1:
            problem = "缺少优先级标记" if not priorities else f"优先级标记重复（{', '.join(priorities)}）"
            warnings.warn(PriorityMarkerWarning(f"{item.nodeid}：{problem}，请标注且只标注 p0 / p1 / p2 之一"))
        if item.get_closest_marker("fund") and not allow:
            item.add_marker(skip_fund)


class FundGuard:
    def __init__(self, max_amount: Decimal) -> None:
        self.max_amount = max_amount

    def check_amount(self, amount: Decimal, currency: str) -> Decimal:
        """下单前调用：金额超过单笔上限时直接报错，防止写错金额动到大额资金。"""
        if not isinstance(amount, Decimal):
            raise TypeError("金额必须是 Decimal")
        if amount <= 0:
            raise ValueError(f"下单金额必须为正：{amount} {currency}")
        if amount > self.max_amount:
            raise ValueError(f"下单金额 {amount} {currency} 超过资金用例单笔上限 {self.max_amount}（fund.max_amount）")
        return amount


@pytest.fixture
def fund_guard(request):
    if request.node.get_closest_marker("fund") is None:
        raise pytest.UsageError(f"{request.node.nodeid} 使用了 fund_guard 但没有标记 @pytest.mark.fund")
    if not _allow_fund():  # 正常情况下已在收集阶段 skip，这里兜底
        pytest.skip("资金类用例未开启：设置 MS_ALLOW_FUND=1")
    from config.settings import settings
    return FundGuard(settings.fund_max_amount)


@pytest.fixture(scope="session")
def proto():
    from config.settings import settings
    from clients.proto_client import ProtoClient
    settings.require_proto()
    client = ProtoClient(settings.proto_base_url, settings.proto_sso_url,
                         settings.proto_username, settings.proto_password)
    yield client
    client.close()


@pytest.fixture(scope="session")
def totp():
    from config.settings import settings
    from utils.otp import current_code
    settings.require_totp()
    return lambda: current_code(settings.totp_secret)
