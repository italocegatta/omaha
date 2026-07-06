"""CSV row loaders + row-parsing helpers for the CSV-driven seed path.

Reads the per-profile triplet under ``data/seed/`` and produces
frozen dataclasses for each layer:

* ``load_classes`` → list[:class:`ClassRow`]
* ``load_assets``  → list[:class:`AssetRow`]
* ``load_positions`` → list[:class:`PositionRow`]

All three honour the documented headers (see ``data/seed/README.md``)
and abort with a clear error before any DB write if the header is
wrong, a value is out of range, or a row duplicates an existing key.

The broker-published ``total_invested`` / ``total_current`` columns
on the position CSV are inserted verbatim into
``Position.total_invested`` / ``Position.total_current`` — the
seed script never falls back to ``qty * price``.
"""

from __future__ import annotations

import csv
import sys
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path

import scripts.seed_from_csv
from omaha.models import QuoteKind

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
# Canonical value lives here; the package re-exports it via ``__init__``.
# ``scripts.seed_from_csv.SEED_DIR`` is resolved at call time so that
# tests which patch ``seed_mod.SEED_DIR`` (see
# ``tests/test_seed_from_csv.py:665``) flow through naturally.
SEED_DIR = REPO_ROOT / "data" / "seed"

PROFILES = ("italo", "ana")

CLASS_HEADER = ("name", "target_pct", "display_order", "quote_kind")
ASSET_HEADER = (
    "class_name",
    "name",
    "target_pct",
    "display_order",
    "buy_enabled",
    "sell_enabled",
    "currency_code",
)
POSITION_HEADER = (
    "asset_name",
    "broker_ticker",
    "qty",
    "avg_price",
    "current_price",
    "total_invested",
    "total_current",
)

VALID_QUOTE_KINDS = frozenset({q.value for q in QuoteKind})
VALID_CURRENCY_CODES = frozenset({"BRL", "USD"})


@dataclass(frozen=True)
class ClassRow:
    name: str
    target_pct: Decimal
    display_order: int
    quote_kind: str
    line_no: int


@dataclass(frozen=True)
class AssetRow:
    class_name: str
    name: str
    target_pct: Decimal
    display_order: int
    buy_enabled: bool
    sell_enabled: bool
    currency_code: str
    line_no: int


@dataclass(frozen=True)
class PositionRow:
    asset_name: str
    broker_ticker: str
    qty: Decimal
    avg_price: Decimal
    current_price: Decimal
    # broker-csv-import-totals: totals are broker-published values,
    # NEVER recomputed from ``qty * price``. An empty cell in the CSV
    # parses to ``None`` and contributes 0 to the dashboard aggregate
    # (see ``routes/pages.py``); a non-empty cell is taken verbatim
    # and inserted into ``Position.total_invested`` / ``total_current``.
    total_invested: Decimal | None
    total_current: Decimal | None
    line_no: int


def _read_csv(path: Path, expected_header: tuple[str, ...]) -> list[dict[str, str]]:
    """Read a CSV file and verify its header.

    Returns a list of row dicts keyed by header column. Aborts on:
    - missing file
    - wrong header (in order or missing columns)
    """
    if not path.exists():
        abort(f"missing CSV: {path}")
    with open(path, encoding="utf-8", newline="") as f:
        reader = csv.reader(f)
        try:
            header = tuple(next(reader))
        except StopIteration:
            abort(f"empty CSV (no header): {path}")
        if header != expected_header:
            abort(
                f"bad header in {path}\n"
                f"  expected: {','.join(expected_header)}\n"
                f"  got:      {','.join(header)}"
            )
        return [dict(zip(expected_header, row, strict=False)) for row in reader]


def _decimal(raw: str, *, field: str, path: Path, line_no: int) -> Decimal:
    try:
        return Decimal(raw.strip())
    except Exception as exc:  # noqa: BLE001 — argparse-style catch
        abort(f"{path}:{line_no} {field}={raw!r} not a decimal: {exc}")


def _optional_decimal(raw: str, *, field: str, path: Path, line_no: int) -> Decimal | None:
    """Parse a CSV cell that may be empty (``None``) or a decimal.

    Empty / whitespace-only cell → ``None``. Non-empty cell must
    parse as :class:`~decimal.Decimal`; otherwise abort with the
    line number. Used for ``total_invested`` / ``total_current``
    so the broker-published values flow through the round-trip
    without ever being recomputed from ``qty * price``.
    """
    s = raw.strip()
    if not s:
        return None
    try:
        value = Decimal(s)
    except Exception as exc:  # noqa: BLE001 — argparse-style catch
        abort(f"{path}:{line_no} {field}={raw!r} not a decimal: {exc}")
    if value < 0:
        abort(f"{path}:{line_no} {field}={value} < 0")
    return value


def _int(raw: str, *, field: str, path: Path, line_no: int) -> int:
    try:
        return int(Decimal(raw.strip()))
    except Exception as exc:  # noqa: BLE001
        abort(f"{path}:{line_no} {field}={raw!r} not an integer: {exc}")


def _bool(raw: str, *, field: str, path: Path, line_no: int) -> bool:
    """Parse a permissive boolean cell. Accepts ``true/false/1/0/yes/no``."""
    s = raw.strip().lower()
    if s in {"true", "1", "yes", "y", "t"}:
        return True
    if s in {"false", "0", "no", "n", "f", ""}:
        return False
    abort(f"{path}:{line_no} {field}={raw!r} not a boolean (use true/false/1/0)")


def abort(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    sys.exit(1)


def load_classes(profile: str) -> list[ClassRow]:
    path = scripts.seed_from_csv.SEED_DIR / f"{profile}_classes.csv"
    raw_rows = _read_csv(path, CLASS_HEADER)
    out: list[ClassRow] = []
    seen: dict[str, int] = {}
    for idx, raw in enumerate(raw_rows, start=2):  # header is line 1
        name = raw["name"].strip()
        if not name:
            abort(f"{path}:{idx} empty class name")
        if name in seen:
            abort(f"{path}:{idx} duplicate class name {name!r} (first seen at line {seen[name]})")
        seen[name] = idx
        target_pct = _decimal(raw["target_pct"], field="target_pct", path=path, line_no=idx)
        if not (Decimal("0") <= target_pct <= Decimal("100")):
            abort(f"{path}:{idx} target_pct={target_pct} out of [0, 100]")
        display_order = _int(raw["display_order"], field="display_order", path=path, line_no=idx)
        if display_order < 0:
            abort(f"{path}:{idx} display_order={display_order} < 0")
        quote_kind = raw["quote_kind"].strip()
        if quote_kind not in VALID_QUOTE_KINDS:
            abort(f"{path}:{idx} quote_kind={quote_kind!r} not one of {sorted(VALID_QUOTE_KINDS)}")
        out.append(
            ClassRow(
                name=name,
                target_pct=target_pct,
                display_order=display_order,
                quote_kind=quote_kind,
                line_no=idx,
            )
        )
    return out


def load_assets(profile: str) -> list[AssetRow]:
    path = scripts.seed_from_csv.SEED_DIR / f"{profile}_assets.csv"
    raw_rows = _read_csv(path, ASSET_HEADER)
    out: list[AssetRow] = []
    seen: dict[tuple[str, str], int] = {}
    for idx, raw in enumerate(raw_rows, start=2):
        class_name = raw["class_name"].strip()
        name = raw["name"].strip()
        if not class_name:
            abort(f"{path}:{idx} empty class_name")
        if not name:
            abort(f"{path}:{idx} empty asset name")
        key = (class_name, name)
        if key in seen:
            abort(
                f"{path}:{idx} duplicate ({class_name!r}, {name!r}) "
                f"(first seen at line {seen[key]})"
            )
        seen[key] = idx
        target_pct = _decimal(raw["target_pct"], field="target_pct", path=path, line_no=idx)
        if not (Decimal("0") <= target_pct <= Decimal("100")):
            abort(f"{path}:{idx} target_pct={target_pct} out of [0, 100]")
        display_order = _int(raw["display_order"], field="display_order", path=path, line_no=idx)
        if display_order < 0:
            abort(f"{path}:{idx} display_order={display_order} < 0")
        buy_enabled = _bool(raw["buy_enabled"], field="buy_enabled", path=path, line_no=idx)
        sell_enabled = _bool(raw["sell_enabled"], field="sell_enabled", path=path, line_no=idx)
        currency_code = raw["currency_code"].strip().upper()
        if currency_code not in VALID_CURRENCY_CODES:
            abort(
                f"{path}:{idx} currency_code={raw['currency_code']!r} "
                f"not one of {sorted(VALID_CURRENCY_CODES)}"
            )
        out.append(
            AssetRow(
                class_name=class_name,
                name=name,
                target_pct=target_pct,
                display_order=display_order,
                buy_enabled=buy_enabled,
                sell_enabled=sell_enabled,
                currency_code=currency_code,
                line_no=idx,
            )
        )
    return out


def load_positions(profile: str) -> list[PositionRow]:
    path = scripts.seed_from_csv.SEED_DIR / f"{profile}_positions.csv"
    raw_rows = _read_csv(path, POSITION_HEADER)
    out: list[PositionRow] = []
    for idx, raw in enumerate(raw_rows, start=2):
        asset_name = raw["asset_name"].strip()
        if not asset_name:
            abort(f"{path}:{idx} empty asset_name")
        broker_ticker = raw["broker_ticker"].strip()
        if not broker_ticker:
            abort(f"{path}:{idx} empty broker_ticker")
        qty = _decimal(raw["qty"], field="qty", path=path, line_no=idx)
        if qty < 0:
            abort(f"{path}:{idx} qty={qty} < 0")
        avg_price = _decimal(raw["avg_price"], field="avg_price", path=path, line_no=idx)
        if avg_price < 0:
            abort(f"{path}:{idx} avg_price={avg_price} < 0")
        current_price = _decimal(
            raw["current_price"], field="current_price", path=path, line_no=idx
        )
        if current_price < 0:
            abort(f"{path}:{idx} current_price={current_price} < 0")
        # broker-csv-import-totals: totals are broker-published
        # values. Empty cell → ``None`` (contributes 0 to the
        # dashboard aggregate). Non-empty cell is taken verbatim;
        # the parser never falls back to ``qty * price`` — that
        # path is the exact drift source this code eliminates.
        total_invested = _optional_decimal(
            raw["total_invested"], field="total_invested", path=path, line_no=idx
        )
        total_current = _optional_decimal(
            raw["total_current"], field="total_current", path=path, line_no=idx
        )
        out.append(
            PositionRow(
                asset_name=asset_name,
                broker_ticker=broker_ticker,
                qty=qty,
                avg_price=avg_price,
                current_price=current_price,
                total_invested=total_invested,
                total_current=total_current,
                line_no=idx,
            )
        )
    return out
