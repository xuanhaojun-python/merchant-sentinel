"""测试数据生成。"""
import threading
import time
from datetime import datetime

_lock = threading.Lock()
_last = ""


def unique_email(prefix: str | None = None, domain: str | None = None) -> str:
    """返回 {prefix}{yyyyMMddHHmmssSSS}@{domain}，与 SIT 现有 autotest 邮箱格式一致；同进程内保证不重复。"""
    global _last
    if prefix is None or domain is None:
        from config.settings import settings
        prefix = settings.email_prefix if prefix is None else prefix
        domain = settings.email_domain if domain is None else domain
    with _lock:
        while True:
            stamp = datetime.now().strftime("%Y%m%d%H%M%S%f")[:-3]
            if stamp != _last:
                _last = stamp
                break
            time.sleep(0.001)
    return f"{prefix}{stamp}@{domain}"
