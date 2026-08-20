"""Governance policy for per-node test importance and deterministic selection."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from functools import cache
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = REPO_ROOT / "tests" / "fixtures" / "test_importance.json"
AUDIT_PATH = REPO_ROOT / "tests" / "AUDIT.md"
AUDIT_COST_RE = re.compile(r"^\| `([^`]+)` \| .* \| (?P<seconds>\d+\.\d+)s \|")
IMPORTANCE_LEVELS = ("critical", "high", "normal", "low")
IMPORTANCE_RANK = {
    "critical": 3,
    "high": 2,
    "normal": 1,
    "low": 0,
}
LANES = frozenset(("unit", "integration", "audit", "e2e", "bdd", "visual"))


@dataclass(frozen=True)
class DisabledCase:
    nodeid: str
    importance: str
    estimated_seconds: float
    lane: str | None = None


@dataclass(frozen=True)
class GovernancePolicy:
    version: str
    ceiling_seconds: float
    prior_known_seconds: float
    safety_margin_seconds: float
    lane_importance: dict[str, str]
    approved_disabled: tuple[DisabledCase, ...]
    pre_run_candidates: tuple[DisabledCase, ...]
    blocking_command: str
    expanded_command: str


@cache
def load_policy(path: Path = POLICY_PATH) -> GovernancePolicy:
    raw: Any = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise RuntimeError("test importance policy must be an object")
    levels = raw.get("importance_levels")
    if tuple(levels or ()) != IMPORTANCE_LEVELS:
        raise RuntimeError("test importance policy levels are invalid")
    lane_importance = raw.get("lane_importance")
    if not isinstance(lane_importance, dict) or set(lane_importance) != {
        "critical",
        "high",
        "normal",
    }:
        raise RuntimeError("test importance policy lane mapping is incomplete")
    if any(value not in IMPORTANCE_LEVELS for value in lane_importance.values()):
        raise RuntimeError("test importance policy contains unknown importance")
    cases: list[DisabledCase] = []
    for entry in raw.get("approved_disabled", []):
        if not isinstance(entry, dict):
            raise RuntimeError("approved disabled case must be an object")
        case = DisabledCase(
            nodeid=str(entry.get("nodeid", "")),
            importance=str(entry.get("importance", "")),
            estimated_seconds=float(entry.get("estimated_seconds", 0.0)),
            lane=str(entry["lane"]) if entry.get("lane") is not None else None,
        )
        if not case.nodeid or case.importance not in IMPORTANCE_LEVELS:
            raise RuntimeError("approved disabled case is incomplete")
        if case.estimated_seconds < 0:
            raise RuntimeError("approved disabled case cost cannot be negative")
        if case.lane is not None and case.lane not in LANES:
            raise RuntimeError("approved disabled case lane is invalid")
        cases.append(case)
    if len({case.nodeid for case in cases}) != len(cases):
        raise RuntimeError("approved disabled cases must be unique")
    candidates: list[DisabledCase] = []
    for entry in raw.get("pre_run_candidates", []):
        if not isinstance(entry, dict):
            raise RuntimeError("pre-run candidate must be an object")
        candidate = DisabledCase(
            nodeid=str(entry.get("nodeid", "")),
            importance=str(entry.get("importance", "")),
            estimated_seconds=float(entry.get("estimated_seconds", 0.0)),
            lane=str(entry["lane"]) if entry.get("lane") is not None else None,
        )
        if not candidate.nodeid or candidate.importance not in IMPORTANCE_LEVELS:
            raise RuntimeError("pre-run candidate is incomplete")
        if candidate.estimated_seconds <= 0:
            raise RuntimeError("pre-run candidate cost must be positive")
        if candidate.lane not in {"unit", "integration", "audit", "e2e", "bdd", "visual"}:
            raise RuntimeError("pre-run candidate lane is required and invalid")
        candidates.append(candidate)
    if len({case.nodeid for case in candidates}) != len(candidates):
        raise RuntimeError("pre-run candidates must be unique")
    if {case.nodeid for case in cases} & {case.nodeid for case in candidates}:
        raise RuntimeError("pre-run candidates cannot already be disabled")
    return GovernancePolicy(
        version=str(raw.get("version", "")),
        ceiling_seconds=float(raw.get("ceiling_seconds", 0.0)),
        prior_known_seconds=float(raw.get("prior_known_seconds", 0.0)),
        safety_margin_seconds=float(raw.get("safety_margin_seconds", 0.0)),
        lane_importance={str(key): str(value) for key, value in lane_importance.items()},
        approved_disabled=tuple(cases),
        pre_run_candidates=tuple(candidates),
        blocking_command=str(raw.get("blocking_command", "")),
        expanded_command=str(raw.get("expanded_command", "")),
    )


def classify_node(nodeid: str, lane: str | None = None) -> str:
    """Resolve explicit importance for one collected node; never default silently."""
    policy = load_policy()
    if nodeid in _approved_nodeids():
        return "low"
    candidate_importance = {case.nodeid: case.importance for case in policy.pre_run_candidates}.get(
        nodeid
    )
    if candidate_importance is not None:
        return candidate_importance
    path = nodeid.split("::", 1)[0]
    if path.startswith(("tests/e2e/", "tests/bdd/", "tests/visual/")):
        return "critical"
    if lane in {"integration", "bdd"} or path.startswith("tests/audit_integration/"):
        return policy.lane_importance["high"]
    if lane == "unit" or path.startswith("tests/scripts/") or path.startswith("tests/test_"):
        return policy.lane_importance["normal"]
    raise ValueError(f"unclassified test node: {nodeid}")


@cache
def _approved_nodeids() -> frozenset[str]:
    return frozenset(case.nodeid for case in load_policy().approved_disabled)


@cache
def load_known_costs(path: Path = AUDIT_PATH) -> dict[str, float]:
    """Load versioned per-node median costs from the audit manifest."""
    costs: dict[str, float] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        match = AUDIT_COST_RE.match(line)
        if match:
            costs[match.group(1)] = float(match["seconds"])
    if not costs:
        raise RuntimeError("audit manifest contains no per-node cost evidence")
    return costs


def current_blocking_candidates(
    lane_nodes: dict[str, set[str]],
) -> tuple[DisabledCase, ...]:
    """Return versioned candidates that are present in current blocking lanes."""
    policy = load_policy()
    current_nodes = set().union(*lane_nodes.values()) if lane_nodes else set()
    by_node = {candidate.nodeid: candidate for candidate in policy.pre_run_candidates}
    known_costs = load_known_costs()
    candidates: list[DisabledCase] = []
    for lane, nodes in lane_nodes.items():
        for nodeid in sorted(nodes & set(by_node)):
            if nodeid in _approved_nodeids():
                raise RuntimeError(f"pre-run candidate is already outside blocking lane: {nodeid}")
            declared = by_node[nodeid]
            classification = classify_node(nodeid, lane)
            if classification != declared.importance:
                raise RuntimeError(
                    f"pre-run importance mismatch for {nodeid}: "
                    f"declared={declared.importance}, resolved={classification}"
                )
            if nodeid not in known_costs:
                raise RuntimeError(f"missing cost evidence for pre-run candidate: {nodeid}")
            candidates.append(DisabledCase(nodeid, classification, known_costs[nodeid]))
    if {candidate.nodeid for candidate in candidates} != (set(by_node) & current_nodes):
        missing = sorted(set(by_node) - current_nodes)
        if missing:
            raise RuntimeError(f"pre-run candidates are not currently blocking: {missing}")
    return tuple(candidates)


def manifest_blocking_candidates(
    current_nodes: set[str] | frozenset[str],
) -> tuple[DisabledCase, ...]:
    """Resolve pre-run candidates from versioned manifest state, before launch."""
    policy = load_policy()
    approved = _approved_nodeids()
    missing = sorted(
        candidate.nodeid
        for candidate in policy.pre_run_candidates
        if candidate.nodeid not in current_nodes
    )
    if missing:
        raise RuntimeError(f"pre-run candidates are not in versioned manifest: {missing}")
    candidates = tuple(
        candidate for candidate in policy.pre_run_candidates if candidate.nodeid not in approved
    )
    for candidate in candidates:
        classification = classify_node(candidate.nodeid, candidate.lane)
        if classification != candidate.importance:
            raise RuntimeError(
                f"pre-run importance mismatch for {candidate.nodeid}: "
                f"declared={candidate.importance}, resolved={classification}"
            )
    return candidates


def classify_item(item: Any) -> str:
    lanes = {marker.name for marker in item.iter_markers()}
    lane = next(
        (candidate for candidate in ("integration", "unit", "bdd") if candidate in lanes),
        None,
    )
    return classify_node(item.nodeid, lane)


def select_lowest_importance_cases(
    predicted_seconds: float,
    candidates: tuple[DisabledCase, ...],
    *,
    ceiling_seconds: float,
    safety_margin_seconds: float = 0.0,
) -> tuple[DisabledCase, ...]:
    """Select cases before execution, using stable importance/cost/node ordering."""
    target_seconds = ceiling_seconds - safety_margin_seconds
    if target_seconds <= 0:
        raise ValueError("importance policy safety margin must leave positive headroom")
    if predicted_seconds <= target_seconds:
        return ()
    selected: list[DisabledCase] = []
    remaining = predicted_seconds
    ordered = sorted(
        candidates,
        key=lambda case: (IMPORTANCE_RANK[case.importance], -case.estimated_seconds, case.nodeid),
    )
    for case in ordered:
        if remaining <= target_seconds:
            break
        selected.append(case)
        remaining -= case.estimated_seconds
    if remaining > target_seconds:
        raise RuntimeError("importance policy cannot forecast a blocking lane within ceiling")
    return tuple(selected)


def validate_collected_items(items: list[Any]) -> dict[str, str]:
    """Return node classifications and fail loudly for any unclassified item."""
    classifications: dict[str, str] = {}
    for item in items:
        classification = classify_item(item)
        if classification not in IMPORTANCE_LEVELS:
            raise ValueError(f"invalid importance for {item.nodeid}: {classification}")
        classifications[item.nodeid] = classification
    return classifications
