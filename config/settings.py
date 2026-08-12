import yaml
from pathlib import Path


def _load() -> dict:
    config_path = Path(__file__).parent / "config.yaml"
    with open(config_path, encoding="utf-8") as f:
        return yaml.safe_load(f)


class Settings:
    _data = _load()

    base_url: str = _data["base_url"]
    email: str = _data["credentials"]["email"]
    password: str = _data["credentials"]["password"]
    timeout_default: int = _data["timeouts"]["default"]
    timeout_navigation: int = _data["timeouts"]["navigation"]
    headless: bool = _data["browser"]["headless"]
    slow_mo: int = _data["browser"]["slow_mo"]


settings = Settings()
