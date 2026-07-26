"""Focused tests for T29 runtime receipt capture."""

from __future__ import annotations

import os
import subprocess

import pytest
import run_full_suite as runner


@pytest.mark.parametrize("lane, task", runner.LANES)
def test_runtime_child_command_and_environment_capture_receipts(
    monkeypatch, tmp_path, lane: str, task: str
) -> None:
    monkeypatch.setenv("T29_DB_RECEIPT_LANE", "foreign")
    timing_path = tmp_path / f"{lane}.timings"
    env = runner._lane_environment(lane)
    env["T29_PROFILE_PATH"] = str(timing_path)
    command = runner._runtime_child_command(task)

    assert env["T29_DB_RECEIPT_LANE"] == lane
    assert env["T29_PROFILE_PATH"] == str(timing_path)
    assert "-s" in command
    assert command[-2:] == ["-p", "test_profile_plugin"]


def test_runtime_logs_parse_dynamic_and_fixed_db_receipts() -> None:
    dynamic = "/tmp/omaha-conftest-safe-example/portfolio.db"
    logs = {
        "unit": f"T29_DB_TARGET={dynamic}\n",
        "integration": f"T29_DB_TARGET={dynamic}\n",
        "audit": f"T29_DB_TARGET={dynamic}\n",
        "e2e": "T29_DB_TARGET=data/test_e2e.db\nT29_DB_TARGET=data/test_e2e_short_ttl.db\n",
        "bdd": "T29_DB_TARGET=data/test_bdd.db\n",
        "visual": "T29_DB_TARGET=data/test_visual.db\n",
    }

    for lane, output in logs.items():
        runner._validate_db_targets(lane, runner.DB_RE.findall(output))


def test_s_flag_exposes_receipt_output(tmp_path) -> None:
    test_file = tmp_path / "test_receipt.py"
    test_file.write_text("def test_receipt(): print('T29_DB_TARGET=visible')\n", encoding="utf-8")
    base = [os.fspath(test_file), "-q"]

    captured = subprocess.run(["uv", "run", "pytest", *base], capture_output=True, text=True)
    visible = subprocess.run(["uv", "run", "pytest", *base, "-s"], capture_output=True, text=True)

    assert "T29_DB_TARGET=visible" not in captured.stdout
    assert "T29_DB_TARGET=visible" in visible.stdout
