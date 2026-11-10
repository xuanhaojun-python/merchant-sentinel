"""用 pytester 验证收集钩子与资金保护闸。"""
import pytest

PLUGIN = ["-p", "utils.pytest_guards", "-o", "addopts=", "-p", "no:cacheprovider"]
INI = """
[pytest]
markers =
    p0: x
    p1: x
    p2: x
    fund: x
"""


@pytest.fixture
def run(pytester, monkeypatch):
    pytester.makeini(INI)

    def _run(src, allow_fund=None, *args):
        if allow_fund is None:
            monkeypatch.delenv("MS_ALLOW_FUND", raising=False)
        else:
            monkeypatch.setenv("MS_ALLOW_FUND", allow_fund)
        pytester.makepyfile(src)
        return pytester.runpytest(*PLUGIN, "-rs", *args)
    return _run


FUND_SRC = """
import pytest
from decimal import Decimal

@pytest.mark.p0
@pytest.mark.fund
def test_pay(fund_guard):
    fund_guard.check_amount(Decimal("0.5"), "USDT")
"""


def test_fund_skipped_by_default(run):
    r = run(FUND_SRC)
    r.assert_outcomes(skipped=1)
    r.stdout.fnmatch_lines(["*MS_ALLOW_FUND=1*"])


def test_fund_runs_when_allowed(run):
    run(FUND_SRC, "1").assert_outcomes(passed=1)


def test_fund_amount_over_limit(run):
    r = run("""
import pytest
from decimal import Decimal

@pytest.mark.p0
@pytest.mark.fund
def test_pay(fund_guard):
    fund_guard.check_amount(Decimal("5"), "USDT")
""", "1")
    r.assert_outcomes(failed=1)
    r.stdout.fnmatch_lines(["*超过资金用例单笔上限*"])


def test_fund_guard_requires_fund_marker(run):
    r = run("""
import pytest

@pytest.mark.p0
def test_pay(fund_guard):
    pass
""", "1")
    r.assert_outcomes(errors=1)
    r.stdout.fnmatch_lines(["*没有标记 @pytest.mark.fund*"])


def test_missing_priority_warns(run):
    r = run("""
def test_a():
    pass
""")
    r.assert_outcomes(passed=1, warnings=1)
    r.stdout.fnmatch_lines(["*test_a*缺少优先级标记*"])


def test_duplicate_priority_warns(run):
    r = run("""
import pytest

@pytest.mark.p0
@pytest.mark.p1
def test_a():
    pass
""")
    r.assert_outcomes(passed=1, warnings=1)
    r.stdout.fnmatch_lines(["*优先级标记重复*"])


def test_single_priority_no_warning(run):
    run("""
import pytest

@pytest.mark.p1
def test_a():
    pass
""").assert_outcomes(passed=1)
