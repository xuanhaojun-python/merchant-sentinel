"""TOTP 验证码生成（商户端 2FA）。"""
import time
from typing import Callable

import pyotp

PERIOD = 30


def current_code(secret: str, min_remaining: int = 5,
                 clock: Callable[[], float] = time.time,
                 sleep: Callable[[float], None] = time.sleep) -> str:
    """生成当前 TOTP。若本周期剩余不足 min_remaining 秒，则等到下一周期再生成，避免提交时过期。"""
    if not secret:
        raise ValueError("TOTP 密钥为空")
    totp = pyotp.TOTP(secret, interval=PERIOD)
    now = clock()
    remaining = PERIOD - (now % PERIOD)
    if remaining < min_remaining:
        sleep(remaining)
        now += remaining
    return totp.at(now)
