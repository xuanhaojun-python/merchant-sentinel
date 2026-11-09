import os
import time

import pytest


@pytest.mark.smoke
def test_pass():
    """总是通过"""
    print("\n[Sample] 第一步")
    print("[Sample] 第二步")
    print("普通输出不算步骤")


def test_fail():
    print("\n[Sample] 准备失败")
    assert 1 == 2, "故意失败"


def test_skip():
    pytest.skip("故意跳过")


def test_env():
    print(f"\n[Env] base_url={os.getenv('MS_BASE_URL')}")
    assert os.getenv("MS_BASE_URL") == "https://example.test"


@pytest.mark.slow
def test_slow():
    time.sleep(60)
