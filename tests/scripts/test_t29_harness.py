"""Focused contract tests for T29 runner and inventory receipts."""

from __future__ import annotations

import json
import socket
from types import SimpleNamespace

import pytest

from scripts import build_test_inventory as inventory
from scripts import run_full_suite as runner
from scripts import test_governance as governance
from scripts import test_profile_plugin as profile_plugin
from tests.support import db as db_support
from tests.support import server as server_support

pytestmark = pytest.mark.unit


def test_t33_server_does_not_accept_stale_listener_for_dead_child(monkeypatch, tmp_path) -> None:
    """A listener not owned by spawned child cannot satisfy startup readiness."""

    class DeadProcess:
        pid = 41001
        returncode = 1

        def poll(self):
            return self.returncode

        def terminate(self):
            return None

        def wait(self, timeout=None):
            del timeout
            return self.returncode

        def kill(self):
            return None

    listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listener.bind(("127.0.0.1", 0))
    listener.listen(1)
    port = listener.getsockname()[1]
    log_handle = (tmp_path / "stale-listener.log").open("w+", encoding="utf-8")
    monkeypatch.setattr(server_support.subprocess, "Popen", lambda *args, **kwargs: DeadProcess())
    monkeypatch.setattr(server_support, "uvicorn_log_file", lambda *args, **kwargs: log_handle)
    try:
        with (
            pytest.raises(RuntimeError, match="uvicorn did not start") as exc_info,
            server_support.run_test_server(
                tmp_path / "test.db",
                port,
                label="t33-stale-listener",
            ),
        ):
            pytest.fail("dead child must not yield URL backed by stale listener")
        assert "returncode=1" in str(exc_info.value)
    finally:
        listener.close()


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
    for elapsed_seconds, expected in (
        (299.999, False),
        (300.0, False),
        (300.001, True),
    ):
        assert runner._duration_exceeded(elapsed_seconds) is expected
    candidates = (
        governance.DisabledCase("tests/low.py::test_expensive", "low", 2.0),
        governance.DisabledCase("tests/normal.py::test_small", "normal", 1.0),
        governance.DisabledCase("tests/low.py::test_small", "low", 1.0),
    )
    selected = governance.select_lowest_importance_cases(303.0, candidates, ceiling_seconds=300.0)
    assert [case.nodeid for case in selected] == [
        "tests/low.py::test_expensive",
        "tests/low.py::test_small",
    ]
    assert governance.select_lowest_importance_cases(299.0, candidates, ceiling_seconds=300.0) == ()
    headroom_candidates = (
        governance.DisabledCase("tests/low.py::test_a", "low", 5.26),
        governance.DisabledCase("tests/low.py::test_b", "low", 5.26),
    )
    assert [
        case.nodeid
        for case in governance.select_lowest_importance_cases(
            300.38,
            headroom_candidates,
            ceiling_seconds=300.0,
            safety_margin_seconds=5.0,
        )
    ] == ["tests/low.py::test_a", "tests/low.py::test_b"]
    assert runner._runtime_child_command(
        "test-visual", ("tests/visual/test_snapshots.py::test_login_snapshot[mobile]",)
    )[-2:] == ["--deselect", "tests/visual/test_snapshots.py::test_login_snapshot[mobile]"]


def test_pre_run_selection_uses_current_blocking_candidates_only() -> None:
    policy = governance.load_policy()
    candidates = policy.pre_run_candidates
    preflight = {
        lane: (
            {candidate.nodeid for candidate in candidates} if lane == "unit" else set(),
            set(),
            [],
        )
        for lane, _ in runner.LANES
    }
    selected, selected_by_lane = runner._select_pre_run_cases(policy, preflight)
    assert selected
    assert set(case.nodeid for case in selected) < set(case.nodeid for case in candidates)
    assert selected_by_lane["unit"] == tuple(case.nodeid for case in selected)
    assert not set(case.nodeid for case in selected) & governance._approved_nodeids()


def test_pre_run_selection_uses_versioned_manifest_before_launch() -> None:
    policy = governance.load_policy()
    selected, selected_by_lane = runner._select_pre_run_cases(
        policy,
        {
            *[case.nodeid for case in policy.pre_run_candidates],
            *[case.nodeid for case in policy.approved_disabled],
        },
    )
    assert len(selected) == 23
    assert selected[0].nodeid.endswith("test_class_swatches_against_bg[5]")
    assert selected[-1].nodeid.endswith("test_documented_pairs_pass")
    assert selected_by_lane == {
        "unit": tuple(case.nodeid for case in selected),
    }
    assert not set(selected_by_lane["unit"]) & governance._approved_nodeids()


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

    large_lanes = _synthetic_current_lanes()
    large_manifest = _manifest(large_lanes)
    large_preflight = runner.reconcile_preflight(large_manifest, large_lanes)
    assert large_preflight["ok"] is True
    assert large_preflight["actual_nodes"] == 1032
    assert large_preflight["lane_mismatches"] == {}


def _synthetic_current_lanes() -> dict[str, set[str]]:
    nodes = [f"tests/test_manifest.py::test_node_{index}" for index in range(1032)]
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


def test_runner_manifest_loader_accepts_current_audit_snapshot(request) -> None:
    manifest = runner.load_manifest()
    assert manifest.population == 1032
    assert len(manifest.nodes) == 1032
    assert manifest.skip_ids == runner.EXPECTED_SKIPS
    assert manifest.enforce_population is False
    classifications = governance.validate_collected_items(request.session.items)
    assert len(classifications) == len(request.session.items)
    assert set(classifications.values()) <= set(governance.IMPORTANCE_LEVELS)
    assert governance.classify_node("tests/e2e/test_contract.py::test_flow") == "critical"
    audit_node = "tests/audit_integration/test_contract.py::test_audit"
    assert governance.classify_node(audit_node) == "high"
    assert governance.classify_node("tests/test_contract.py::test_unit") == "normal"
    assert governance.classify_node(governance.load_policy().approved_disabled[0].nodeid) == "low"


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


class _ControlledChild:
    def __init__(self, pid: int, returncode: int | None = None) -> None:
        self.pid = pid
        self.returncode = returncode
        self.wait_calls = 0

    def poll(self):
        return self.returncode

    def wait(self):
        self.wait_calls += 1
        return self.returncode


class _VanishedChild(_ControlledChild):
    def __init__(self, pid: int, vanish_on: str) -> None:
        super().__init__(pid)
        self.vanish_on = vanish_on
        self.poll_calls = 0

    def poll(self):
        self.poll_calls += 1
        if self.vanish_on == "poll" or self.poll_calls > 1:
            raise ProcessLookupError("child vanished")
        return None

    def wait(self):
        raise BrokenPipeError("child pipe vanished")


def _lane_entry(name: str = "unit") -> dict[str, object]:
    return runner._lane_metadata(
        name,
        f"test-{name}",
        "controlled-run",
        runner.REPO_ROOT / f"{name}.log",
        runner.REPO_ROOT / f"{name}.timings",
    )


def test_runner_vanished_child_during_signal_preserves_failure(monkeypatch) -> None:
    child = _ControlledChild(41001)
    entry = _lane_entry()
    kill_calls: list[tuple[int, int]] = []

    def killpg(pgid: int, sig: int) -> None:
        kill_calls.append((pgid, sig))
        raise ProcessLookupError("PID not found")

    monkeypatch.setattr(runner.os, "killpg", killpg)
    assert (
        runner._stop({"unit": child}, runner.signal.SIGTERM, {"unit": entry}, "fail-fast") is False
    )
    assert kill_calls == [(41001, runner.signal.SIGTERM)]
    assert entry["lifecycle_races"][0]["phase"] == "signal"
    assert runner._final_exit_code(None, False, 7, {"unit": child}) == 7


def test_runner_no_such_process_is_lifecycle_race() -> None:
    error = type("NoSuchProcess", (Exception,), {})
    assert runner._is_lifecycle_race(error("gone")) is True


def test_runner_reaps_owned_survivor(monkeypatch) -> None:
    child = _ControlledChild(41002)
    entry = _lane_entry()
    kill_calls: list[tuple[int, int]] = []

    def killpg(pgid: int, sig: int) -> None:
        kill_calls.append((pgid, sig))
        child.returncode = -9

    monkeypatch.setattr(runner.os, "killpg", killpg)
    monkeypatch.setattr(runner, "GRACE_SECONDS", 0.0)
    assert runner._reap({"unit": child}, {"unit": entry}, "timeout") is False
    assert kill_calls == [(41002, runner.signal.SIGKILL)]
    assert entry["signals"][-1]["signal"] == "SIGKILL"
    assert child.wait_calls == 1


def test_runner_vanished_child_during_wait(monkeypatch) -> None:
    child = _VanishedChild(41003, "wait")
    entry = _lane_entry()
    monkeypatch.setattr(runner, "GRACE_SECONDS", 0.0)
    monkeypatch.setattr(runner.os, "killpg", lambda pgid, sig: None)
    assert runner._reap({"unit": child}, {"unit": entry}) is False
    assert any(race["phase"] == "wait" for race in entry["lifecycle_races"])
    assert entry["cleanup_result"] == "vanished-child"


def test_runner_preserves_foreign_resource(monkeypatch) -> None:
    foreign = _ControlledChild(41005)
    calls: list[int] = []
    monkeypatch.setattr(runner.os, "killpg", lambda pgid, sig: calls.append(pgid))
    entry = _lane_entry("e2e")
    entry["owned_resource_mapping"]["process_group"].update(
        {"resource_id": foreign.pid, "classification": "owned-current-run"}
    )
    inventory = runner._canonical_resource_inventory(
        (
            {
                "resource_kind": "port",
                "resource_id": 8765,
                "owner": "other-run",
                "evidence": "foreign canonical listener",
            },
        )
    )
    assert runner._propagate_resource_inventory({"e2e": entry}, inventory) is False
    assert (
        runner._stop({"e2e": foreign}, runner.signal.SIGTERM, {"e2e": entry}, "fail-fast") is False
    )
    assert calls == []
    assert entry["cleanup_result"] == "untrusted-resource"
    assert runner._resource_cleanup_verdict({"unit": entry})[0] is False


def test_runner_preflight_inventory_ignores_harmless_host_observations() -> None:
    inventory = runner._canonical_resource_inventory(
        (
            {
                "resource_kind": "port",
                "resource_id": 8000,
                "owner": "host-service",
            },
            {
                "resource_kind": "port",
                "resource_id": 5443,
                "owner": "host-service",
            },
            {
                "resource_kind": "port",
                "resource_id": 4096,
                "owner": "opencode",
            },
            {
                "resource_kind": "path",
                "resource_id": "/tmp/pytest-of-juca/",
                "owner": "pytest",
            },
        )
    )
    observed = inventory["resources"][-4:]
    assert all(item["relevant"] is False for item in observed)
    assert all(item["classification"] == "pre-existing" for item in observed)
    assert all(item["cleanup_target"] is False for item in observed)
    assert all(item["allowlisted"] is False and item["adopted"] is False for item in observed)
    assert inventory["ok"] is True


def test_runner_preflight_inventory_records_canonical_port_collision() -> None:
    inventory = runner._canonical_resource_inventory(
        (
            {
                "resource_kind": "port",
                "resource_id": 8765,
                "owner": "foreign-run",
                "evidence": "controlled listener",
            },
        )
    )
    collision = inventory["resources"][-1]
    assert collision["relevant"] is True
    assert collision["classification"] == "foreign"
    assert inventory["ok"] is False
    assert collision["cleanup_target"] is False


def test_runner_preflight_inventory_records_preexisting_pytest_root_as_irrelevant() -> None:
    inventory = runner._canonical_resource_inventory(
        (
            {
                "resource_kind": "temporary path",
                "resource_id": "/tmp/pytest-of-juca/",
                "owner": "old-pytest",
            },
        )
    )
    root = inventory["resources"][-1]
    assert root == {
        "resource_kind": "temporary path",
        "resource_id": "/tmp/pytest-of-juca/",
        "relevant": False,
        "owner": "old-pytest",
        "evidence": "controlled observation",
        "cleanup_target": False,
        "preserved": True,
        "allowlisted": False,
        "adopted": False,
        "classification": "pre-existing",
    }


def test_runner_owned_resource_cleanup_is_trusted(monkeypatch) -> None:
    child = _ControlledChild(41008)
    entry = _lane_entry()
    entry["owned_resource_mapping"]["process_group"].update(
        {"resource_id": child.pid, "classification": "owned-current-run"}
    )
    calls: list[tuple[int, int]] = []

    def killpg(pgid: int, sig: int) -> None:
        calls.append((pgid, sig))
        child.returncode = -9

    monkeypatch.setattr(runner.os, "killpg", killpg)
    monkeypatch.setattr(runner, "GRACE_SECONDS", 0.0)
    assert runner._reap({"unit": child}, {"unit": entry}, "timeout") is False
    assert calls == [(child.pid, runner.signal.SIGKILL)]
    assert runner._resource_cleanup_verdict({"unit": entry})[0] is True


def test_runner_fail_fast_receipt_attributes_sibling_stop(monkeypatch) -> None:
    failed = _ControlledChild(41006, returncode=7)
    sibling = _ControlledChild(41007)
    entries = {"unit": _lane_entry("unit"), "integration": _lane_entry("integration")}
    calls: list[tuple[int, int]] = []

    def killpg(pgid: int, sig: int) -> None:
        calls.append((pgid, sig))
        sibling.returncode = -15

    monkeypatch.setattr(runner.os, "killpg", killpg)
    runner._stop(
        {"unit": failed, "integration": sibling},
        runner.signal.SIGTERM,
        entries,
        "fail-fast:unit",
    )
    assert calls == [(41007, runner.signal.SIGTERM)]
    assert entries["integration"]["sibling_stop_reason"] == "fail-fast:unit"
    assert runner._final_exit_code(None, True, 7, {"unit": failed, "integration": sibling}) == 7


def _patch_main_preflight(monkeypatch, tmp_path, *, launch_failure: str | None = None):
    class Policy:
        version = "controlled"
        ceiling_seconds = 300.0
        prior_known_seconds = 0.0
        safety_margin_seconds = 0.0
        approved_disabled = ()
        blocking_command = "blocking"
        expanded_command = "expanded"

    nodes = {lane: set() for lane, _ in runner.LANES}
    manifest = runner.Manifest(
        frozenset(),
        runner._node_checksum(set()),
        0,
        {lane: runner._node_checksum(set()) for lane in nodes},
        runner.EXPECTED_SKIPS,
        False,
    )
    monkeypatch.setattr(runner, "load_policy", lambda: Policy())
    monkeypatch.setattr(runner, "_preflight", lambda: None)
    monkeypatch.setattr(runner, "load_manifest", lambda: manifest)
    monkeypatch.setattr(runner, "_select_pre_run_cases", lambda policy, nodes: ((), {}))
    monkeypatch.setattr(runner, "REPORT_DIR", tmp_path)
    monkeypatch.setattr(runner.time, "strftime", lambda *args: "controlled")
    monkeypatch.setattr(runner.time, "localtime", lambda: 0)

    class Child(_ControlledChild):
        def __init__(self, pid: int) -> None:
            super().__init__(pid, returncode=None)

    children: list[Child] = []

    def popen(command, **kwargs):
        del kwargs
        lane = command[3]
        if lane == launch_failure:
            raise OSError("controlled launch failure")
        child = Child(42000 + len(children))
        children.append(child)
        return child

    monkeypatch.setattr(runner.subprocess, "Popen", popen)
    monkeypatch.setattr(
        runner.os,
        "killpg",
        lambda pgid, sig: setattr(
            next(child for child in children if child.pid == pgid), "returncode", -sig
        ),
    )
    return children


def test_runner_partial_launch_emits_all_lane_receipts(monkeypatch, tmp_path) -> None:
    _patch_main_preflight(monkeypatch, tmp_path, launch_failure="test-integration")
    assert runner.main() == 2
    receipt = json.loads(next(tmp_path.glob("controlled-run.json")).read_text())
    assert [entry["lane"] for entry in receipt["lanes"]] == [name for name, _ in runner.LANES]
    required = {
        "lane",
        "task",
        "pid",
        "pgid",
        "ports",
        "owned_resource_mapping",
        "owner_evidence",
        "started_at",
        "ended_at",
        "signal",
        "return_code",
        "cleanup_result",
        "residue_classification",
        "timeout",
    }
    assert all(required <= entry.keys() for entry in receipt["lanes"])
    failed = next(entry for entry in receipt["lanes"] if entry["lane"] == "integration")
    assert failed["pid"] is None and failed["pgid"] is None
    assert failed["launch_status"] == "failed"
    assert failed["launch_error"]
    assert failed["owned_resource_mapping"]["ports"]["resource_id"] == []
    assert failed["owned_resource_mapping"]["ports"]["classification"] == "absent"
    assert {
        lane: entry["owned_resource_mapping"]["ports"]["resource_id"]
        for lane, entry in ((item["lane"], item) for item in receipt["lanes"])
    } == {
        "unit": [],
        "integration": [],
        "audit": [],
        "e2e": [8765, 8767],
        "bdd": [8766],
        "visual": [8768],
    }


def test_runner_persists_six_placeholders_before_first_launch(monkeypatch, tmp_path) -> None:
    children = _patch_main_preflight(monkeypatch, tmp_path, launch_failure="test-unit")
    observed: list[dict[str, object]] = []
    original_popen = runner.subprocess.Popen

    def popen(command, **kwargs):
        receipt = tmp_path / "controlled-run.json"
        observed.append(json.loads(receipt.read_text()))
        return original_popen(command, **kwargs)

    monkeypatch.setattr(runner.subprocess, "Popen", popen)
    runner.main()
    assert observed
    assert [entry["lane"] for entry in observed[0]["lanes"]] == [name for name, _ in runner.LANES]
    assert all(entry["pid"] is None and entry["pgid"] is None for entry in observed[0]["lanes"])
    assert children == []


def test_runner_retains_partial_artifacts_after_lane_finalization_exception(
    monkeypatch, tmp_path
) -> None:
    _patch_main_preflight(monkeypatch, tmp_path)
    monkeypatch.setattr(runner, "_stop_deadline", lambda started: -1.0)
    original_collection = runner._collection

    def collection(output: str, timing_output: str = ""):
        if not output and not timing_output:
            raise RuntimeError("controlled finalization failure")
        return original_collection(output, timing_output)

    monkeypatch.setattr(runner, "_collection", collection)
    assert runner.main() == runner.TIMEOUT_EXIT_CODE
    receipt = json.loads((tmp_path / "controlled-run.json").read_text())
    assert len(receipt["lanes"]) == 6
    assert receipt["first_failure"] == runner.TIMEOUT_EXIT_CODE
    assert receipt["receipt_errors"]
    assert any(error["stage"] == "lane-finalization" for error in receipt["receipt_errors"])
    integration = next(entry for entry in receipt["lanes"] if entry["lane"] == "integration")
    assert integration["receipt_error"]
    assert integration["cleanup_result"] in {"untrusted-receipt", "owned-cleaned"}


def test_runner_receipt_retains_first_integration_failure_and_sibling_reason(
    monkeypatch, tmp_path
) -> None:
    _patch_main_preflight(monkeypatch, tmp_path)
    original_popen = runner.subprocess.Popen

    def popen(command, **kwargs):
        child = original_popen(command, **kwargs)
        if command[3] == "test-integration":
            child.returncode = 1
        return child

    monkeypatch.setattr(runner.subprocess, "Popen", popen)
    assert runner.main() == 1
    receipt = json.loads((tmp_path / "controlled-run.json").read_text())
    assert receipt["first_failure"] == 1
    assert receipt["first_failure_lane"] == "integration"
    integration = next(entry for entry in receipt["lanes"] if entry["lane"] == "integration")
    assert integration["return_code"] == 1
    sibling = next(entry for entry in receipt["lanes"] if entry["lane"] == "e2e")
    assert sibling["sibling_stop_reason"] == "fail-fast:integration"


def test_runner_serialization_failure_falls_back_without_losing_telemetry(tmp_path) -> None:
    payload = {
        "run_id": "controlled-run",
        "lanes": [{"lane": "integration", "return_code": 1, "sibling_stop_reason": "fail-fast"}],
        "receipt_errors": [],
        "bad": object(),
    }
    path = tmp_path / "run.json"
    assert runner._persist_receipt(payload, path, "finalization") is True
    receipt = json.loads(path.read_text())
    assert receipt["run_id"] == "controlled-run"
    assert receipt["lanes"][0]["return_code"] == 1
    assert receipt["lanes"][0]["sibling_stop_reason"] == "fail-fast"
    assert receipt["receipt_errors"][0]["stage"] == "finalization:serialize"


def test_runner_canonical_preflight_collision_emits_untrusted_receipt(
    monkeypatch, tmp_path
) -> None:
    _patch_main_preflight(monkeypatch, tmp_path)
    inventory = runner._canonical_resource_inventory(
        (
            {
                "resource_kind": "port",
                "resource_id": 8765,
                "owner": "foreign-run",
                "evidence": "controlled canonical collision",
            },
        )
    )

    def blocked_preflight():
        raise runner.PreflightError("canonical port collision", inventory)

    monkeypatch.setattr(runner, "_preflight", blocked_preflight)
    assert runner.main() == 2
    receipt = json.loads(next(tmp_path.glob("controlled-run.json")).read_text())
    assert receipt["cleanup"]["verdict"] == "untrusted"
    assert receipt["final_exit_code"] != 0
    assert len(receipt["lanes"]) == len(runner.LANES) == 6
    assert receipt["preflight"]["untrusted_resources"]
    assert receipt["lanes"][0]["launch_status"] == "not-attempted"


def test_runner_timeout_receipt_includes_cleanup(monkeypatch, tmp_path) -> None:
    _patch_main_preflight(monkeypatch, tmp_path)
    monkeypatch.setattr(runner, "_stop_deadline", lambda started: -1.0)
    runner.main()
    receipt = json.loads(next(tmp_path.glob("controlled-run.json")).read_text())
    assert receipt["final_exit_code"] == runner.TIMEOUT_EXIT_CODE
    assert receipt["deadline_triggered"] is True
    assert receipt["elapsed_seconds"] >= 0
    assert receipt["cleanup"]["through_elapsed_seconds"] >= 0
    assert len(receipt["lanes"]) == 6
    assert all("cleanup_result" in entry for entry in receipt["lanes"])
    assert "verdict" in receipt["cleanup"]


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


def test_inventory_builds_valid_current_node_three_run_fixture(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(inventory, "ROOT", tmp_path)
    nodes = {f"tests/test_generated.py::test_node_{index}" for index in range(1032)}
    monkeypatch.setattr(inventory, "baseline_nodes", lambda: nodes)
    report_dir = tmp_path / "reports" / "test-profile"
    report_dir.mkdir(parents=True)
    for stamp in ("one", "two", "three"):
        for lane_index, lane in enumerate(inventory.LANES):
            lane_nodes = sorted(nodes)[lane_index :: len(inventory.LANES)]
            (report_dir / f"{stamp}-{lane}.timings").write_text(
                "".join(f"T29_PROFILE 0.100000000s call {node}\n" for node in lane_nodes)
            )
    assert inventory.build(["one", "two", "three"]).count("| `tests/") == 1032
