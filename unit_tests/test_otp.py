import pytest

from utils.otp import current_code

# RFC 6238 附录 B 的 SHA1 种子 "12345678901234567890" 的 Base32 编码
SECRET = "GEZDGNBVGY3TQOJQGEZDGNBVGY3TQOJQ"


def test_rfc6238_vector():
    # T=59 → 94287082（8 位）；6 位取后 6 位
    assert current_code(SECRET, min_remaining=0, clock=lambda: 59) == "287082"


def test_waits_for_next_period_when_about_to_expire():
    slept = []
    # 时间 58：本周期仅剩 2 秒 → 等 2 秒，使用 T=60 的验证码
    code = current_code(SECRET, min_remaining=5, clock=lambda: 58, sleep=slept.append)
    assert slept == [2]
    assert code == current_code(SECRET, min_remaining=0, clock=lambda: 60)


def test_no_wait_when_enough_time():
    slept = []
    current_code(SECRET, clock=lambda: 31, sleep=slept.append)
    assert slept == []


def test_empty_secret():
    with pytest.raises(ValueError):
        current_code("")
