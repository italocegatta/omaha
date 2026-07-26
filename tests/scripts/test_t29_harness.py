"""Focused contract tests for T29 runner and inventory receipts."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from scripts import build_test_inventory as inventory
from scripts import run_full_suite as runner
from scripts import test_profile_plugin as profile_plugin
from tests.support import db as db_support

pytestmark = pytest.mark.unit


@pytest.mark.parametrize(
    ("requested", "owner", "expected"),
    [("e2e", "e2e", True), ("unit", "e2e", False), ("visual", "visual", True)],
)
def test_db_receipt_emission_is_lane_scoped(
    monkeypatch, capsys, requested: str, owner: str, expected: bool
) -> None:
    monkeypatch.setenv("T29_DB_RECEIPT_LANE", requested)
    db_support.emit_db_receipt(owner, runner.REPO_ROOT / "data" / "test_e2e.db")
    output = capsys.readouterr().out
    assert ("T29_DB_TARGET=" in output) is expected


def test_db_receipt_ownership_matrix(monkeypatch, capsys) -> None:
    paths = {
        "unit": "safe-unit",
        "integration": "safe-integration",
        "audit": "safe-audit",
        "e2e": "test_e2e.db",
        "bdd": "test_bdd.db",
        "visual": "test_visual.db",
    }
    for lane, filename in paths.items():
        monkeypatch.setenv("T29_DB_RECEIPT_LANE", lane)
        owner = (
            ("unit", "integration", "audit") if lane in {"unit", "integration", "audit"} else lane
        )
        db_support.emit_db_receipt(owner, filename)
        assert filename in capsys.readouterr().out


def test_runner_collector_env_single_lane(monkeypatch) -> None:
    monkeypatch.setenv("T29_DB_RECEIPT_LANE", "foreign")
    env = runner._lane_environment("bdd")
    assert env["T29_DB_RECEIPT_LANE"] == "bdd"


def test_runner_spawned_child_env_single_lane(monkeypatch) -> None:
    monkeypatch.setenv("T29_DB_RECEIPT_LANE", "foreign")
    env = runner._lane_environment("visual")
    assert env["T29_DB_RECEIPT_LANE"] == "visual"


def test_runner_rejects_explicit_production_db() -> None:
    with pytest.raises(RuntimeError, match="production database"):
        runner._validate_db_targets("unit", [str(runner.REPO_ROOT / "data" / "portfolio.db")])


def test_runner_accepts_lane_owned_receipts() -> None:
    runner._validate_db_targets(
        "e2e",
        [
            str(runner.REPO_ROOT / "data" / "test_e2e.db"),
            str(runner.REPO_ROOT / "data" / "test_e2e_short_ttl.db"),
        ],
    )


def test_runner_rejects_empty_receipt() -> None:
    with pytest.raises(RuntimeError, match="did not report"):
        runner._validate_db_targets("bdd", [])


@pytest.mark.parametrize(
    "lane, targets",
    [
        ("bdd", [str(runner.REPO_ROOT / "data" / "test_visual.db")]),
        ("visual", [str(runner.REPO_ROOT / "data" / "portfolio.db")]),
    ],
)
def test_runner_rejects_production_or_cross_lane_receipts(lane: str, targets: list[str]) -> None:
    with pytest.raises(RuntimeError):
        runner._validate_db_targets(lane, targets)


def test_runner_returns_first_lane_failure_after_sibling_term() -> None:
    processes = {
        "unit": SimpleNamespace(returncode=7),
        "integration": SimpleNamespace(returncode=-15),
    }
    assert runner._final_exit_code(None, True, 7, processes) == 7


def _manifest(
    nodes_by_lane: dict[str, set[str]],
    skips: tuple[str, ...] = runner.EXPECTED_SKIPS,
) -> runner.Manifest:
    nodes = frozenset().union(*nodes_by_lane.values())
    return runner.Manifest(
        nodes,
        runner._node_checksum(nodes),
        len(nodes),
        {lane: runner._node_checksum(values) for lane, values in nodes_by_lane.items()},
        skips,
    )


def test_runner_reconciliation_accepts_exact_population_and_skips() -> None:
    lanes = {
        "unit": {"tests/test_unit.py::test_one"},
        "integration": {"tests/test_integration.py::test_one"},
        "audit": {"tests/test_audit.py::test_one"},
        "e2e": {"tests/test_e2e.py::test_one"},
        "bdd": {"tests/test_bdd.py::test_one"},
        "visual": {"tests/test_visual.py::test_one"},
    }
    preflight = runner.reconcile_preflight(_manifest(lanes), lanes)
    assert preflight["ok"] is True
    assert preflight["actual_nodes"] == 6
    assert preflight["lane_mismatches"] == {}
    assert preflight["actual_skips"] == []
    assert preflight["skip_mismatch"] is False
    result = runner.reconcile_population(_manifest(lanes), lanes, set(runner.EXPECTED_SKIPS))
    assert result["ok"] is True

    large_lanes = _synthetic_1043_lanes()
    large_manifest = _manifest(large_lanes)
    large_preflight = runner.reconcile_preflight(large_manifest, large_lanes)
    assert large_preflight["ok"] is True
    assert large_preflight["actual_nodes"] == 1043
    assert large_preflight["lane_mismatches"] == {}


def _synthetic_1043_lanes() -> dict[str, set[str]]:
    nodes = [f"tests/test_manifest.py::test_node_{index}" for index in range(1043)]
    lanes: dict[str, set[str]] = {}
    for index, (lane, _) in enumerate(runner.LANES):
        lanes[lane] = set(nodes[index :: len(runner.LANES)])
    return lanes


def test_runner_reconciliation_rejects_duplicate_node_across_lanes() -> None:
    lanes = {
        "unit": {"tests/test_one.py::test_one"},
        "integration": set(),
        "audit": set(),
        "e2e": set(),
        "bdd": set(),
        "visual": set(),
    }
    actual = {**lanes, "integration": set(lanes["unit"])}
    preflight = runner.reconcile_preflight(_manifest(lanes), actual)
    assert preflight["ok"] is False
    assert preflight["duplicate_nodes"] == ["tests/test_one.py::test_one"]
    result = runner.reconcile_population(_manifest(lanes), actual, set(runner.EXPECTED_SKIPS))
    assert result["ok"] is False
    assert result["duplicate_nodes"] == ["tests/test_one.py::test_one"]


def test_runner_manifest_loader_accepts_committed_1043_population() -> None:
    manifest = runner.load_manifest()
    assert manifest.population == 1043
    assert len(manifest.nodes) == 1043
    assert manifest.skip_ids == runner.EXPECTED_SKIPS


def test_runner_manifest_loader_rejects_1026_or_missing_manifest(tmp_path) -> None:
    path = tmp_path / "AUDIT.md"
    path.write_text("- **Population:** 1,026 nodes\n", encoding="utf-8")
    with pytest.raises(RuntimeError, match="population mismatch"):
        runner.load_manifest(path)


@pytest.mark.parametrize(
    ("actual", "skips", "error_key"),
    [
        ({"tests/test_missing.py::test_missing"}, set(runner.EXPECTED_SKIPS), "unexpected_nodes"),
        (set(), set(runner.EXPECTED_SKIPS), "missing_nodes"),
        (
            {"tests/test_one.py::test_one", "tests/test_two.py::test_two"},
            set(runner.EXPECTED_SKIPS),
            "unexpected_nodes",
        ),
        ({"tests/test_one.py::test_one"}, {"tests/test_wrong.py::test_skip"}, "skip_mismatch"),
    ],
)
def test_runner_reconciliation_rejects_population_or_skip_mismatch(
    actual, skips, error_key
) -> None:
    expected = {
        "unit": {"tests/test_one.py::test_one"},
        "integration": set(),
        "audit": set(),
        "e2e": set(),
        "bdd": set(),
        "visual": set(),
    }
    actual_lanes = {
        lane: (actual if lane == "unit" else values) for lane, values in expected.items()
    }
    preflight = runner.reconcile_preflight(_manifest(expected), actual_lanes)
    if error_key == "skip_mismatch":
        assert preflight["ok"] is True
    else:
        assert preflight["ok"] is False
    result = runner.reconcile_population(_manifest(expected), actual_lanes, skips)
    assert result["ok"] is False
    assert result[error_key]


def test_runner_parent_sigterm_stays_signal_exit() -> None:
    processes = {"unit": SimpleNamespace(returncode=-15)}
    assert runner._final_exit_code(15, True, None, processes) == 143


def test_interrupted_stdout_uses_lossless_timing_outcome(tmp_path, monkeypatch) -> None:
    path = tmp_path / "node.timings"
    monkeypatch.setenv("T29_PROFILE_PATH", str(path))
    profile_plugin._TIMING_FILE = None
    report = SimpleNamespace(
        when="call",
        skipped=False,
        duration=0.125,
        outcome="passed",
        nodeid="tests/test_interrupted.py::test_node[param:exact]",
    )
    profile_plugin.pytest_runtest_logreport(report)
    profile_plugin._TIMING_FILE.close()
    profile_plugin._TIMING_FILE = None

    node = report.nodeid
    collection = runner._collection(
        "tests/test_interrupted.py::test_node[param:exact] PASSED\n",
        path.read_text(),
    )
    assert collection["nodes"] == [node]
    assert collection["outcomes"] == {node: "PASSED"}
    assert collection["terminal_outcomes"] == {node: "PASSED"}
    assert f"PASSED {node}" in path.read_text()


def test_setup_skip_timing_record_preserves_skip_identity(tmp_path, monkeypatch) -> None:
    path = tmp_path / "skip.timings"
    monkeypatch.setenv("T29_PROFILE_PATH", str(path))
    profile_plugin._TIMING_FILE = None
    node = "tests/test_dockerfile.py::test_docker_build_pro_image_succeeds"
    profile_plugin.pytest_runtest_logreport(
        SimpleNamespace(
            when="setup",
            skipped=True,
            duration=0.001,
            outcome="skipped",
            nodeid=node,
        )
    )
    profile_plugin._TIMING_FILE.close()
    profile_plugin._TIMING_FILE = None

    collection = runner._collection("", path.read_text())
    assert collection["skipped"] == [node]
    assert collection["outcomes"] == {node: "SKIPPED"}


def test_unbroken_terminal_line_remains_diagnostic() -> None:
    node = "tests/test_terminal.py::test_complete"
    collection = runner._collection(f"{node} PASSED\n")
    assert collection["nodes"] == []
    assert collection["terminal_outcomes"] == {node: "PASSED"}


def test_inventory_uses_only_six_stamp_timing_files(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(inventory, "ROOT", tmp_path)
    report_dir = tmp_path / "reports" / "test-profile"
    report_dir.mkdir(parents=True)
    nodes = ["tests/test_example.py::test_one", "tests/bdd/test_scenarios.py::test_two"]
    audit = tmp_path / "tests" / "AUDIT.md"
    audit.parent.mkdir()
    audit.write_text("\n".join(f"| `{node}` |" for node in nodes) + "\n")
    monkeypatch.setattr(inventory, "baseline_nodes", lambda: set(nodes))
    for stamp in ("one", "two", "three"):
        for lane in inventory.LANES:
            path = report_dir / f"{stamp}-{lane}.timings"
            node = nodes[0] if lane == "unit" else nodes[1] if lane == "bdd" else None
            path.write_text(
                f"T29_PROFILE 0.100000000s call {node}\n" if node else "",
            )
    assert inventory.profile_nodes("one") == {
        nodes[0]: 0.1,
        nodes[1]: 0.1,
    }


def test_inventory_rejects_missing_timing_file(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(inventory, "ROOT", tmp_path)
    report_dir = tmp_path / "reports" / "test-profile"
    report_dir.mkdir(parents=True)
    with pytest.raises(SystemExit, match="missing timing files"):
        inventory.profile_nodes("stamp")


def test_inventory_rejects_duplicate_normalized_node(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(inventory, "ROOT", tmp_path)
    report_dir = tmp_path / "reports" / "test-profile"
    report_dir.mkdir(parents=True)
    audit = tmp_path / "tests" / "AUDIT.md"
    audit.parent.mkdir()
    audit.write_text("| `tests/test_example.py::test_one` |\n")
    monkeypatch.setattr(inventory, "baseline_nodes", lambda: {"tests/test_example.py::test_one"})
    for lane in inventory.LANES:
        (report_dir / f"stamp-{lane}.timings").write_text(
            "T29_PROFILE 0.100000000s call tests/test_example.py::test_one\n"
        )
    with pytest.raises(SystemExit, match="duplicate timing"):
        inventory.profile_nodes("stamp")


def test_inventory_rejects_unexpected_node(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(inventory, "ROOT", tmp_path)
    report_dir = tmp_path / "reports" / "test-profile"
    report_dir.mkdir(parents=True)
    audit = tmp_path / "tests" / "AUDIT.md"
    audit.parent.mkdir()
    audit.write_text("| `tests/test_example.py::test_one` |\n")
    monkeypatch.setattr(inventory, "baseline_nodes", lambda: {"tests/test_example.py::test_one"})
    for lane in inventory.LANES:
        node = "tests/test_example.py::test_one" if lane == "unit" else None
        (report_dir / f"stamp-{lane}.timings").write_text(
            f"T29_PROFILE 0.100000000s call {node}\n" if node else ""
        )
    (report_dir / "stamp-bdd.timings").write_text(
        "T29_PROFILE 0.100000000s call tests/test_example.py::test_other\n"
    )
    with pytest.raises(SystemExit, match="profile node mismatch"):
        inventory.profile_nodes("stamp")


def test_inventory_builds_valid_1026_node_three_run_fixture(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(inventory, "ROOT", tmp_path)
    nodes = {f"tests/test_generated.py::test_node_{index}" for index in range(1044)}
    monkeypatch.setattr(inventory, "baseline_nodes", lambda: nodes)
    report_dir = tmp_path / "reports" / "test-profile"
    report_dir.mkdir(parents=True)
    for stamp in ("one", "two", "three"):
        for lane_index, lane in enumerate(inventory.LANES):
            lane_nodes = sorted(nodes)[lane_index :: len(inventory.LANES)]
            (report_dir / f"{stamp}-{lane}.timings").write_text(
                "".join(f"T29_PROFILE 0.100000000s call {node}\n" for node in lane_nodes)
            )
    assert inventory.build(["one", "two", "three"]).count("| `tests/") == 1044
