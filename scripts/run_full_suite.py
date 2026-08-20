"""Run all canonical test lanes concurrently with failure-safe cleanup."""

from __future__ import annotations

import errno
import hashlib
import json
import os
import re
import signal
import socket
import subprocess
import sys
import tempfile
import time
from contextlib import suppress
from dataclasses import dataclass
from pathlib import Path

from scripts.test_governance import (
    current_blocking_candidates,
    load_policy,
    manifest_blocking_candidates,
    select_lowest_importance_cases,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
REPORT_DIR = REPO_ROOT / "reports" / "test-profile"
GRACE_SECONDS = 10.0
MAX_FULL_SUITE_SECONDS = 300.0
TIMEOUT_EXIT_CODE = 124
LANES = (
    ("unit", "test-unit"),
    ("integration", "test-integration"),
    ("audit", "test-audit-integration"),
    ("e2e", "test-e2e"),
    ("bdd", "test-bdd"),
    ("visual", "test-visual"),
)
PORTS = (8765, 8766, 8767, 8768)
LANE_PORTS = {
    "unit": (),
    "integration": (),
    "audit": (),
    "e2e": (8765, 8767),
    "bdd": (8766,),
    "visual": (8768,),
}
LANE_DATABASES = {
    "unit": ("dynamic pytest temp DB",),
    "integration": ("dynamic pytest temp DB",),
    "audit": ("dynamic pytest temp DB",),
    "e2e": (REPO_ROOT / "data" / "test_e2e.db", REPO_ROOT / "data" / "test_e2e_short_ttl.db"),
    "bdd": (REPO_ROOT / "data" / "test_bdd.db",),
    "visual": (REPO_ROOT / "data" / "test_visual.db",),
}
KNOWN_DATABASES = {
    str(path.resolve())
    for targets in LANE_DATABASES.values()
    for path in targets
    if isinstance(path, Path)
}
CANONICAL_DATABASE_PATHS = frozenset(KNOWN_DATABASES)
BASELINE_AUDIT = REPO_ROOT / "tests" / "AUDIT.md"
MANIFEST_PATH = BASELINE_AUDIT
BASELINE_NODE_RE = re.compile(r"^\| `(tests/[^`]+)` \|")
OUTCOME_RE = re.compile(
    r"^\s*(tests/.*?)\s+(PASSED|SKIPPED|FAILED|ERROR)(?:\s+\[.*)?(?:\s+T29_PROFILE.*)?$"
)
TIMING_RE = re.compile(
    r"^T29_PROFILE\s+(?P<seconds>\d+\.\d+)s\s+"
    r"(?P<when>setup|call|teardown)\s+"
    r"(?:(?P<outcome>PASSED|SKIPPED|FAILED|ERROR)\s+)?"
    r"(?P<node>tests/.*?::.*)$"
)
DB_RE = re.compile(r"^T29_DB_TARGET=(.+)$", re.MULTILINE)
SUMMARY_RE = re.compile(
    r"(?P<passed>\d+) passed|(?P<failed>\d+) failed|"
    r"(?P<skipped>\d+) skipped|(?P<errors>\d+) errors?"
)
COLLECTION_RE = re.compile(
    r"collected (?P<collected>\d+) items(?: / (?P<deselected>\d+) deselected)?"
)
MANIFEST_RE = re.compile(r"^- \*\*Population:\*\* (?P<count>[\d,]+) nodes$")
CHECKSUM_RE = re.compile(r"^- \*\*Node checksum:\*\* `(?P<checksum>[0-9a-f]+)`$")
LANE_CHECKSUM_RE = re.compile(
    r"(?P<lane>unit|integration|audit|e2e|bdd|visual) `(?P<checksum>[0-9a-f]+)`"
)


@dataclass(frozen=True)
class Manifest:
    nodes: frozenset[str]
    checksum: str
    population: int
    lane_checksums: dict[str, str]
    skip_ids: tuple[str, ...]
    enforce_population: bool = True


EXPECTED_SKIPS = (
    "tests/test_dockerfile.py::test_docker_build_pro_image_succeeds",
    "tests/test_dockerfile.py::test_docker_run_pro_image_runs_as_omaha_user",
)


def _node_checksum(nodes: set[str] | frozenset[str]) -> str:
    return hashlib.sha256("\n".join(sorted(nodes)).encode()).hexdigest()


def load_manifest(path: Path = MANIFEST_PATH) -> Manifest:
    """Load and validate committed T29 population metadata from AUDIT.md."""
    lines = path.read_text(encoding="utf-8").splitlines()
    nodes = frozenset(
        _normalize_node(match[1]) for line in lines if (match := BASELINE_NODE_RE.match(line))
    )
    population = next(
        (
            int(match["count"].replace(",", ""))
            for line in lines
            if (match := MANIFEST_RE.match(line))
        ),
        None,
    )
    checksum = next(
        (match["checksum"] for line in lines if (match := CHECKSUM_RE.match(line))), None
    )
    lane_line = next((line for line in lines if "**Lane checksums:**" in line), "")
    lane_checksums = {
        match["lane"]: match["checksum"] for match in LANE_CHECKSUM_RE.finditer(lane_line)
    }
    if population is None or checksum is None:
        raise RuntimeError(
            f"T29 manifest population mismatch: snapshot metadata missing; "
            f"population={population}, checksum={checksum}"
        )
    if _node_checksum(nodes) != checksum:
        raise RuntimeError("T29 manifest checksum mismatch")
    if set(lane_checksums) != {name for name, _ in LANES}:
        raise RuntimeError("T29 manifest lane checksums incomplete")
    # Audit population/checksum remain a transparent versioned snapshot. They
    # are not an immutable active-count contract; collection governance
    # classifies every current node independently.
    return Manifest(nodes, checksum, population, lane_checksums, EXPECTED_SKIPS, False)


def _lane_environment(name: str) -> dict[str, str]:
    """Return process environment carrying one lane's receipt scope."""
    return {**os.environ, "T29_DB_RECEIPT_LANE": name}


def _runtime_child_command(task: str, selected: tuple[str, ...] = ()) -> list[str]:
    """Build runtime lane command with pre-run governance deselection."""
    command = ["uv", "run", "task", task, "--", "-s", "-p", "test_profile_plugin"]
    for nodeid in selected:
        command.extend(("--deselect", nodeid))
    return command


def _normalize_node(node: str) -> str:
    """Normalize pytest's BDD output without changing node identity."""
    node = node.replace("\\x3a", ":").strip()
    node = node.split(" <- ", 1)[0]
    if node.startswith("./"):
        node = node[2:]
    return node


def _baseline_nodes() -> set[str]:
    return set(load_manifest().nodes)


class PreflightError(RuntimeError):
    """Canonical resource collision with bounded inventory evidence."""

    def __init__(self, message: str, receipt: dict[str, object]) -> None:
        super().__init__(message)
        self.receipt = receipt


def _resource_path(resource_id: object) -> str:
    return str(Path(str(resource_id)).resolve())


def _canonical_resource_inventory(
    observations: tuple[dict[str, object], ...] = (),
    *,
    run_id: str | None = None,
    owned_resources: tuple[dict[str, object], ...] = (),
) -> dict[str, object]:
    """Classify only canonical resources; retain unrelated host observations."""
    canonical: list[dict[str, object]] = []
    for port in PORTS:
        canonical.append(
            {
                "resource_kind": "port",
                "resource_id": port,
                "relevant": True,
                "classification": "absent",
                "owner": run_id,
                "evidence": "canonical port declared; no host-wide scan",
                "cleanup_target": False,
            }
        )
    for path in sorted(CANONICAL_DATABASE_PATHS):
        canonical.append(
            {
                "resource_kind": "test DB",
                "resource_id": path,
                "relevant": True,
                "classification": "absent",
                "owner": run_id,
                "evidence": "canonical fixed test DB declared; no host-wide scan",
                "cleanup_target": False,
            }
        )
    canonical.extend(owned_resources)

    def is_canonical(observation: dict[str, object]) -> bool:
        kind = str(observation.get("resource_kind", observation.get("kind", "")))
        resource_id = observation.get("resource_id", observation.get("id"))
        if kind == "port":
            try:
                return int(resource_id) in PORTS
            except (TypeError, ValueError):
                return False
        if kind in {"test DB", "database", "path", "temporary path", "log", "timings"}:
            return _resource_path(resource_id) in CANONICAL_DATABASE_PATHS or any(
                _resource_path(item.get("resource_id")) == _resource_path(resource_id)
                for item in owned_resources
                if item.get("resource_id") is not None
            )
        if kind in {"process_group", "pgid"}:
            return any(
                item.get("resource_kind") in {"process_group", "pgid"}
                and item.get("resource_id") == resource_id
                for item in owned_resources
            )
        return False

    resources = [*canonical]
    for raw in observations:
        relevant = is_canonical(raw)
        resource = {
            "resource_kind": raw.get("resource_kind", raw.get("kind", "unknown")),
            "resource_id": raw.get("resource_id", raw.get("id")),
            "relevant": relevant,
            "owner": raw.get("owner"),
            "evidence": raw.get("evidence", "controlled observation"),
            "cleanup_target": False,
            "preserved": True,
            "allowlisted": False,
            "adopted": False,
        }
        if not relevant:
            resource["classification"] = "pre-existing"
        elif raw.get("owner") == run_id and run_id is not None:
            resource["classification"] = "owned-current-run"
        elif raw.get("owner"):
            resource["classification"] = "foreign"
        else:
            resource["classification"] = "unknown"
        resources.append(resource)

    relevant_observations = [item for item in resources if item["relevant"]]
    trusted = all(
        item["classification"] in {"absent", "owned-current-run", "owned-cleaned"}
        for item in relevant_observations
    )
    return {
        "ok": trusted,
        "canonical": {
            "ports": list(PORTS),
            "lane_ports": {lane: list(ports) for lane, ports in LANE_PORTS.items()},
            "fixed_test_db_paths": sorted(CANONICAL_DATABASE_PATHS),
            "runner_owned": list(owned_resources),
        },
        "resources": resources,
        "relevant_resources": relevant_observations,
        "untrusted_resources": [
            item
            for item in relevant_observations
            if item["classification"] not in {"absent", "owned-current-run", "owned-cleaned"}
        ],
    }


def _preflight(observations: tuple[dict[str, object], ...] = ()) -> dict[str, object]:
    """Probe canonical ports and return bounded, ownership-aware inventory."""
    inventory = _canonical_resource_inventory(observations)
    database_url = os.environ.get("DATABASE_URL", "")
    if "data/portfolio.db" in database_url or database_url.endswith("/data/portfolio.db"):
        raise RuntimeError("refusing full test run with production DATABASE_URL")
    for port in PORTS:
        with socket.socket() as probe:
            probe.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                probe.bind(("127.0.0.1", port))
            except OSError as exc:
                collision = {
                    "resource_kind": "port",
                    "resource_id": port,
                    "owner": None,
                    "evidence": f"canonical bind failed: {exc.__class__.__name__}: {exc}",
                }
                inventory = _canonical_resource_inventory((*observations, collision))
                raise PreflightError(f"test lane port {port} is unavailable", inventory) from exc
    for lane, targets in LANE_DATABASES.items():
        for target in targets:
            if isinstance(target, Path) and (
                target.parent != REPO_ROOT / "data" or target.name == "portfolio.db"
            ):
                raise RuntimeError(f"unrecognized {lane} database target: {target}")
    if not inventory["ok"]:
        raise PreflightError("canonical test resource is untrusted", inventory)
    return inventory


def _validate_db_targets(name: str, targets: list[str]) -> None:
    """Accept only complete, lane-owned test DB receipts."""
    resolved = [str(Path(target).resolve()) for target in targets]
    if not resolved:
        raise RuntimeError(f"{name} did not report its session test DB")
    if any(target.endswith("/data/portfolio.db") for target in resolved):
        raise RuntimeError(f"{name} reported production database: {targets!r}")
    expected = {str(path.resolve()) for path in LANE_DATABASES[name] if isinstance(path, Path)}
    dynamic = {target for target in resolved if "/omaha-conftest-safe-" in target}
    configured = set(resolved) - dynamic
    if name in {"unit", "integration", "audit"}:
        if not dynamic or configured:
            raise RuntimeError(f"{name} DB target mismatch: configured={targets!r}")
        return
    if dynamic or configured != expected:
        raise RuntimeError(
            f"{name} DB target mismatch: configured={targets!r}, expected={sorted(expected)!r}"
        )


def _is_lifecycle_race(exc: BaseException) -> bool:
    """Recognize only expected disappearance/write races at process boundary."""
    if isinstance(exc, (ProcessLookupError, BrokenPipeError)):
        return True
    if isinstance(exc, OSError) and exc.errno in {errno.ESRCH, errno.EPIPE}:
        return True
    return exc.__class__.__name__ == "NoSuchProcess"


def _race_evidence(exc: BaseException) -> dict[str, str]:
    return {
        "kind": exc.__class__.__name__,
        "message": str(exc),
    }


def _lane_metadata(
    name: str, task: str, run_id: str, log_path: Path, timing_path: Path
) -> dict[str, object]:
    """Register complete lane evidence before any child is launched."""
    owner_evidence = {
        "run_id": run_id,
        "runner_pid": os.getpid(),
        "recorded_at": time.time(),
        "start_new_session": True,
    }
    resources = {
        "process_group": {
            "resource_kind": "process_group",
            "resource_id": None,
            "owner": run_id,
            "classification": "absent",
            "evidence": "PGID is assigned only after successful Popen",
        },
        "log": {
            "resource_kind": "log",
            "resource_id": str(log_path),
            "owner": run_id,
            "classification": "owned-current-run",
            "evidence": "path opened by current runner before child use",
        },
        "timings": {
            "resource_kind": "temporary path",
            "resource_id": str(timing_path),
            "owner": run_id,
            "classification": "owned-current-run",
            "evidence": "path registered by current runner before child use",
        },
        "database": {
            "resource_kind": "test DB",
            "resource_id": [str(target) for target in LANE_DATABASES[name]],
            "owner": run_id,
            "classification": "absent",
            "evidence": "lane receipt required before ownership classification",
        },
        "ports": {
            "resource_kind": "port",
            "resource_id": list(LANE_PORTS[name]),
            "owner": run_id,
            "classification": "absent" if not LANE_PORTS[name] else "unknown",
            "evidence": (
                "lane has no canonical server port"
                if not LANE_PORTS[name]
                else "preflight availability is not ownership proof"
            ),
        },
    }
    return {
        "lane": name,
        "task": f"uv run task {task}",
        "pid": None,
        "pgid": None,
        "log": str(log_path),
        "timings": str(timing_path),
        "ports": list(LANE_PORTS[name]),
        "owned_resource_mapping": resources,
        "owner_evidence": owner_evidence,
        "registered_at": owner_evidence["recorded_at"],
        "started_at": None,
        "ended_at": None,
        "status": "pending",
        "launch_status": "pending",
        "launch_error": None,
        "signal": None,
        "signals": [],
        "return_code": None,
        "exit_code": None,
        "sibling_stop_reason": None,
        "residue_classification": "absent",
        "residue": [],
        "cleanup_status": "not-attempted",
        "cleanup_result": "not-attempted",
        "lifecycle_races": [],
        "timeout": {
            "deadline_triggered": False,
            "deadline": None,
            "duration_exceeded": False,
        },
        "receipt_error": None,
    }


def _record_receipt_error(
    payload: dict[str, object], stage: str, exc: BaseException, lane: str | None = None
) -> None:
    """Retain receipt failures without replacing earlier run telemetry."""
    error = {
        "stage": stage,
        "kind": exc.__class__.__name__,
        "message": str(exc),
    }
    errors = payload.setdefault("receipt_errors", [])
    assert isinstance(errors, list)
    errors.append(error)
    payload["receipt_error"] = error
    if lane is not None:
        lanes = payload.get("lanes", [])
        if isinstance(lanes, list):
            for entry in lanes:
                if isinstance(entry, dict) and entry.get("lane") == lane:
                    entry["receipt_error"] = f"{stage}: {exc}"
                    break


def _json_safe(value: object) -> object:
    """Convert final receipt values to JSON-safe diagnostics after serialization failure."""
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    try:
        return str(value)
    except Exception:
        return f"<{type(value).__name__} unavailable>"


def _atomic_write_receipt(path: Path, serialized: str) -> None:
    """Flush and atomically replace receipt so an interrupted write leaves prior receipt."""
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            descriptor = -1
            stream.write(serialized)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        directory_flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
        directory = os.open(path.parent, directory_flags)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    except Exception:
        if descriptor >= 0:
            os.close(descriptor)
        with suppress(OSError):
            os.unlink(temporary)
        raise


def _persist_receipt(
    payload: dict[str, object], path: Path, stage: str, lane: str | None = None
) -> bool:
    """Persist current ledger snapshot, retaining telemetry across serialization/write errors."""
    try:
        serialized = json.dumps(payload, indent=2) + "\n"
    except Exception as exc:
        _record_receipt_error(payload, stage + ":serialize", exc, lane)
        try:
            serialized = json.dumps(_json_safe(payload), indent=2) + "\n"
        except Exception as fallback_exc:
            _record_receipt_error(payload, stage + ":fallback-serialize", fallback_exc, lane)
            return False
    try:
        _atomic_write_receipt(path, serialized)
    except Exception as exc:
        _record_receipt_error(payload, stage + ":write", exc, lane)
        return False
    return True


def _write_preflight_blocked_receipt(
    started: float,
    run_started_at: float,
    preflight: dict[str, object],
    reason: str,
) -> None:
    """Persist six explicit lane receipts when canonical preflight blocks launch."""
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%dT%H%M%S", time.localtime())
    run_id = f"{stamp}-{os.getpid()}"
    metadata = []
    for name, task in LANES:
        entry = _lane_metadata(
            name,
            task,
            run_id,
            REPORT_DIR / f"{stamp}-{name}.log",
            REPORT_DIR / f"{stamp}-{name}.timings",
        )
        entry.update(
            {
                "status": "preflight-blocked",
                "launch_status": "not-attempted",
                "cleanup_status": "not-attempted",
                "cleanup_result": "not-attempted",
                "receipt_error": reason,
                "ended_at": time.time(),
            }
        )
        metadata.append(entry)
    elapsed = time.monotonic() - started
    payload = {
        "run_id": run_id,
        "started_at": run_started_at,
        "ended_at": time.time(),
        "elapsed_seconds": elapsed,
        "duration_limit_seconds": MAX_FULL_SUITE_SECONDS,
        "duration_exceeded": _duration_exceeded(elapsed),
        "deadline_triggered": False,
        "lanes": metadata,
        "clean_children": True,
        "cleanup": {
            "verdict": "untrusted",
            "owned_only": True,
            "through_elapsed_seconds": elapsed,
            "residue": preflight.get("untrusted_resources", []),
        },
        "preflight": preflight,
        "preflight_reconciliation": {"ok": False, "reason": reason},
        "reconciliation": None,
        "first_failure": 2,
        "final_exit_code": 2,
    }
    _persist_receipt(payload, REPORT_DIR / f"{stamp}-run.json", "preflight-blocked")


def _entry_for(
    metadata: dict[str, dict[str, object]] | None, name: str
) -> dict[str, object] | None:
    return metadata.get(name) if metadata is not None else None


def _record_race(entry: dict[str, object] | None, phase: str, exc: BaseException) -> None:
    if entry is None:
        return
    races = entry.setdefault("lifecycle_races", [])
    assert isinstance(races, list)
    races.append({"phase": phase, **_race_evidence(exc)})
    entry["residue_classification"] = "absent"
    entry["residue"] = [{"phase": phase, **_race_evidence(exc)}]


def _resource_is_untrusted(resource: object) -> bool:
    return (
        isinstance(resource, dict)
        and resource.get("relevant", True)
        and resource.get("classification") in {"foreign", "unknown", "pre-existing"}
    )


def _entry_has_untrusted_resource(entry: dict[str, object] | None) -> bool:
    if entry is None:
        return False
    resources = entry.get("owned_resource_mapping", {})
    return isinstance(resources, dict) and any(
        _resource_is_untrusted(resource) for resource in resources.values()
    )


def _resource_cleanup_verdict(
    metadata: dict[str, dict[str, object]],
) -> tuple[bool, list[dict[str, object]]]:
    """Return false when canonical foreign/unknown residue reached cleanup."""
    residue: list[dict[str, object]] = []
    for entry in metadata.values():
        resources = entry.get("owned_resource_mapping", {})
        if not isinstance(resources, dict):
            continue
        for resource_name, resource in resources.items():
            if _resource_is_untrusted(resource):
                assert isinstance(resource, dict)
                evidence = {
                    "lane": entry.get("lane"),
                    "resource": resource_name,
                    **resource,
                }
                residue.append(evidence)
                entry["residue_classification"] = str(resource["classification"])
                entry.setdefault("residue", []).append(evidence)
                entry["cleanup_result"] = "untrusted-resource"
    return not residue, residue


def _propagate_resource_inventory(
    metadata: dict[str, dict[str, object]], inventory: dict[str, object]
) -> bool:
    """Attach canonical observations to lane receipts; never adopt them."""
    trusted = True
    observations = inventory.get("untrusted_resources", [])
    if not isinstance(observations, list):
        return False
    for observation in observations:
        if not isinstance(observation, dict):
            trusted = False
            continue
        resource_id = observation.get("resource_id")
        lane_name = observation.get("lane")
        if lane_name not in metadata:
            for candidate, ports in LANE_PORTS.items():
                if resource_id in ports:
                    lane_name = candidate
                    break
        if lane_name not in metadata:
            for candidate, targets in LANE_DATABASES.items():
                if _resource_path(resource_id) in {_resource_path(target) for target in targets}:
                    lane_name = candidate
                    break
        if lane_name not in metadata:
            trusted = False
            continue
        entry = metadata[str(lane_name)]
        kind = str(observation.get("resource_kind", ""))
        mapping_name = {
            "port": "ports",
            "test DB": "database",
            "database": "database",
            "process_group": "process_group",
            "pgid": "process_group",
            "path": "timings",
            "temporary path": "timings",
            "log": "log",
            "timings": "timings",
        }.get(kind)
        if mapping_name is not None:
            resource = entry["owned_resource_mapping"][mapping_name]
            resource.update(
                {
                    "resource_id": observation["resource_id"],
                    "classification": observation["classification"],
                    "owner": observation.get("owner"),
                    "evidence": observation.get("evidence", "preflight observation"),
                    "relevant": observation["relevant"],
                }
            )
        entry["residue_classification"] = observation["classification"]
        entry.setdefault("residue", []).append(observation)
        entry["cleanup_result"] = "untrusted-resource"
        trusted = False
    return trusted


def _owned_process_group(entry: dict[str, object] | None, process: object) -> bool:
    """Require current-run process-group evidence before signaling or reaping."""
    if entry is None:
        return True
    resource = entry.get("owned_resource_mapping", {}).get("process_group", {})
    if not isinstance(resource, dict):
        return False
    if resource.get("classification") in {"foreign", "unknown", "pre-existing"}:
        return False
    resource_id = resource.get("resource_id")
    if resource_id is not None and resource_id != getattr(process, "pid", None):
        return False
    # Direct helper callers represent a launched child in the process map. The
    # main runner always upgrades this entry to owned-current-run at launch.
    return resource.get("classification") in {None, "absent", "owned-current-run"}


def _stop(
    processes: dict[str, subprocess.Popen[str]],
    sig: int,
    metadata: dict[str, dict[str, object]] | None = None,
    reason: str = "cleanup",
) -> bool:
    """Signal only launched current-run groups; report bounded lifecycle races."""
    clean = True
    for name, process in processes.items():
        entry = _entry_for(metadata, name)
        if _entry_has_untrusted_resource(entry) or not _owned_process_group(entry, process):
            if entry is not None:
                entry["cleanup_result"] = "untrusted-resource"
                entry["residue_classification"] = "foreign"
                entry.setdefault("residue", []).append(
                    {
                        "phase": "signal",
                        "resource": "process_group",
                        "classification": "foreign",
                        "resource_id": getattr(process, "pid", None),
                        "evidence": "process group is not current-run-owned",
                    }
                )
            clean = False
            continue
        try:
            running = process.poll() is None
        except Exception as exc:
            if _is_lifecycle_race(exc):
                _record_race(entry, "poll-before-signal", exc)
                if entry is not None:
                    entry["cleanup_result"] = "vanished-child"
                clean = False
                continue
            if entry is not None:
                entry["cleanup_result"] = f"error: {exc}"
            clean = False
            continue
        if not running:
            continue
        if entry is not None:
            entry["signal"] = signal.Signals(sig).name
            signals = entry.setdefault("signals", [])
            assert isinstance(signals, list)
            signals.append({"signal": signal.Signals(sig).name, "reason": reason})
            entry["sibling_stop_reason"] = reason
        try:
            os.killpg(process.pid, sig)
        except Exception as exc:
            if _is_lifecycle_race(exc):
                _record_race(entry, "signal", exc)
                if entry is not None:
                    entry["cleanup_result"] = "vanished-child"
            else:
                if entry is not None:
                    entry["cleanup_result"] = f"error: {exc}"
            clean = False
    return clean


def _reap(
    processes: dict[str, subprocess.Popen[str]],
    metadata: dict[str, dict[str, object]] | None = None,
    reason: str = "cleanup",
) -> bool:
    """Reap launched children and escalate only recorded process groups."""
    clean = True
    deadline = time.monotonic() + GRACE_SECONDS
    while time.monotonic() < deadline:
        running = False
        for name, process in processes.items():
            entry = _entry_for(metadata, name)
            if _entry_has_untrusted_resource(entry) or not _owned_process_group(entry, process):
                continue
            try:
                if process.poll() is None:
                    running = True
            except Exception as exc:
                entry = _entry_for(metadata, name)
                if _is_lifecycle_race(exc):
                    _record_race(entry, "poll-before-reap", exc)
                    if entry is not None:
                        entry["cleanup_result"] = "vanished-child"
                    clean = False
                else:
                    if entry is not None:
                        entry["cleanup_result"] = f"error: {exc}"
                    clean = False
        if not running:
            break
        time.sleep(0.1)
    survivors: list[tuple[str, subprocess.Popen[str]]] = []
    for name, process in processes.items():
        entry = _entry_for(metadata, name)
        if _entry_has_untrusted_resource(entry) or not _owned_process_group(entry, process):
            if entry is not None:
                entry["cleanup_result"] = "untrusted-resource"
                entry["residue_classification"] = "foreign"
            clean = False
            continue
        try:
            if process.poll() is None:
                survivors.append((name, process))
        except Exception as exc:
            entry = _entry_for(metadata, name)
            if _is_lifecycle_race(exc):
                _record_race(entry, "poll-after-grace", exc)
                if entry is not None:
                    entry["cleanup_result"] = "vanished-child"
            else:
                if entry is not None:
                    entry["cleanup_result"] = f"error: {exc}"
            clean = False
    for name, process in survivors:
        entry = _entry_for(metadata, name)
        if entry is not None:
            entry["cleanup_status"] = "escalated"
            entry["signal"] = signal.Signals(signal.SIGKILL).name
            entry["signals"] = [
                *entry.get("signals", []),
                {"signal": signal.Signals(signal.SIGKILL).name, "reason": reason},
            ]
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except Exception as exc:
            if _is_lifecycle_race(exc):
                _record_race(entry, "kill", exc)
                if entry is not None:
                    entry["cleanup_result"] = "vanished-child"
            else:
                if entry is not None:
                    entry["cleanup_result"] = f"error: {exc}"
            clean = False
    for name, process in processes.items():
        entry = _entry_for(metadata, name)
        if _entry_has_untrusted_resource(entry) or not _owned_process_group(entry, process):
            continue
        try:
            waited = process.wait()
            if entry is not None and process.returncode is None:
                entry["return_code"] = waited
                entry["exit_code"] = waited
        except Exception as exc:
            if _is_lifecycle_race(exc):
                _record_race(entry, "wait", exc)
                if entry is not None:
                    entry["cleanup_result"] = "vanished-child"
            else:
                if entry is not None:
                    entry["cleanup_result"] = f"error: {exc}"
            clean = False
        if entry is not None:
            entry["return_code"] = process.returncode
            entry["exit_code"] = process.returncode
            if entry["cleanup_result"] == "not-attempted":
                entry["cleanup_result"] = "owned-cleaned"
            if entry["cleanup_status"] == "not-attempted":
                entry["cleanup_status"] = "complete"
            if entry["cleanup_result"] == "owned-cleaned":
                entry["residue_classification"] = "owned-cleaned"
                entry["owned_resource_mapping"]["process_group"]["classification"] = "owned-cleaned"
    return clean and not survivors


def _summary(output: str) -> dict[str, int]:
    result = {"passed": 0, "failed": 0, "skipped": 0, "errors": 0}
    for match in SUMMARY_RE.finditer(output):
        for key, value in match.groupdict().items():
            if value is not None:
                result[key] += int(value)
    return result


def _timing_records(output: str) -> dict[str, dict[str, object]]:
    records: dict[str, dict[str, object]] = {}
    for line in output.splitlines():
        match = TIMING_RE.match(line)
        if match:
            node = _normalize_node(match["node"])
            records[node] = {
                "duration": float(match["seconds"]),
                "when": match["when"],
                "outcome": (match["outcome"] or "PASSED").upper(),
            }
    return records


def _collection(output: str, timing_output: str = "") -> dict[str, object]:
    """Reconcile timing receipts; retain terminal output only as diagnostics."""
    records = _timing_records(timing_output)
    nodes = set(records)
    skipped = {node for node, record in records.items() if record["outcome"] == "SKIPPED"}
    outcomes = {node: str(record["outcome"]) for node, record in records.items()}
    terminal_outcomes: dict[str, str] = {}
    for line in output.splitlines():
        match = OUTCOME_RE.match(line)
        if match:
            node = _normalize_node(match[1])
            terminal_outcomes[node] = match[2]
    matches = list(COLLECTION_RE.finditer(output))
    result: dict[str, object] = {
        "collected": len(nodes),
        "nodes": sorted(nodes),
        "skipped": sorted(skipped),
        "node_checksum": hashlib.sha256("\n".join(sorted(nodes)).encode()).hexdigest(),
        "outcomes": outcomes,
        "terminal_outcomes": terminal_outcomes,
    }
    if matches and matches[-1]["deselected"] is not None:
        result["deselected"] = int(matches[-1]["deselected"])
    return result


def _final_exit_code(
    interrupted: int | None,
    clean: bool,
    first_failure: int | None,
    processes: dict[str, subprocess.Popen[str]],
) -> int:
    """Choose parent result after every child has been reaped."""
    if interrupted is not None:
        return 128 + interrupted
    if not clean or any(process.returncode != 0 for process in processes.values()):
        if first_failure is not None:
            return first_failure
        return next(
            (
                process.returncode if process.returncode != 0 else 1
                for process in processes.values()
                if process.returncode != 0
            ),
            1,
        )
    return 0


def _duration_exceeded(elapsed_seconds: float) -> bool:
    """Return whether a full-suite run breached its hard wall-clock ceiling."""
    return elapsed_seconds > MAX_FULL_SUITE_SECONDS


def _stop_deadline(started: float) -> float:
    """Reserve cleanup margin so hard ceiling includes child teardown."""
    return started + MAX_FULL_SUITE_SECONDS - GRACE_SECONDS - 1.0


def reconcile_population(
    manifest: Manifest,
    lane_nodes: dict[str, set[str]],
    skip_nodes: set[str],
    *,
    check_skips: bool = True,
) -> dict[str, object]:
    all_nodes = set().union(*lane_nodes.values()) if lane_nodes else set()
    duplicate_nodes = sorted(
        node for node in all_nodes if sum(node in values for values in lane_nodes.values()) > 1
    )
    expected_lanes = {name for name, _ in LANES}
    actual_lanes = set(lane_nodes)
    missing_lanes = sorted(expected_lanes - actual_lanes)
    unexpected_lanes = sorted(actual_lanes - expected_lanes)
    lane_checksums = {lane: _node_checksum(nodes) for lane, nodes in lane_nodes.items()}
    lane_mismatches = {}
    if manifest.enforce_population:
        for lane, _nodes in lane_nodes.items():
            actual_checksum = lane_checksums[lane]
            if actual_checksum != manifest.lane_checksums.get(lane):
                lane_mismatches[lane] = {
                    "expected": manifest.lane_checksums.get(lane),
                    "actual": actual_checksum,
                }
    result = {
        "expected_nodes": manifest.population if manifest.enforce_population else None,
        "manifest_snapshot_nodes": manifest.population,
        "actual_nodes": len(all_nodes),
        "lane_checksums": lane_checksums,
        "duplicate_nodes": duplicate_nodes,
        "missing_lanes": missing_lanes,
        "unexpected_lanes": unexpected_lanes,
        "missing_nodes": sorted(manifest.nodes - all_nodes) if manifest.enforce_population else [],
        "unexpected_nodes": (
            sorted(all_nodes - manifest.nodes) if manifest.enforce_population else []
        ),
        "lane_mismatches": lane_mismatches,
        "expected_skips": list(manifest.skip_ids),
        "actual_skips": sorted(skip_nodes),
        "skip_mismatch": check_skips and sorted(skip_nodes) != list(manifest.skip_ids),
    }
    result["ok"] = (
        actual_lanes == expected_lanes
        and (len(all_nodes) == manifest.population if manifest.enforce_population else True)
        and not result["duplicate_nodes"]
        and not result["missing_nodes"]
        and not result["unexpected_nodes"]
        and not result["lane_mismatches"]
        and not result["skip_mismatch"]
    )
    return result


def reconcile_preflight(manifest: Manifest, lane_nodes: dict[str, set[str]]) -> dict[str, object]:
    """Reconcile collection-only lane receipts before starting test children."""
    return reconcile_population(manifest, lane_nodes, set(), check_skips=False)


def _select_pre_run_cases(
    policy,
    manifest_or_preflight: set[str]
    | frozenset[str]
    | dict[str, tuple[set[str], set[str], list[str]]],
) -> tuple[tuple[object, ...], dict[str, tuple[str, ...]]]:
    """Select versioned blocking candidates before any runtime child launch."""
    if isinstance(manifest_or_preflight, dict):
        lane_nodes = {name: nodes for name, (nodes, _, _) in manifest_or_preflight.items()}
        candidates = current_blocking_candidates(lane_nodes)
    else:
        candidates = manifest_blocking_candidates(manifest_or_preflight)
    selected = select_lowest_importance_cases(
        policy.prior_known_seconds,
        candidates,
        ceiling_seconds=policy.ceiling_seconds,
        safety_margin_seconds=policy.safety_margin_seconds,
    )
    if isinstance(manifest_or_preflight, dict):
        selected_by_lane = {
            lane: tuple(case.nodeid for case in selected if case.nodeid in nodes)
            for lane, nodes in lane_nodes.items()
        }
    else:
        selected_by_lane = {}
        for case in selected:
            if case.lane is None:
                raise RuntimeError(f"selected case has no lane: {case.nodeid}")
            selected_by_lane.setdefault(case.lane, tuple())
            selected_by_lane[case.lane] += (case.nodeid,)
    return selected, selected_by_lane


def main() -> int:
    started = time.monotonic()
    run_started_at = time.time()
    try:
        policy = load_policy()
    except (OSError, RuntimeError, ValueError) as exc:
        print(f"full-suite governance preflight failed: {exc}", file=sys.stderr)
        return 2
    try:
        preflight_receipt = _preflight() or _canonical_resource_inventory()
    except PreflightError as exc:
        try:
            _write_preflight_blocked_receipt(started, run_started_at, exc.receipt, str(exc))
        except OSError as receipt_exc:
            print(f"full-suite preflight receipt write failed: {receipt_exc}", file=sys.stderr)
        print(f"full-suite preflight failed: {exc}", file=sys.stderr)
        return 2
    except RuntimeError as exc:
        print(f"full-suite preflight failed: {exc}", file=sys.stderr)
        return 2
    try:
        manifest = load_manifest()
        selected_before_run, selected_by_lane = _select_pre_run_cases(policy, manifest.nodes)
        if time.monotonic() - started >= MAX_FULL_SUITE_SECONDS:
            print(
                "full suite duration ceiling reached during preflight",
                file=sys.stderr,
            )
            return TIMEOUT_EXIT_CODE
    except RuntimeError as exc:
        print(f"full-suite lane preflight failed: {exc}", file=sys.stderr)
        return 2
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%dT%H%M%S", time.localtime())
    run_id = f"{stamp}-{os.getpid()}"
    processes: dict[str, subprocess.Popen[str]] = {}
    metadata: list[dict[str, object]] = []
    metadata_by_lane: dict[str, dict[str, object]] = {}
    for name, task in LANES:
        log_path = REPORT_DIR / f"{stamp}-{name}.log"
        timing_path = REPORT_DIR / f"{stamp}-{name}.timings"
        entry = _lane_metadata(name, task, run_id, log_path, timing_path)
        entry["owned_resources"] = entry["owned_resource_mapping"]
        metadata.append(entry)
        metadata_by_lane[name] = entry
    receipt_path = REPORT_DIR / f"{stamp}-run.json"
    payload: dict[str, object] = {
        "run_id": run_id,
        "started_at": run_started_at,
        "ended_at": None,
        "elapsed_seconds": None,
        "duration_limit_seconds": MAX_FULL_SUITE_SECONDS,
        "duration_exceeded": False,
        "deadline_triggered": False,
        "lanes": metadata,
        "clean_children": None,
        "cleanup": {
            "verdict": "not-attempted",
            "owned_only": True,
            "through_elapsed_seconds": None,
            "residue": [],
        },
        "preflight": {
            **preflight_receipt,
            "source": "canonical resource inventory plus versioned audit manifest",
            "manifest_snapshot_nodes": manifest.population,
            "manifest_checksum": manifest.checksum,
        },
        "preflight_reconciliation": {
            "ok": True,
            "source": "versioned audit manifest",
            "selected_before_child_launch": True,
        },
        "governance": {
            "policy_version": policy.version,
            "ceiling_seconds": policy.ceiling_seconds,
            "prior_known_seconds": policy.prior_known_seconds,
            "safety_margin_seconds": policy.safety_margin_seconds,
            "approved_outside_blocking_lane": [case.nodeid for case in policy.approved_disabled],
            "additional_pre_run_selection": [
                {
                    "nodeid": case.nodeid,
                    "importance": case.importance,
                    "estimated_seconds": case.estimated_seconds,
                }
                for case in selected_before_run
            ],
            "additional_pre_run_economy_seconds": sum(
                case.estimated_seconds for case in selected_before_run
            ),
            "blocking_command": policy.blocking_command,
            "expanded_command": policy.expanded_command,
        },
        "reconciliation": None,
        "first_failure": None,
        "first_failure_lane": None,
        "first_failure_reason": None,
        "final_exit_code": None,
        "receipt_errors": [],
        "receipt_error": None,
    }
    receipt_write_failed = not _persist_receipt(payload, receipt_path, "pre-launch")

    def persist(stage: str, lane: str | None = None) -> None:
        nonlocal receipt_write_failed
        if not _persist_receipt(payload, receipt_path, stage, lane):
            receipt_write_failed = True

    def record_error(stage: str, exc: BaseException, lane: str | None = None) -> None:
        _record_receipt_error(payload, stage, exc, lane)
        persist(stage + ":retained", lane)

    interrupted: int | None = None
    first_failure: int | None = None
    first_failure_lane: str | None = None
    first_failure_reason: str | None = None
    stopping = False
    duration_exceeded = False
    deadline_triggered = False

    def handle_signal(signum: int, _frame: object) -> None:
        nonlocal interrupted, stopping
        if stopping:
            return
        interrupted, stopping = signum, True
        try:
            _stop(processes, signum, metadata_by_lane, "parent-interrupt")
        except Exception as exc:
            record_error("parent-interrupt", exc)
        persist("parent-interrupt")

    previous = {sig: signal.getsignal(sig) for sig in (signal.SIGINT, signal.SIGTERM)}
    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    def launch(name: str, task: str) -> bool:
        entry = metadata_by_lane[name]
        log_path = Path(str(entry["log"]))
        timing_path = Path(str(entry["timings"]))
        log = None
        child_env = _lane_environment(name)
        child_env["PYTHONPATH"] = os.pathsep.join(
            filter(None, [str(REPO_ROOT / "scripts"), child_env.get("PYTHONPATH", "")])
        )
        child_env["T29_PROFILE_PATH"] = str(timing_path)
        child_env["T29_DB_RECEIPT_LANE"] = name
        entry["launch_status"] = "starting"
        try:
            log = log_path.open("w", encoding="utf-8")
            process = subprocess.Popen(
                _runtime_child_command(task, selected_by_lane.get(name, ())),
                cwd=REPO_ROOT,
                env=child_env,
                stdout=log,
                stderr=subprocess.STDOUT,
                start_new_session=True,
                text=True,
            )
        except Exception as exc:
            entry["launch_status"] = "failed"
            entry["status"] = "launch-failed"
            entry["launch_error"] = f"{exc.__class__.__name__}: {exc}"
            entry["residue_classification"] = "absent"
            entry["cleanup_status"] = "not-needed"
            entry["cleanup_result"] = "not-launched"
            if log is not None:
                log.close()
            persist(f"launch:{name}", name)
            return False
        finally:
            if log is not None:
                log.close()
        processes[name] = process
        entry["pid"] = process.pid
        entry["pgid"] = process.pid
        entry["started_at"] = time.time()
        entry["status"] = "launched"
        entry["launch_status"] = "launched"
        process_group = entry["owned_resource_mapping"]["process_group"]
        process_group.update(
            {
                "resource_id": process.pid,
                "classification": "owned-current-run",
                "evidence": "Popen(start_new_session=True) returned current-run child",
            }
        )
        ports_resource = entry["owned_resource_mapping"]["ports"]
        ports_resource.update(
            {
                "classification": ("owned-current-run" if LANE_PORTS[name] else "absent"),
                "evidence": (
                    "Popen(start_new_session=True) plus canonical lane port mapping"
                    if LANE_PORTS[name]
                    else "lane has no canonical server port"
                ),
            }
        )
        persist(f"launch:{name}", name)
        return True

    def monitor(phase: tuple[str, ...]) -> bool:
        nonlocal \
            first_failure, \
            first_failure_lane, \
            first_failure_reason, \
            stopping, \
            deadline_triggered
        while True:
            running = False
            for name in phase:
                process = processes[name]
                entry = metadata_by_lane[name]
                try:
                    if process.poll() is None:
                        running = True
                except Exception as exc:
                    if _is_lifecycle_race(exc):
                        _record_race(entry, "monitor-poll", exc)
                        if first_failure is None:
                            first_failure = 1
                            first_failure_lane = name
                            first_failure_reason = "lane disappeared during monitor poll"
                    else:
                        entry["receipt_error"] = f"monitor poll: {exc}"
                        if first_failure is None:
                            first_failure = 2
                            first_failure_lane = name
                            first_failure_reason = "monitor poll failed"
                    stopping = True
                    _stop_reason = f"lane-disappeared:{name}"
                    try:
                        _stop(processes, signal.SIGTERM, metadata_by_lane, _stop_reason)
                    except Exception as exc:
                        record_error("monitor-stop", exc, name)
                    persist("monitor-lane-disappeared", name)
                    return False
            if interrupted is not None:
                return False
            if time.monotonic() >= _stop_deadline(started):
                deadline_triggered = True
                first_failure = TIMEOUT_EXIT_CODE
                stopping = True
                for entry in metadata:
                    entry["timeout"]["deadline_triggered"] = True
                    entry["timeout"]["deadline"] = _stop_deadline(started)
                try:
                    _stop(processes, signal.SIGTERM, metadata_by_lane, "deadline")
                except Exception as exc:
                    record_error("deadline-stop", exc)
                first_failure_lane = first_failure_lane or "deadline"
                first_failure_reason = first_failure_reason or "300-second deadline"
                persist("deadline-stop")
                return False
            failed = None
            for name in phase:
                process = processes[name]
                try:
                    returncode = process.poll()
                except Exception as exc:
                    if _is_lifecycle_race(exc):
                        _record_race(metadata_by_lane[name], "monitor-failure-poll", exc)
                        returncode = 1
                    else:
                        metadata_by_lane[name]["receipt_error"] = f"monitor poll: {exc}"
                        returncode = 2
                if returncode not in (None, 0):
                    failed = name
                    break
            if failed is not None:
                first_failure = processes[failed].returncode
                if first_failure == 0 or first_failure is None:
                    first_failure = 1
                first_failure_lane = failed
                first_failure_reason = "lane exited nonzero; fail-fast sibling stop"
                stopping = True
                try:
                    _stop(
                        processes,
                        signal.SIGTERM,
                        metadata_by_lane,
                        f"fail-fast:{failed}",
                    )
                except Exception as exc:
                    record_error("fail-fast-stop", exc, failed)
                persist("fail-fast-stop", failed)
                return False
            if not running:
                return True
            time.sleep(0.2)

    clean = True
    try:
        launch_failed = False
        failed_lane = None
        for index, (name, task) in enumerate(LANES):
            if not launch(name, task):
                launch_failed = True
                failed_lane = name
                for remaining_name, _ in LANES[index + 1 :]:
                    remaining = metadata_by_lane[remaining_name]
                    remaining["launch_status"] = "not-attempted"
                    remaining["status"] = "not-attempted"
                    remaining["launch_error"] = f"partial launch after {name} failed"
                    remaining["cleanup_status"] = "not-needed"
                    remaining["cleanup_result"] = "not-launched"
                break
        if launch_failed:
            first_failure = 2
            first_failure_lane = failed_lane
            first_failure_reason = f"partial launch failed for {failed_lane}"
            stopping = True
            try:
                _stop(
                    processes,
                    signal.SIGTERM,
                    metadata_by_lane,
                    f"partial-launch:{failed_lane}",
                )
            except Exception as exc:
                record_error("partial-launch-stop", exc, failed_lane)
            persist("partial-launch", failed_lane)
        elif processes:
            monitor(tuple(name for name, _ in LANES))
    except Exception as exc:
        if first_failure is None:
            first_failure = 2
            first_failure_lane = first_failure_lane or "runner"
            first_failure_reason = first_failure_reason or "runner lifecycle exception"
        record_error("launch-monitor", exc)
    finally:
        try:
            clean = _reap(processes, metadata_by_lane, "final-cleanup")
        except Exception as exc:
            clean = False
            if first_failure is None:
                first_failure = 2
                first_failure_lane = first_failure_lane or "runner"
                first_failure_reason = first_failure_reason or "cleanup exception"
            record_error("cleanup", exc)
        payload["clean_children"] = clean
        payload["cleanup"]["through_elapsed_seconds"] = time.monotonic() - started
        payload["cleanup"]["verdict"] = "clean" if clean else "untrusted"
        persist("cleanup")
        for sig, handler in previous.items():
            try:
                signal.signal(sig, handler)
            except Exception as exc:
                record_error("signal-restore", exc)
    empty_collection = {
        "collected": 0,
        "nodes": [],
        "skipped": [],
        "node_checksum": _node_checksum(set()),
        "outcomes": {},
        "terminal_outcomes": {},
    }
    for entry in metadata:
        lane = str(entry["lane"])
        process = processes.get(lane)
        output = ""
        timing_output = ""
        collection: dict[str, object] = dict(empty_collection)
        db_targets: list[str] = []
        try:
            try:
                output = Path(str(entry["log"])).read_text(encoding="utf-8", errors="replace")
            except OSError as exc:
                entry["residue_classification"] = "unknown"
                entry["cleanup_result"] = "untrusted-receipt"
                if first_failure is None:
                    first_failure = 2
                    first_failure_lane = lane
                    first_failure_reason = "lane log read failed"
                record_error("log-read", exc, lane)
            timing_path = Path(str(entry["timings"]))
            try:
                timing_output = (
                    timing_path.read_text(encoding="utf-8", errors="replace")
                    if timing_path.exists()
                    else ""
                )
            except OSError as exc:
                entry["residue_classification"] = "unknown"
                entry["cleanup_result"] = "untrusted-receipt"
                if first_failure is None:
                    first_failure = 2
                    first_failure_lane = lane
                    first_failure_reason = "lane timing read failed"
                record_error("timing-read", exc, lane)
            collection = _collection(output, timing_output)
            db_targets = [str(Path(value).resolve()) for value in DB_RE.findall(output)]
            if process is not None:
                try:
                    _validate_db_targets(lane, db_targets)
                    if lane in {"unit", "integration"} and not collection["nodes"]:
                        raise RuntimeError(f"{lane} published empty collection receipt")
                    database_resource = entry["owned_resource_mapping"]["database"]
                    database_resource.update(
                        {
                            "resource_id": db_targets,
                            "classification": "owned-current-run",
                            "evidence": "lane emitted matching T29_DB_TARGET receipt",
                        }
                    )
                except RuntimeError as exc:
                    entry["residue_classification"] = "unknown"
                    entry["cleanup_result"] = "untrusted-receipt"
                    database_resource = entry["owned_resource_mapping"]["database"]
                    database_resource["resource_id"] = db_targets
                    database_resource["classification"] = "unknown"
                    if first_failure is None:
                        first_failure = 2
                        first_failure_lane = lane
                        first_failure_reason = "lane DB receipt invalid"
                    record_error("db-receipt", exc, lane)
            elif entry["launch_status"] != "failed":
                entry["receipt_error"] = entry["launch_error"] or "lane was not launched"
        except Exception as exc:
            entry["residue_classification"] = "unknown"
            entry["cleanup_result"] = "untrusted-receipt"
            if first_failure is None:
                first_failure = 2
                first_failure_lane = lane
                first_failure_reason = "lane finalization failed"
            record_error("lane-finalization", exc, lane)
        finally:
            try:
                return_code = process.returncode if process is not None else None
            except Exception as exc:
                return_code = None
                record_error("return-code-read", exc, lane)
            try:
                summary = _summary(output)
            except Exception as exc:
                summary = {}
                record_error("summary-read", exc, lane)
            try:
                entry.update(
                    {
                        "exit_code": return_code,
                        "return_code": return_code,
                        "ended_at": time.time(),
                        "summary": summary,
                        "collection": collection,
                        "db_targets": db_targets,
                    }
                )
                if process is not None:
                    entry["status"] = "failed" if return_code not in (0, None) else "completed"
                    if return_code not in (0, None) and first_failure is None:
                        first_failure = return_code
                        first_failure_lane = lane
                        first_failure_reason = "lane returned nonzero"
                if entry["timeout"]["deadline_triggered"]:
                    entry["timeout"]["duration_exceeded"] = True
            except Exception as exc:
                record_error("lane-finalization-update", exc, lane)
            persist("lane-finalization", lane)
            print(f"[{entry['lane']}] exit={entry['exit_code']} log={entry['log']}")
    lane_nodes = {
        name: set(entry["collection"]["nodes"])
        for name, entry in ((str(entry["lane"]), entry) for entry in metadata)
    }
    skip_nodes = set().union(*(set(entry["collection"]["skipped"]) for entry in metadata))
    try:
        reconciliation = reconcile_population(manifest, lane_nodes, skip_nodes)
    except Exception as exc:
        reconciliation = {
            "ok": False,
            "error": f"{exc.__class__.__name__}: {exc}",
            "lane_receipts": {name: sorted(nodes) for name, nodes in lane_nodes.items()},
        }
        if first_failure is None:
            first_failure = 2
            first_failure_lane = "runner"
            first_failure_reason = "population reconciliation failed"
        record_error("reconciliation", exc)
    persist("reconciliation")
    through_elapsed_seconds = time.monotonic() - started
    try:
        duration_exceeded = duration_exceeded or _duration_exceeded(through_elapsed_seconds)
    except Exception as exc:
        duration_exceeded = True
        record_error("duration-classification", exc)
    for entry in metadata:
        entry["timeout"]["duration_exceeded"] = duration_exceeded
    if duration_exceeded:
        deadline_triggered = True
    try:
        resources_clean, resource_residue = _resource_cleanup_verdict(metadata_by_lane)
    except Exception as exc:
        resources_clean, resource_residue = False, []
        if first_failure is None:
            first_failure = 2
            first_failure_lane = "runner"
            first_failure_reason = "resource reconciliation failed"
        record_error("resource-reconciliation", exc)
    cleanup_ok = (
        clean
        and resources_clean
        and all(entry["cleanup_result"] in {"owned-cleaned", "not-launched"} for entry in metadata)
    )
    if not resources_clean and first_failure is None:
        first_failure = 2
        first_failure_lane = "runner"
        first_failure_reason = "untrusted resource residue"
    try:
        result = _final_exit_code(interrupted, clean and resources_clean, first_failure, processes)
    except Exception as exc:
        result = first_failure or 2
        if first_failure is None:
            first_failure = result
            first_failure_lane = "runner"
            first_failure_reason = "final exit selection failed"
        record_error("exit-selection", exc)
    if duration_exceeded:
        result = TIMEOUT_EXIT_CODE
    elif result == 0 and not reconciliation["ok"]:
        result = 3
    if receipt_write_failed and result == 0:
        result = 2
    elapsed_seconds = time.monotonic() - started
    duration_exceeded = duration_exceeded or _duration_exceeded(elapsed_seconds)
    if duration_exceeded:
        result = TIMEOUT_EXIT_CODE
    payload.update(
        {
            "ended_at": time.time(),
            "elapsed_seconds": elapsed_seconds,
            "duration_exceeded": duration_exceeded,
            "deadline_triggered": deadline_triggered or duration_exceeded,
            "clean_children": clean,
            "reconciliation": reconciliation,
            "first_failure": first_failure,
            "first_failure_lane": first_failure_lane,
            "first_failure_reason": first_failure_reason,
            "final_exit_code": result,
        }
    )
    cleanup = payload["cleanup"]
    cleanup.update(
        {
            "verdict": "clean" if cleanup_ok else "untrusted",
            "through_elapsed_seconds": through_elapsed_seconds,
            "residue": resource_residue,
        }
    )
    persist("finalization")
    if receipt_write_failed and payload["final_exit_code"] == 0:
        payload["final_exit_code"] = 2
        result = 2
        persist("finalization-retry")
    if duration_exceeded:
        print(
            "full suite duration ceiling exceeded: "
            f"{elapsed_seconds:.2f}s > {MAX_FULL_SUITE_SECONDS:.2f}s",
            file=sys.stderr,
        )
        return TIMEOUT_EXIT_CODE
    if result:
        return result
    print(f"full suite passed in {elapsed_seconds:.2f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
