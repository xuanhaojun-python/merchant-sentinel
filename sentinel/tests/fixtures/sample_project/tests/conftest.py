import os
import pytest


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    rep = outcome.get_result()
    run_dir = os.getenv("MS_RUN_DIR")
    if rep.when == "call" and rep.failed and run_dir:
        shots = os.path.join(run_dir, "screenshots")
        os.makedirs(shots, exist_ok=True)
        with open(os.path.join(shots, f"{item.name}.png"), "wb") as f:
            f.write(b"\x89PNG\r\n\x1a\n")
