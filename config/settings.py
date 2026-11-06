import os
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

    @classmethod
    def require_credentials(cls) -> None:
        if not cls.email or not cls.password:
            raise RuntimeError(
                "未配置登录账号：请设置环境变量 MS_EMAIL / MS_PASSWORD，"
                "或在 config/config.local.yaml 中填写 credentials。"
            )


settings = Settings()
