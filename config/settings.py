import os
from decimal import Decimal
from pathlib import Path

import yaml

_CONFIG_DIR = Path(__file__).parent


def _load() -> dict:
    """加载 config.yaml，若存在 config.local.yaml（不入库）则覆盖同名配置。"""
    with open(_CONFIG_DIR / "config.yaml", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    local = _CONFIG_DIR / "config.local.yaml"
    if local.exists():
        with open(local, encoding="utf-8") as f:
            for key, value in (yaml.safe_load(f) or {}).items():
                if isinstance(value, dict) and isinstance(data.get(key), dict):
                    data[key].update(value)
                else:
                    data[key] = value
    return data


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in ("1", "true", "yes")


class Settings:
    """优先级：环境变量 > config.local.yaml > config.yaml"""

    _data = _load()

    base_url: str = os.getenv("MS_BASE_URL", _data["base_url"])
    email: str = os.getenv("MS_EMAIL", _data["credentials"]["email"])
    password: str = os.getenv("MS_PASSWORD", _data["credentials"]["password"])
    timeout_default: int = _data["timeouts"]["default"]
    timeout_navigation: int = _data["timeouts"]["navigation"]
    headless: bool = _env_bool("MS_HEADLESS", _data["browser"]["headless"])
    slow_mo: int = _data["browser"]["slow_mo"]

    # 2FA（TOTP）
    totp_secret: str = os.getenv("MS_TOTP_SECRET", _data["credentials"].get("totp_secret", ""))

    # 运营后台 proto（仅作为辅助：取验证码、审批放行）
    proto_base_url: str = os.getenv("MS_PROTO_BASE_URL", _data.get("proto", {}).get("base_url", ""))
    proto_sso_url: str = os.getenv("MS_PROTO_SSO_URL", _data.get("proto", {}).get("sso_url", ""))
    proto_username: str = os.getenv("MS_PROTO_USERNAME", _data.get("proto", {}).get("username", ""))
    proto_password: str = os.getenv("MS_PROTO_PASSWORD", _data.get("proto", {}).get("password", ""))

    # 资金类用例单笔上限；是否执行由环境变量 MS_ALLOW_FUND 控制（见 utils/pytest_guards.py）
    fund_max_amount: Decimal = Decimal(str(_data.get("fund", {}).get("max_amount", "1")))

    # 测试数据
    email_domain: str = _data.get("test_data", {}).get("email_domain", "test.com")
    email_prefix: str = _data.get("test_data", {}).get("email_prefix", "autotest")

    @classmethod
    def require_credentials(cls) -> None:
        if not cls.email or not cls.password:
            raise RuntimeError(
                "未配置登录账号：请设置环境变量 MS_EMAIL / MS_PASSWORD，"
                "或在 config/config.local.yaml 中填写 credentials。"
            )

    @classmethod
    def require_totp(cls) -> None:
        if not cls.totp_secret:
            raise RuntimeError(
                "未配置 TOTP 密钥：请设置环境变量 MS_TOTP_SECRET，"
                "或在 config/config.local.yaml 中填写 credentials.totp_secret。"
            )

    @classmethod
    def require_proto(cls) -> None:
        missing = [n for n in ("proto_base_url", "proto_sso_url", "proto_username", "proto_password")
                   if not getattr(cls, n)]
        if missing:
            raise RuntimeError(
                f"未配置 proto 运营后台：缺少 {', '.join(missing)}。"
                "请在 config/config.local.yaml 的 proto 段填写，或设置环境变量 MS_PROTO_USERNAME / MS_PROTO_PASSWORD。"
            )


settings = Settings()
