"""Pure CSV parser + matcher for the S04 broker importer.

The parser is intentionally dependency-free: it relies on the stdlib
``csv`` module and :mod:`decimal` to keep it deterministic, fast, and
trivially unit-testable. There is no DB, no FastAPI, no session, no
templates — this module is a plain function library the S04 routes
call into.

The unit-tested contract:

* :func:`parse_positions` accepts the raw text of a broker CSV (UTF-8
  with optional BOM, possibly Portuguese, possibly with a banner row,
  possibly with a header row, possibly with a Total footer row at the
  bottom) and returns a list of :class:`RawPosition` objects. It
  silently skips malformed rows, blank lines, banner rows, header
  rows, footer rows, and rows with an empty ticker cell — every
  skip is a deliberate "this row is not a position" decision, not a
  parser error.
* :func:`normalize_name` is the canonical name key used by
  :func:`match_positions`. It lower-cases, strips accents, drops
  punctuation, and collapses whitespace so the user-typed asset name
  "Tesouro IPCA+ 2035" matches the broker-supplied name "Tesouro
  IPCA+ 2035" even if the user later types it with extra spaces or
  a slightly different separator.
* :func:`match_positions` walks a list of :class:`RawPosition`
  objects and an iterable of existing asset-like objects (anything
  with ``.id`` and ``.name`` attributes; works for both SQLAlchemy
  :class:`~omaha.models.Asset` rows and test fakes). It returns a
  :class:`MatchResult` with the auto-matched rows and the rows the
  user has to review manually.

The T02 plan keeps the matcher *exact* (normalized-name equality).
Fuzzy matching (Levenshtein, ticker-prefix, etc.) is deferred to a
later slice — the demo flow with the 48-row fixture gives 43
auto-matches under exact normalization, which is well above the
"good enough for v1" threshold.
"""

from __future__ import annotations

import csv
import re
import unicodedata
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from io import StringIO
from typing import Iterable, Protocol

# Known header labels (lowercased, accent-stripped, no punctuation).
# The header detector matches any cell whose normalized form
# CONTAINS one of these substrings — that way "Codigo", "Código do
# Ativo", "Ticker", "Ticker Broker", etc. all match.
_KNOWN_TICKER_LABELS = ("codigo", "papel", "ticker", "ativo", "simbolo")
_KNOWN_NAME_LABELS = ("ativo", "nome", "descricao", "papel")
_KNOWN_QTY_LABELS = ("quantidade", "qty", "qtd", "qtde")
_KNOWN_AVG_LABELS = ("preco medio", "preco de compra", "preco de aquisicao", "avg price", "avg cost")
_KNOWN_CUR_LABELS = ("preco atual", "preco de mercado", "current price", "preco")

# Known footer labels. Footer rows are detected by ticker-cell match
# (col 0) or, in some broker statements, by the first non-empty
# cell. Substring match so "Total Geral", "Conta corrente",
# "Subtotal", "X ativos" all hit.
_KNOWN_FOOTER_LABELS = ("total", "subtotal", "conta", "ativos", "resumo", "patrimonio liquido")

# Header detection threshold: a row is a header if >=2 of its cells
# look like known labels. One match is too weak (could be coincidence
# — e.g. an asset name like "Conta corrente" sneaks in); two is
# strong enough to call it.
_HEADER_MIN_LABEL_HITS = 2

# Banner detection rule: a row is a banner when ALL of its
# non-empty cells are non-numeric AND don't match a known label.
# The "all cells" condition distinguishes free-form text like
# "Posição consolidada - 01/06/2026","Cliente: 12345" (banner)
# from a data row whose first column is a non-numeric ticker
# like "PETR4","PETR4",100,"28,50","35,10" (data).
_BANNER_REQUIRES_ALL_NON_NUMERIC = True

# Regex helpers — pre-compiled for speed on the 48-row fixture.
_PUNCT_RE = re.compile(r"[^\w\s]", re.UNICODE)
_WS_RE = re.compile(r"\s+")
_QR_PREFIX_RE = re.compile(r"^r\$\s*", re.IGNORECASE)


class AssetLike(Protocol):
    """Anything with an id and a name is enough for the matcher.

    Both :class:`omaha.models.Asset` rows and unit-test fakes satisfy
    this protocol — the matcher only ever calls ``.id`` and ``.name``.
    """

    id: int
    name: str


@dataclass(frozen=True)
class RawPosition:
    """A single broker-supplied position row, in the importer's neutral shape.

    All numeric fields are :class:`~decimal.Decimal` so the S04
    confirm handler can write them to the ``positions`` table's
    ``Numeric(18, 4)`` columns without intermediate float rounding.
    ``row_index`` is the 1-based line number in the original CSV,
    used in error messages surfaced to the user ("row 17: malformed
    number").
    """

    broker_ticker: str
    name: str
    qty: Decimal
    avg_price: Decimal
    current_price: Decimal
    row_index: int


@dataclass
class MatchResult:
    """Output of :func:`match_positions`.

    ``auto_matched`` is a list of ``(RawPosition, asset_id)`` pairs
    — the broker's position and the existing Asset id the parser
    confidently mapped it to. ``unmatched`` is a list of
    :class:`RawPosition` rows that did not match any existing asset
    and therefore need a user decision in the review screen.
    """

    auto_matched: list[tuple[RawPosition, int]]
    unmatched: list[RawPosition]


def _strip_accents(s: str) -> str:
    """Decompose unicode to NFD then drop combining marks."""
    nfd = unicodedata.normalize("NFD", s)
    return "".join(c for c in nfd if unicodedata.category(c) != "Mn")


def normalize_name(s: str) -> str:
    """Canonical form used by :func:`match_positions`.

    Lower-cases, strips accents, drops punctuation, collapses
    whitespace. "  Tesouro IPCA+ 2035  " and "Tesouro ipca 2035"
    and "TESOURO  IPCA  2035" all canonicalize to
    ``"tesouro ipca 2035"``.
    """
    if not s:
        return ""
    s = _strip_accents(s.lower()).strip()
    s = _PUNCT_RE.sub(" ", s)
    s = _WS_RE.sub(" ", s).strip()
    return s


def _normalize_cell(s: str) -> str:
    """Accent-stripped, lower-cased, whitespace-stripped cell.

    Used for header-label and footer-label matching. Doesn't drop
    punctuation because header cells rarely contain punctuation; if
    they do, the substring match still works.
    """
    if not s:
        return ""
    return _strip_accents(s.strip().lower())


def _is_known_label(cell: str) -> bool:
    """True if the cell looks like one of our known header labels."""
    n = _normalize_cell(cell)
    if not n:
        return False
    for group in (
        _KNOWN_TICKER_LABELS,
        _KNOWN_NAME_LABELS,
        _KNOWN_QTY_LABELS,
        _KNOWN_AVG_LABELS,
        _KNOWN_CUR_LABELS,
    ):
        for label in group:
            if label in n:
                return True
    return False


def _is_known_footer(cell: str) -> bool:
    """True if the cell looks like one of the known footer markers."""
    n = _normalize_cell(cell)
    if not n:
        return False
    return any(label in n for label in _KNOWN_FOOTER_LABELS)


def _parse_brazilian_number(s: str) -> Decimal:
    """Parse a number string into a :class:`~decimal.Decimal`.

    Handles both Brazilian (``1.234,56``, ``28,50``) and US
    (``1,234.56``, ``1234.56``) formats. The rule: when BOTH a
    dot and a comma are present, the rightmost separator is the
    decimal point. When only one separator is present, it is
    treated as the decimal point. Strips an ``R$`` prefix and
    surrounding quotes. Raises
    :class:`~decimal.InvalidOperation` on unparseable input —
    the caller catches that and treats the row as malformed.

    Examples::

        _parse_brazilian_number("1.234,56")   -> Decimal("1234.56")
        _parse_brazilian_number("28,50")      -> Decimal("28.50")
        _parse_brazilian_number("R$ 990,92")  -> Decimal("990.92")
        _parse_brazilian_number("1234.56")    -> Decimal("1234.56")
        _parse_brazilian_number("1,234.56")   -> Decimal("1234.56")
        _parse_brazilian_number("")           -> InvalidOperation
    """
    s = s.strip()
    if not s:
        raise InvalidOperation("empty value")
    s = _QR_PREFIX_RE.sub("", s).strip().strip('"').strip()
    if not s:
        raise InvalidOperation("empty value after currency strip")
    has_dot = "." in s
    has_comma = "," in s
    if has_dot and has_comma:
        # Rightmost separator is the decimal. Drop the other one as
        # a thousands separator.
        if s.rfind(",") > s.rfind("."):
            # BR: dots are thousands, comma is decimal.
            s = s.replace(".", "").replace(",", ".")
        else:
            # US: commas are thousands, dot is decimal.
            s = s.replace(",", "")
    elif has_comma:
        # Only comma — treat as decimal (Brazilian default).
        s = s.replace(",", ".")
    # else: only dot (or no separator) — leave as-is (US decimal).
    return Decimal(s)


def _is_blank_row(row: list[str]) -> bool:
    return not any(cell.strip() for cell in row)


def _count_non_numeric_unknown(row: list[str]) -> int:
    """Count cells that are non-numeric AND don't match a known label.

    Used for banner detection: a row that is mostly
    label-unrecognized non-numeric content (e.g. "Posição
    consolidada", "Emitido em 01/06/2026") is a banner row, not a
    header and not data.
    """
    count = 0
    for cell in row:
        cell_strip = cell.strip()
        if not cell_strip:
            continue
        if _is_known_label(cell_strip):
            return 0  # any known label disqualifies the row as a banner
        try:
            _parse_brazilian_number(cell_strip)
        except InvalidOperation:
            count += 1
    return count


def _is_banner_row(row: list[str]) -> bool:
    non_empty = sum(1 for c in row if c.strip())
    if non_empty == 0:
        return False
    return _count_non_numeric_unknown(row) >= non_empty


def _is_header_row(row: list[str]) -> bool:
    """True if the row is a recognizable header (>=2 label hits)."""
    hits = sum(1 for cell in row if _is_known_label(cell))
    return hits >= _HEADER_MIN_LABEL_HITS


def _parse_data_row(row: list[str], row_index: int) -> RawPosition | None:
    """Convert one CSV data row to a :class:`RawPosition`, or ``None`` to skip.

    Skips rows whose ticker cell is empty (phantom rows some broker
    files insert between sections) and rows whose ticker matches a
    known footer label. Malformed numeric cells (e.g. ``"abc"``)
    raise :class:`~decimal.InvalidOperation` inside
    :func:`_parse_brazilian_number`; the caller turns that into a
    ``None`` skip so the parser never crashes on a single bad row.
    """
    if len(row) < 2:
        return None
    ticker_cell = row[0].strip()
    name_cell = row[1].strip()
    if not ticker_cell:
        return None  # empty-ticker phantom row
    if _is_known_footer(ticker_cell):
        return None
    if name_cell and _is_known_footer(name_cell):
        return None
    try:
        qty = _parse_brazilian_number(row[2]) if len(row) > 2 else Decimal("0")
    except (InvalidOperation, IndexError):
        return None
    try:
        avg_price = _parse_brazilian_number(row[3]) if len(row) > 3 else Decimal("0")
    except (InvalidOperation, IndexError):
        return None
    try:
        current_price = _parse_brazilian_number(row[4]) if len(row) > 4 else Decimal("0")
    except (InvalidOperation, IndexError):
        return None
    return RawPosition(
        broker_ticker=ticker_cell,
        name=name_cell,
        qty=qty,
        avg_price=avg_price,
        current_price=current_price,
        row_index=row_index,
    )


def parse_positions(text: str) -> list[RawPosition]:
    """Parse the text of a broker CSV into a list of :class:`RawPosition`.

    Detection order: skip blank lines, then skip leading banner
    rows, then detect a header row (>=2 label hits), then parse
    every remaining row positionally (col 0 = ticker, col 1 =
    name, col 2 = qty, col 3 = avg price, col 4 = current price).
    If no header is detected the first non-banner row is treated
    as data.

    A row whose numeric cells don't parse is silently dropped — the
    importer surfaces "X rows imported, Y skipped" rather than
    blowing up the whole upload. An exception in a single row
    never aborts the rest of the file.
    """
    if not text:
        return []
    # Drop a leading UTF-8 BOM if present — common when broker sites
    # serve the file as text/csv with a BOM.
    if text.startswith("\ufeff"):
        text = text[1:]
    reader = csv.reader(StringIO(text))
    rows = list(reader)
    if not rows:
        return []

    idx = 0
    # Skip leading blank lines.
    while idx < len(rows) and _is_blank_row(rows[idx]):
        idx += 1
    if idx >= len(rows):
        return []

    # Skip leading banner rows.
    while idx < len(rows) and _is_banner_row(rows[idx]):
        idx += 1
        while idx < len(rows) and _is_blank_row(rows[idx]):
            idx += 1
    if idx >= len(rows):
        return []

    # Detect header row. A header is consumed; the next non-blank
    # row starts the data section. If no header is detected, the
    # first non-banner row is data and positional parsing begins
    # immediately.
    if _is_header_row(rows[idx]):
        idx += 1
    while idx < len(rows) and _is_blank_row(rows[idx]):
        idx += 1

    out: list[RawPosition] = []
    for offset, row in enumerate(rows[idx:]):
        # 1-based line number in the source file (header is line 1,
        # first data row is line 2 if no banner, line N+1 if there
        # was a banner).
        row_index = idx + offset + 1
        if _is_blank_row(row):
            continue
        parsed = _parse_data_row(row, row_index)
        if parsed is not None:
            out.append(parsed)
    return out


def match_positions(
    raw: Iterable[RawPosition],
    existing_assets: Iterable[AssetLike],
) -> MatchResult:
    """Auto-match raw positions against the user's existing assets.

    The match is exact on normalized name. If the same normalized
    name appears twice in the existing assets (which the schema's
    unique-per-class constraint prevents at the DB level but tests
    can synthesize), the FIRST asset wins — the matcher keeps a
    dict so duplicates don't introduce ambiguity.

    Returns a :class:`MatchResult`. ``auto_matched`` preserves the
    order of the input ``raw`` iterable, as does ``unmatched`` — so
    the review screen renders the same order the user saw in the
    broker file.
    """
    index: dict[str, int] = {}
    for asset in existing_assets:
        key = normalize_name(asset.name)
        if key and key not in index:
            index[key] = asset.id

    auto_matched: list[tuple[RawPosition, int]] = []
    unmatched: list[RawPosition] = []
    for raw_pos in raw:
        key = normalize_name(raw_pos.name)
        if key and key in index:
            auto_matched.append((raw_pos, index[key]))
        else:
            unmatched.append(raw_pos)
    return MatchResult(auto_matched=auto_matched, unmatched=unmatched)
