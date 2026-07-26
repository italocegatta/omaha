"""Focused generator tests using durable proof and decision fixtures."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts import build_test_inventory as inventory
from scripts.run_full_suite import Manifest

CHECKSUM = "a" * 64
REAL_CHECKSUM = "a77e2a45fa2ff6c9854a945870f0489c54c332aa2a3dd4845970e256f06d40c8"
STAMPS = ["run-1", "run-2", "run-3"]
REMOVALS = sorted(inventory.AUTHORIZED_REMOVALS)
REAL_STAMPS = ["20260726T190307", "20260726T190824", "20260726T191307"]


def _manifest(nodes: set[str]) -> Manifest:
    return Manifest(frozenset(nodes), CHECKSUM, 1043, {}, inventory.EXPECTED_SKIPS)


def _receipt(stamp: str, **overrides: object) -> dict[str, object]:
    value: dict[str, object] = {
        "stamp": stamp,
        "seconds": 280.98,
        "status": "passed",
        "clean_children": True,
        "nodes": 1043,
        "node_checksum": CHECKSUM,
        "skips": list(inventory.EXPECTED_SKIPS),
    }
    value.update(overrides)
    return value


def _proof_data(**overrides: object) -> dict[str, object]:
    value: dict[str, object] = {
        "receipts": [_receipt(stamp) for stamp in STAMPS],
        "removed_nodes": REMOVALS,
    }
    value.update(overrides)
    return value


def test_build_uses_supplied_proof_receipts_and_removals(monkeypatch: pytest.MonkeyPatch) -> None:
    nodes = {"tests/test_example.py::test_one"}
    monkeypatch.setattr(inventory, "baseline_nodes", lambda: nodes)
    monkeypatch.setattr(inventory, "load_manifest", lambda _path: _manifest(nodes))
    monkeypatch.setattr(
        inventory,
        "profile_nodes",
        lambda stamp: {"tests/test_example.py::test_one": float(len(stamp))},
    )

    receipts = tuple(
        inventory.ProofReceipt(stamp, 280.98, 1043, CHECKSUM, inventory.EXPECTED_SKIPS)
        for stamp in STAMPS
    )
    output = inventory.build(STAMPS, receipts, REMOVALS)

    assert "3/3 proof receipts green" in output
    assert "test_assets_table_snapshot[desktop]" in output


def test_load_proof_data_accepts_complete_fixture(tmp_path: Path) -> None:
    path = tmp_path / "receipts.json"
    path.write_text(json.dumps(_proof_data()), encoding="utf-8")

    receipts, removals = inventory.load_proof_data(path)

    assert [receipt.seconds for receipt in receipts] == [280.98] * 3
    assert removals == tuple(REMOVALS)


def test_load_proof_data_accepts_current_receipt_artifact() -> None:
    path = Path(__file__).parents[1] / "tests" / "fixtures" / "t29_proof_receipts.json"

    receipts, removals = inventory.load_proof_data(path)

    assert [receipt.stamp for receipt in receipts] == REAL_STAMPS
    assert [receipt.seconds for receipt in receipts] == [280.98, 276.10, 274.77]
    assert all(receipt.node_checksum == REAL_CHECKSUM for receipt in receipts)
    assert set(removals) == inventory.AUTHORIZED_REMOVALS


@pytest.mark.parametrize(
    "change",
    [
        {"_remove_key": "removed_nodes"},
        {"removed_nodes": []},
        {"removed_nodes": REMOVALS[:-1]},
        {"removed_nodes": [*REMOVALS, REMOVALS[0]]},
        {"removed_nodes": [*REMOVALS[:-1], "not-a-visual-node"]},
        {"removed_nodes": [*REMOVALS[:-1], 42]},
    ],
    ids=["missing", "empty", "incomplete", "duplicate", "unknown", "malformed"],
)
def test_load_proof_data_rejects_invalid_removal_declarations(tmp_path: Path, change: dict) -> None:
    path = tmp_path / "receipts.json"
    proof_data = _proof_data(
        **{key: value for key, value in change.items() if key != "_remove_key"}
    )
    if "_remove_key" in change:
        proof_data.pop(change["_remove_key"])
    path.write_text(json.dumps(proof_data), encoding="utf-8")

    with pytest.raises(SystemExit, match="removed_nodes"):
        inventory.load_proof_data(path)


@pytest.mark.parametrize(
    "change",
    [
        {"receipts": [_receipt("run-1"), _receipt("run-2")]},
        {"receipts": [_receipt("run-1"), _receipt("run-2"), _receipt("run-2")]},
        {"receipts": [_receipt("run-1", status=None), _receipt("run-2"), _receipt("run-3")]},
        {
            "receipts": [
                _receipt("run-1", clean_children=None),
                _receipt("run-2"),
                _receipt("run-3"),
            ]
        },
        {
            "receipts": [
                _receipt("run-1", node_checksum="bad"),
                _receipt("run-2"),
                _receipt("run-3"),
            ]
        },
        {"receipts": [_receipt("run-1", skips=[]), _receipt("run-2"), _receipt("run-3")]},
    ],
    ids=[
        "count",
        "duplicate-stamp",
        "missing-status",
        "missing-clean-children",
        "checksum",
        "skips",
    ],
)
def test_load_proof_data_rejects_invalid_receipts(tmp_path: Path, change: dict) -> None:
    path = tmp_path / "receipts.json"
    path.write_text(json.dumps(_proof_data(**change)), encoding="utf-8")

    with pytest.raises(SystemExit):
        inventory.load_proof_data(path)


def test_cli_regeneration_path_writes_audit(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    nodes = {"tests/test_example.py::test_one"}
    output_dir = tmp_path / "tests"
    output_dir.mkdir()
    monkeypatch.setattr(inventory, "ROOT", tmp_path)
    monkeypatch.setattr(inventory, "baseline_nodes", lambda: nodes)
    monkeypatch.setattr(inventory, "load_manifest", lambda _path: _manifest(nodes))
    monkeypatch.setattr(inventory, "profile_nodes", lambda _stamp: {next(iter(nodes)): 0.1})
    proof_path = tmp_path / "proof.json"
    proof_path.write_text(json.dumps(_proof_data()), encoding="utf-8")
    monkeypatch.setattr(
        sys,
        "argv",
        ["build_test_inventory.py", *STAMPS, "--proof-data", str(proof_path)],
    )

    assert inventory.main() == 0
    assert (output_dir / "AUDIT.md").is_file()
    assert "3/3 proof receipts green" in (output_dir / "AUDIT.md").read_text()


def test_cli_regeneration_path_accepts_current_receipt_artifact(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    nodes = {"tests/test_example.py::test_one"}
    output_dir = tmp_path / "tests"
    output_dir.mkdir()
    monkeypatch.setattr(inventory, "ROOT", tmp_path)
    monkeypatch.setattr(inventory, "baseline_nodes", lambda: nodes)
    monkeypatch.setattr(
        inventory,
        "load_manifest",
        lambda _path: Manifest(frozenset(nodes), REAL_CHECKSUM, 1043, {}, inventory.EXPECTED_SKIPS),
    )
    monkeypatch.setattr(inventory, "profile_nodes", lambda _stamp: {next(iter(nodes)): 0.1})
    proof_path = Path(__file__).parents[1] / "tests" / "fixtures" / "t29_proof_receipts.json"
    monkeypatch.setattr(
        sys,
        "argv",
        ["build_test_inventory.py", *REAL_STAMPS, "--proof-data", str(proof_path)],
    )

    assert inventory.main() == 0
    audit = (output_dir / "AUDIT.md").read_text()
    assert "280.98s / 276.10s / 274.77s" in audit


def test_cli_rejects_missing_proof_data(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sys, "argv", ["build_test_inventory.py", *STAMPS])

    with pytest.raises(SystemExit):
        inventory.main()


def test_cli_rejects_invalid_proof_data(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    proof_path = tmp_path / "invalid-proof.json"
    proof_path.write_text("not json", encoding="utf-8")
    monkeypatch.setattr(
        sys,
        "argv",
        ["build_test_inventory.py", *STAMPS, "--proof-data", str(proof_path)],
    )

    with pytest.raises(SystemExit, match="valid JSON"):
        inventory.main()
