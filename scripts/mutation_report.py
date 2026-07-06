"""Render mutation results from `mutmut run` to stdout.

Reads the per-source-file metadata produced by mutmut3 (one
`mutants/<path>.meta` JSON per mutated file). Computes counts and
the killed share, prints a one-line summary + per-status block.

Scope: implementation of
`openspec/specs/rebalance-mutation-testing/spec.md` §"Mutation
report is human-readable via task wrapper". Keep the contract
minimal — any new output format belongs in a new task/script,
not here.
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

# Exit codes mapped to statuses — mirrors mutmut3's `status_by_exit_code`
# in `mutmut/__main__.py`. Sync if upstream changes.
STATUS_BY_EXIT_CODE: dict[int | None, str] = {
    1: "killed",
    3: "killed",
    -24: "killed",
    0: "survived",
    5: "no_tests",
    33: "no_tests",
    2: "interrupted",
    None: "not_checked",
    34: "skipped",
    35: "suspicious",
    36: "timeout",
    37: "caught_by_type_check",
    24: "timeout",
    152: "timeout",
    255: "timeout",
    -11: "segfault",
    -9: "segfault",
}

# Statuses the spec contracts on. Others are reported but not required
# for the kill-rate denominator (e.g. `segfault`, `suspicious`,
# `caught_by_type_check` are signs of harness problems, not test gaps).
SPEC_STATUSES = ("killed", "survived", "no_tests", "timeout", "skipped")


def collect_counts(mutants_dir: Path) -> Counter:
    counts: Counter = Counter()
    if not mutants_dir.is_dir():
        return counts
    for meta_path in mutants_dir.glob("**/*.meta"):
        try:
            data = json.loads(meta_path.read_text("utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        for exit_code in data.get("exit_code_by_key", {}).values():
            status = STATUS_BY_EXIT_CODE.get(exit_code, "unknown")
            counts[status] += 1
    return counts


def render(counts: Counter, *, out=sys.stdout) -> int:
    total = sum(counts.values())
    if total == 0:
        out.write("no mutation cache found; run task mutation first\n")
        return 1

    killed = counts.get("killed", 0)
    survived = counts.get("survived", 0)
    no_tests = counts.get("no_tests", 0)
    timeout = counts.get("timeout", 0)
    skipped = counts.get("skipped", 0)
    denominator = killed + survived
    killed_share = (killed / denominator) if denominator else 0.0

    out.write(f"mutation testing report — {total} mutants\n")
    out.write(f"  killed      = {killed}\n")
    out.write(f"  survived    = {survived}\n")
    out.write(f"  no_tests    = {no_tests}\n")
    out.write(f"  timeout     = {timeout}\n")
    out.write(f"  skipped     = {skipped}\n")
    out.write(f"  killed_share = {killed_share:.3f}\n")
    for status, count in sorted(counts.items()):
        if status in SPEC_STATUSES:
            continue
        out.write(f"  {status:<24}= {count}\n")
    return 0


def main() -> int:
    mutants_dir = Path("mutants")
    counts = collect_counts(mutants_dir)
    return render(counts)


if __name__ == "__main__":
    raise SystemExit(main())
