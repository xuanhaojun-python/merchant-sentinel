import re

from utils.data_factory import unique_email


def test_format():
    assert re.fullmatch(r"autotest\d{17}@test\.com", unique_email("autotest", "test.com"))


def test_defaults_from_settings():
    assert unique_email().startswith("autotest")


def test_unique():
    emails = {unique_email("a", "b.c") for _ in range(50)}
    assert len(emails) == 50
