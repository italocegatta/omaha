"""Run all canonical test lanes concurrently with failure-safe cleanup."""

from __future__ import annotations

import hashlib
import json
import os
import re
import signal
import socket
import subprocess
import sys
import time
from contextlib import suppress
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
REPORT_DIR = REPO_ROOT / "reports" / "test-profile"
GRACE_SECONDS = 10.0
LANES = (
    ("unit", "test-unit"),
    ("integration", "test-integration"),
    ("audit", "test-audit-integration"),
    ("e2e", "test-e2e"),
    ("bdd", "test-bdd"),
    ("visual", "test-visual"),
)
PORTS = (8765, 8766, 8767, 8768)
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
BASELINE_AUDIT = REPO_ROOT / "tests" / "AUDIT.md"
MANIFEST_PATH = BASELINE_AUDIT
BASELINE_NODE_RE = re.compile(r"^\| `([^`]+)` \|")
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
    if population is None or checksum is None or len(nodes) != population:
        raise RuntimeError(
            f"T29 manifest population mismatch: declared={population}, nodes={len(nodes)}"
        )
    if _node_checksum(nodes) != checksum:
        raise RuntimeError("T29 manifest checksum mismatch")
    if set(lane_checksums) != {name for name, _ in LANES}:
        raise RuntimeError("T29 manifest lane checksums incomplete")
    return Manifest(nodes, checksum, population, lane_checksums, EXPECTED_SKIPS)


def _lane_environment(name: str) -> dict[str, str]:
    """Return process environment carrying one lane's receipt scope."""
    return {**os.environ, "T29_DB_RECEIPT_LANE": name}


def _runtime_child_command(task: str) -> list[str]:
    """Build runtime lane command with uncaptured receipt output."""
    return ["uv", "run", "task", task, "--", "-s", "-p", "test_profile_plugin"]


def _normalize_node(node: str) -> str:
    """Normalize pytest's BDD output without changing node identity."""
    node = node.replace("\\x3a", ":").strip()
    node = node.split(" <- ", 1)[0]
    if node.startswith("./"):
        node = node[2:]
    return node


def _baseline_nodes() -> set[str]:
    return set(load_manifest().nodes)


def _preflight() -> None:
    database_url = os.environ.get("DATABASE_URL", "")
    if "data/portfolio.db" in database_url or database_url.endswith("/data/portfolio.db"):
        raise RuntimeError("refusing full test run with production DATABASE_URL")
    for port in PORTS:
        with socket.socket() as probe:
            probe.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                probe.bind(("127.0.0.1", port))
            except OSError as exc:
                raise RuntimeError(f"test lane port {port} is unavailable") from exc
    for lane, targets in LANE_DATABASES.items():
        for target in targets:
            if isinstance(target, Path) and (
                target.parent != REPO_ROOT / "data" or target.name == "portfolio.db"
            ):
                raise RuntimeError(f"unrecognized {lane} database target: {target}")


def _preflight_lane(name: str, task: str) -> tuple[set[str], set[str], list[str]]:
    """Collect lane and report its child-configured DB target before launch."""
    env = _lane_environment(name)
    env["PYTHONPATH"] = os.pathsep.join(
        filter(None, [str(REPO_ROOT / "scripts"), str(REPO_ROOT), env.get("PYTHONPATH", "")])
    )
    result = subprocess.run(
        [
            "uv",
            "run",
            "task",
            task,
            "--",
            "--collect-only",
            "-q",
            "-s",
            "-p",
            "scripts.t29_collection_plugin",
        ],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
    )
    output = result.stdout + result.stderr
    if result.returncode != 0:
        raise RuntimeError(f"{name} collection preflight failed ({result.returncode})")
    targets = [str(Path(value).resolve()) for value in DB_RE.findall(output)]
    _validate_db_targets(name, targets)
    nodes = {
        _normalize_node(line.removeprefix("T29_NODE ").strip())
        for line in output.splitlines()
        if line.startswith("T29_NODE ")
    }
    return nodes, set(), targets


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


def _stop(processes: dict[str, subprocess.Popen[str]], sig: int) -> None:
    for process in processes.values():
        if process.poll() is None:
            with suppress(ProcessLookupError):
                os.killpg(process.pid, sig)


def _reap(processes: dict[str, subprocess.Popen[str]]) -> bool:
    deadline = time.monotonic() + GRACE_SECONDS
    while time.monotonic() < deadline and any(p.poll() is None for p in processes.values()):
        time.sleep(0.1)
    survivors = [p for p in processes.values() if p.poll() is None]
    for process in survivors:
        with suppress(ProcessLookupError):
            os.killpg(process.pid, signal.SIGKILL)
    for process in processes.values():
        process.wait()
    return not survivors


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
    lane_mismatches = {}
    for lane, nodes in lane_nodes.items():
        actual_checksum = _node_checksum(nodes)
        if actual_checksum != manifest.lane_checksums.get(lane):
            lane_mismatches[lane] = {
                "expected": manifest.lane_checksums.get(lane),
                "actual": actual_checksum,
            }
    result = {
        "expected_nodes": manifest.population,
        "actual_nodes": len(all_nodes),
        "duplicate_nodes": duplicate_nodes,
        "missing_lanes": missing_lanes,
        "unexpected_lanes": unexpected_lanes,
        "missing_nodes": sorted(manifest.nodes - all_nodes),
        "unexpected_nodes": sorted(all_nodes - manifest.nodes),
        "lane_mismatches": lane_mismatches,
        "expected_skips": list(manifest.skip_ids),
        "actual_skips": sorted(skip_nodes),
        "skip_mismatch": check_skips and sorted(skip_nodes) != list(manifest.skip_ids),
    }
    result["ok"] = (
        actual_lanes == expected_lanes
        and len(all_nodes) == manifest.population
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


def main() -> int:
    started = time.monotonic()
    try:
        _preflight()
    except RuntimeError as exc:
        print(f"full-suite preflight failed: {exc}", file=sys.stderr)
        return 2
    try:
        manifest = load_manifest()
        preflight = {name: _preflight_lane(name, task) for name, task in LANES}
        preflight_reconciliation = reconcile_preflight(
            manifest,
            {name: nodes for name, (nodes, _, _) in preflight.items()},
        )
        if not preflight_reconciliation["ok"]:
            raise RuntimeError(f"collection reconciliation failed: {preflight_reconciliation}")
    except RuntimeError as exc:
        print(f"full-suite lane preflight failed: {exc}", file=sys.stderr)
        return 2
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%dT%H%M%S", time.localtime())
    processes: dict[str, subprocess.Popen[str]] = {}
    metadata: list[dict[str, object]] = []
    interrupted: int | None = None
    first_failure: int | None = None
    stopping = False

    def handle_signal(signum: int, _frame: object) -> None:
        nonlocal interrupted, stopping
        if stopping:
            return
        interrupted, stopping = signum, True
        _stop(processes, signum)

    previous = {sig: signal.getsignal(sig) for sig in (signal.SIGINT, signal.SIGTERM)}
    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)
    try:
        for name, task in LANES:
            log_path = REPORT_DIR / f"{stamp}-{name}.log"
            timing_path = REPORT_DIR / f"{stamp}-{name}.timings"
            log = log_path.open("w", encoding="utf-8")
            child_env = _lane_environment(name)
            child_env["PYTHONPATH"] = os.pathsep.join(
                filter(None, [str(REPO_ROOT / "scripts"), child_env.get("PYTHONPATH", "")])
            )
            child_env["T29_PROFILE_PATH"] = str(timing_path)
            child_env["T29_DB_RECEIPT_LANE"] = name
            process = subprocess.Popen(
                _runtime_child_command(task),
                cwd=REPO_ROOT,
                env=child_env,
                stdout=log,
                stderr=subprocess.STDOUT,
                start_new_session=True,
                text=True,
            )
            log.close()
            processes[name] = process
            metadata.append(
                {
                    "lane": name,
                    "task": f"uv run task {task}",
                    "pid": process.pid,
                    "log": str(log_path),
                    "timings": str(timing_path),
                    "started_at": time.time(),
                }
            )
        while any(process.poll() is None for process in processes.values()):
            if interrupted is not None:
                break
            failed = next(
                (name for name, process in processes.items() if process.poll() not in (None, 0)),
                None,
            )
            if failed is not None:
                first_failure = processes[failed].returncode
                if first_failure == 0 or first_failure is None:
                    first_failure = 1
                stopping = True
                _stop(processes, signal.SIGTERM)
                break
            time.sleep(0.2)
    finally:
        clean = _reap(processes)
        for sig, handler in previous.items():
            signal.signal(sig, handler)
    for entry in metadata:
        process = processes[str(entry["lane"])]
        output = Path(str(entry["log"])).read_text(encoding="utf-8", errors="replace")
        timing_path = Path(str(entry["timings"]))
        timing_output = (
            timing_path.read_text(encoding="utf-8", errors="replace")
            if timing_path.exists()
            else ""
        )
        collection = _collection(output, timing_output)
        db_targets = [str(Path(value).resolve()) for value in DB_RE.findall(output)]
        try:
            _validate_db_targets(str(entry["lane"]), db_targets)
            if str(entry["lane"]) in {"unit", "integration"} and not collection["nodes"]:
                raise RuntimeError(f"{entry['lane']} published empty collection receipt")
        except RuntimeError as exc:
            entry["receipt_error"] = str(exc)
            if first_failure is None:
                first_failure = 2
        entry.update(
            {
                "exit_code": process.returncode,
                "ended_at": time.time(),
                "summary": _summary(output),
                "collection": collection,
                "db_targets": db_targets,
            }
        )
        print(f"[{entry['lane']}] exit={process.returncode} log={entry['log']}")
    lane_nodes = {
        name: set(entry["collection"]["nodes"])
        for name, entry in ((str(entry["lane"]), entry) for entry in metadata)
    }
    skip_nodes = set().union(*(set(entry["collection"]["skipped"]) for entry in metadata))
    reconciliation = reconcile_population(manifest, lane_nodes, skip_nodes)
    payload = {
        "started_at": started,
        "ended_at": time.monotonic(),
        "lanes": metadata,
        "clean_children": clean,
        "preflight": {
            name: {"nodes": len(nodes), "db_targets": targets}
            for name, (nodes, _, targets) in preflight.items()
        },
        "preflight_reconciliation": preflight_reconciliation,
        "reconciliation": reconciliation,
    }
    (REPORT_DIR / f"{stamp}-run.json").write_text(json.dumps(payload, indent=2) + "\n")
    result = _final_exit_code(interrupted, clean, first_failure, processes)
    if result:
        return result
    if not reconciliation["ok"]:
        print(f"full-suite population reconciliation failed: {reconciliation}", file=sys.stderr)
        return 3
    print(f"full suite passed in {time.monotonic() - started:.2f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
