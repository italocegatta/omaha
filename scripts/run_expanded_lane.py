"""Run every versioned T32 outside-lane case, including pre-run selections."""

from __future__ import annotations

import subprocess

from scripts.run_full_suite import REPO_ROOT
from scripts.test_governance import load_policy, select_lowest_importance_cases


def main() -> int:
    policy = load_policy()
    selected = select_lowest_importance_cases(
        policy.prior_known_seconds,
        policy.pre_run_candidates,
        ceiling_seconds=policy.ceiling_seconds,
        safety_margin_seconds=policy.safety_margin_seconds,
    )
    expanded_unit_cases = tuple(dict.fromkeys((*selected, *policy.pre_run_candidates)))
    visual = subprocess.run(
        ["uv", "run", "task", "test-visual-pruned"],
        cwd=REPO_ROOT,
        check=False,
    )
    if visual.returncode:
        return visual.returncode
    return subprocess.run(
        [
            "uv",
            "run",
            "pytest",
            "--no-cov",
            "-q",
            *(case.nodeid for case in expanded_unit_cases),
        ],
        cwd=REPO_ROOT,
        check=False,
    ).returncode


if __name__ == "__main__":
    raise SystemExit(main())
