"""Serial BDD replay helper for late-suite harness debugging.

Rebuilds the BDD test DB from scratch, then runs either:

- one scenario via ``-k <name>``; or
- an ordered prefix from ``--after <file>`` followed by the target.

``--trace`` enables Playwright tracing via the shared browser fixtures.
Successful tests discard the trace; failing tests keep ``.zip`` artifacts
under ``tmp/bdd-traces/``.
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
BDD_DB_PATH = REPO_ROOT / "data" / "test_bdd.db"
TEST_ADMIN_PASSWORD = "test-password"
TEST_SECRET_KEY = "test-secret-bdd-do-not-use-in-prod"
TRACE_DIR_ENV_VAR = "OMAHA_E2E_TRACE_DIR"
UV_RUN = ["uv", "run"]

BDD_TEST_FILE = "tests/bdd/test_scenarios.py"
COLLECT_ORDER_CMD = [
    *UV_RUN,
    "pytest",
    BDD_TEST_FILE,
    "--collect-only",
    "-vv",
]


def _collect_nodeids() -> list[str]:
    completed = subprocess.run(
        COLLECT_ORDER_CMD,
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        raise SystemExit(completed.returncode)
    nodeids: list[str] = []
    for line in completed.stdout.splitlines():
        match = re.search(r"<Function\s+([^>]+)>", line)
        if match:
            nodeids.append(f"{BDD_TEST_FILE}::{match.group(1)}")
    return nodeids


def _resolve_target(name: str, collected: list[str]) -> str:
    if name in collected:
        return name
    matches = [nodeid for nodeid in collected if name in nodeid]
    if len(matches) == 1:
        return matches[0]
    if not matches:
        raise SystemExit(f"No collected BDD test matched: {name}")
    raise SystemExit(
        "Multiple collected BDD tests matched "
        f"{name!r}: {', '.join(matches)}. Use exact nodeid."
    )


def _load_prefix(prefix_file: Path, collected: list[str]) -> list[str]:
    lines = [line.strip() for line in prefix_file.read_text().splitlines()]
    prefix: list[str] = []
    for line in lines:
        if not line or line.startswith("#"):
            continue
        prefix.append(_resolve_target(line, collected))
    return prefix


def _rebuild_bdd_db() -> None:
    BDD_DB_PATH.unlink(missing_ok=True)
    env = {
        **os.environ,
        "DATABASE_URL": f"sqlite:///{BDD_DB_PATH}",
        "ADMIN_PASSWORD": TEST_ADMIN_PASSWORD,
        "SECRET_KEY": TEST_SECRET_KEY,
        "OMAHA_SKIP_STARTUP": "1",
    }
    subprocess.run(
        [*UV_RUN, "alembic", "upgrade", "head"],
        cwd=REPO_ROOT,
        env=env,
        check=True,
    )
    subprocess.run(
        [*UV_RUN, "python", "-m", "omaha.seed"],
        cwd=REPO_ROOT,
        env=env,
        check=True,
    )


def _trace_dir_for_run() -> Path:
    stamp = time.strftime("%Y%m%d-%H%M%S")
    trace_dir = REPO_ROOT / "tmp" / "bdd-traces" / stamp
    trace_dir.mkdir(parents=True, exist_ok=True)
    return trace_dir


def _pytest_command(args: argparse.Namespace, collected: list[str]) -> list[str]:
    target = _resolve_target(args.name, collected)
    if args.after is None:
        return [
            *UV_RUN,
            "pytest",
            target,
            "--no-header",
            "-v",
            "-p",
            "no:cacheprovider",
        ]

    prefix = _load_prefix(args.after, collected)
    ordered = [nodeid for nodeid in prefix if nodeid != target]
    ordered.append(target)
    return [
        *UV_RUN,
        "pytest",
        "--no-header",
        "-v",
        "-p",
        "no:cacheprovider",
        *ordered,
    ]


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("name", help="BDD test substring or exact collected nodeid")
    parser.add_argument(
        "--after",
        type=Path,
        help="File with ordered prefix nodeids to run before target in same pytest invocation",
    )
    parser.add_argument(
        "--trace",
        action="store_true",
        help="Keep Playwright trace zip for failing tests under tmp/bdd-traces/",
    )
    return parser


def main() -> int:
    parser = _build_parser()
    args = parser.parse_args()
    collected = _collect_nodeids()
    _resolve_target(args.name, collected)

    start = time.monotonic()
    _rebuild_bdd_db()

    env = os.environ.copy()
    trace_dir: Path | None = None
    if args.trace:
        trace_dir = _trace_dir_for_run()
        env[TRACE_DIR_ENV_VAR] = str(trace_dir)
        print(f"[omaha-test-harness] trace dir: {trace_dir}")

    command = _pytest_command(args, collected)
    completed = subprocess.run(command, cwd=REPO_ROOT, env=env, check=False)
    elapsed = time.monotonic() - start
    verdict = "PASS" if completed.returncode == 0 else "FAIL"
    print(f"[omaha-test-harness] {verdict} in {elapsed:.1f}s")
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
