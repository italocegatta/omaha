"""Build durable per-node T29 inventory from three taskipy profile runs."""

from __future__ import annotations

import argparse
import json
import math
import re
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from scripts.run_full_suite import load_manifest

ROOT = Path(__file__).resolve().parents[1]
LOG_RE = re.compile(
    r"^T29_PROFILE\s+(?P<seconds>\d+\.\d+)s\s+(?:setup|call|teardown)\s+"
    r"(?:(?:PASSED|SKIPPED|FAILED|ERROR)\s+)?(?P<node>tests/.*?::.*)$"
)
NODE_RE = re.compile(r"^\| `([^`]+)` \|")
LANES = ("unit", "integration", "audit", "e2e", "bdd", "visual")
EXPECTED_SKIPS = (
    "tests/test_dockerfile.py::test_docker_build_pro_image_succeeds",
    "tests/test_dockerfile.py::test_docker_run_pro_image_runs_as_omaha_user",
)
AUTHORIZED_REMOVALS = frozenset(
    {
        *(
            f"tests/visual/test_snapshots.py::test_{name}_snapshot[mobile]"
            for name in (
                "login",
                "patrimonio",
                "assets_table",
                "classes",
                "rebalance_form",
                "rebalance_plan",
                "import_form",
                "import_review",
                "rentabilidade_stub",
                "proventos_stub",
            )
        ),
        "tests/visual/test_snapshots.py::test_assets_table_snapshot[desktop]",
        "tests/visual/test_snapshots.py::test_classes_snapshot[desktop]",
    }
)
PROOF_DATA_ARGUMENT = "--proof-data"


@dataclass(frozen=True)
class ProofReceipt:
    stamp: str
    seconds: float
    population: int | None = None
    node_checksum: str | None = None
    skip_ids: tuple[str, ...] | None = None


def load_proof_data(path: Path) -> tuple[tuple[ProofReceipt, ...], tuple[str, ...]]:
    """Load owner-supplied proof receipts and coverage decisions."""
    try:
        data: Any = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"proof data must be valid JSON: {path}") from exc
    if not isinstance(data, dict):
        raise SystemExit("proof data must be a JSON object")
    raw_receipts = data.get("receipts")
    if "removed_nodes" not in data:
        raise SystemExit("proof data requires removed_nodes declaration")
    raw_removals = data["removed_nodes"]
    if not isinstance(raw_receipts, list) or not isinstance(raw_removals, list):
        raise SystemExit("proof data requires receipts and removed_nodes arrays")
    receipts: list[ProofReceipt] = []
    if len(raw_receipts) != 3:
        raise SystemExit("proof data requires exactly three receipts")
    for raw in raw_receipts:
        if (
            not isinstance(raw, dict)
            or not isinstance(raw.get("stamp"), str)
            or not raw["stamp"].strip()
        ):
            raise SystemExit("each proof receipt requires a non-empty string stamp")
        try:
            seconds = float(raw["seconds"])
        except (KeyError, TypeError, ValueError) as exc:
            raise SystemExit("each proof receipt requires numeric seconds") from exc
        if not math.isfinite(seconds) or seconds < 0 or seconds > 300:
            raise SystemExit(f"invalid proof receipt duration: {seconds!r}")
        if raw.get("status") not in ("passed", "green"):
            raise SystemExit(f"proof receipt is not green: {raw['stamp']}")
        if raw.get("clean_children") is not True:
            raise SystemExit(f"proof receipt has unclean children: {raw['stamp']}")
        population = raw.get("nodes", raw.get("population"))
        checksum = raw.get("node_checksum")
        skips = raw.get("skips", raw.get("skipped"))
        if not isinstance(population, int) or population < 1:
            raise SystemExit(f"proof receipt has invalid node count: {raw['stamp']}")
        if not isinstance(checksum, str) or not re.fullmatch(r"[0-9a-f]{64}", checksum):
            raise SystemExit(f"proof receipt has invalid node checksum: {raw['stamp']}")
        if not isinstance(skips, list) or tuple(skips) != EXPECTED_SKIPS:
            raise SystemExit(f"proof receipt has invalid skip data: {raw['stamp']}")
        receipts.append(ProofReceipt(raw["stamp"], seconds, population, checksum, tuple(skips)))
    if len({receipt.stamp for receipt in receipts}) != 3:
        raise SystemExit("proof receipt stamps must be unique")
    removals = tuple(raw_removals)
    if any(not isinstance(node, str) or not node.strip() for node in removals):
        raise SystemExit("removed_nodes must contain non-empty strings")
    if len(set(removals)) != len(removals):
        raise SystemExit("removed_nodes must be unique")
    if set(removals) != AUTHORIZED_REMOVALS:
        raise SystemExit("removed_nodes must exactly match authorized visual removals")
    return tuple(receipts), removals


def _proof_text(stamps: Sequence[str], receipts: Sequence[ProofReceipt] | None) -> str:
    if receipts is None:
        return "Proof receipts not supplied"
    receipt_stamps = tuple(receipt.stamp for receipt in receipts)
    if (
        len(receipts) != 3
        or len(stamps) != 3
        or len(set(stamps)) != 3
        or receipt_stamps != tuple(stamps)
    ):
        raise SystemExit("proof receipts must match the three supplied profile stamps")
    manifest = load_manifest(ROOT / "tests/AUDIT.md")
    for receipt in receipts:
        if (
            receipt.population != manifest.population
            or receipt.node_checksum != manifest.checksum
            or receipt.skip_ids != manifest.skip_ids
        ):
            raise SystemExit(f"proof receipt has invalid manifest data: {receipt.stamp}")
    if any(
        not math.isfinite(receipt.seconds) or not 0 <= receipt.seconds <= 300
        for receipt in receipts
    ):
        raise SystemExit("proof receipts must contain durations from 0 through 300 seconds")
    return (
        f"{len(receipts)}/{len(stamps)} proof receipts green ("
        + " / ".join(f"{receipt.seconds:.2f}s" for receipt in receipts)
        + "; no flake observed)"
    )


def _coverage_text(removed_nodes: Sequence[str]) -> str:
    if not removed_nodes:
        return "No owner-approved coverage removals supplied"
    if any(not isinstance(node, str) or not node.strip() for node in removed_nodes):
        raise SystemExit("removed_nodes must contain non-empty strings")
    if len(set(removed_nodes)) != len(removed_nodes):
        raise SystemExit("removed_nodes must be unique")
    if set(removed_nodes) != AUTHORIZED_REMOVALS:
        raise SystemExit("removed_nodes must exactly match authorized visual removals")
    return "Owner-approved coverage removals: " + ", ".join(f"`{node}`" for node in removed_nodes)


def normalize_node(node: str) -> str:
    node = node.replace("\\x3a", ":").removeprefix("./").strip()
    return node.split(" <- ", 1)[0]


def baseline_nodes() -> set[str]:
    return set(load_manifest(ROOT / "tests/AUDIT.md").nodes)


def profile_nodes(stamp: str) -> dict[str, float]:
    values: dict[str, float] = {}
    profile_dir = ROOT / "reports/test-profile"
    timing_files = [profile_dir / f"{stamp}-{name}.timings" for name in LANES]
    missing = [str(path) for path in timing_files if not path.is_file()]
    if missing:
        raise SystemExit(f"{stamp}: missing timing files: {missing}")
    for timing_file in timing_files:
        for line in timing_file.read_text(encoding="utf-8", errors="replace").splitlines():
            match = LOG_RE.match(line)
            if match:
                node = normalize_node(match["node"])
                if node in values:
                    raise SystemExit(f"{stamp}: duplicate timing for normalized node {node}")
                values[node] = float(match["seconds"])
    expected = baseline_nodes()
    actual = set(values)
    if actual != expected:
        missing_nodes = sorted(expected - actual)
        unexpected_nodes = sorted(actual - expected)
        raise SystemExit(
            f"{stamp}: profile node mismatch; missing={missing_nodes[:5]} "
            f"unexpected={unexpected_nodes[:5]}"
        )
    return values


def lane(node: str) -> str:
    if node.startswith("tests/bdd/test_workflow_contracts.py::"):
        return "unit + bdd"
    for name in ("audit_integration", "e2e", "bdd", "visual"):
        if node.startswith(f"tests/{name}/"):
            return name
    return "unit/integration"


def contract(node: str) -> str:
    path = node.split("::", 1)[0]
    if path.startswith(("tests/e2e/", "tests/bdd/")):
        return "Browser workflow and user-visible contract"
    if path.startswith("tests/visual/"):
        return "Visual regression screenshot contract"
    if path.startswith("tests/audit_integration/"):
        return "Audit/report integration contract"
    return "Unit or integration behavior contract"


def build(
    stamps: list[str],
    proof_receipts: Sequence[ProofReceipt] | None = None,
    removed_nodes: Sequence[str] = (),
) -> str:
    expected = baseline_nodes()
    profiles = [profile_nodes(stamp) for stamp in stamps]
    for stamp, profile in zip(stamps, profiles, strict=True):
        actual = set(profile)
        if actual != expected:
            missing = sorted(expected - actual)
            unexpected = sorted(actual - expected)
            raise SystemExit(
                f"{stamp}: profile node mismatch; missing={missing[:5]} unexpected={unexpected[:5]}"
            )
    nodes = sorted(expected)
    proof_text = _proof_text(stamps, proof_receipts)
    coverage_text = _coverage_text(removed_nodes)
    lines = [
        "# Test Suite Audit Manifest",
        "",
        "Generated from three taskipy profile repetitions by `scripts/build_test_inventory.py`.",
        f"All {len(expected):,} collected nodes are retained. {coverage_text}.",
        "",
        "## Summary",
        "",
        f"- **Total nodes:** {len(expected):,}",
        "- **Skipped nodes:** 2",
        f"- **Profile repetitions:** {len(stamps)}",
        f"- **Flake evidence:** {proof_text}",
        "",
        "## Inventory",
        "",
        "| Node | Lane | Median duration | Protected behavior/contract | Overlap | "
        "Flake evidence | Category | Recommendation |",
        "|---|---|---:|---|---|---|---|---|",
    ]
    for node in nodes:
        values = sorted(profile[node] for profile in profiles)
        median = values[1]
        overlap = (
            "unit + bdd intentional contract overlap"
            if lane(node) == "unit + bdd"
            else "None identified"
        )
        lines.append(
            f"| `{node}` | {lane(node)} | {median:.3f}s | {contract(node)} | "
            f"{overlap} | {proof_text} | retain | {coverage_text} |"
        )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("stamps", nargs=3, help="three run timestamps in reports/test-profile")
    parser.add_argument(
        PROOF_DATA_ARGUMENT,
        type=Path,
        required=True,
        help="JSON file with exact proof receipts and removals",
    )
    args = parser.parse_args()
    receipts, removals = load_proof_data(args.proof_data)
    (ROOT / "tests/AUDIT.md").write_text(build(args.stamps, receipts, removals), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
