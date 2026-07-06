"""Capture the current mutation score to `.mutmut-baseline`.

Reads `mutants/<path>.meta` JSON files produced by mutmut3, computes
the same counts/killed_share as `scripts/mutation_report.py`, and
writes a plain-text baseline file that downstream `diff` calls can
parse. The file is committed to the repo so future mutation runs
have a stable comparison anchor.

Scope: implementation of
`openspec/specs/rebalance-mutation-testing/spec.md` §"Baseline of
mutation results is captured in a committable file".
"""

from __future__ import annotations

import sys
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

from scripts.mutation_report import collect_counts

BASELINE_PATH = Path(".mutmut-baseline")


def render_baseline(counts: Counter, generated_at: datetime) -> str:
    killed = counts.get("killed", 0)
    survived = counts.get("survived", 0)
    no_tests = counts.get("no_tests", 0)
    timeout = counts.get("timeout", 0)
    skipped = counts.get("skipped", 0)
    denominator = killed + survived
    killed_share = (killed / denominator) if denominator else 0.0
    return (
        f"killed={killed}\n"
        f"survived={survived}\n"
        f"no_tests={no_tests}\n"
        f"timeout={timeout}\n"
        f"skipped={skipped}\n"
        f"killed_share={killed_share:.3f}\n"
        f"generated_at={generated_at.isoformat()}\n"
    )


def main() -> int:
    mutants_dir = Path("mutants")
    counts = collect_counts(mutants_dir)
    if sum(counts.values()) == 0:
        sys.stderr.write("no mutation cache found; run task mutation first\n")
        return 1
    baseline = render_baseline(counts, datetime.now(UTC))
    BASELINE_PATH.write_text(baseline, encoding="utf-8")
    sys.stdout.write(f"wrote {BASELINE_PATH}\n{baseline}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
