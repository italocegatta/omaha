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
from collections.abc import Iterable
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from io import StringIO
from typing import Protocol

# Known header labels (lowercased, accent-stripped, no punctuation).
# The header detector matches any cell whose normalized form
# CONTAINS one of these substrings — that way "Codigo", "Código do
# Ativo", "Ticker", "Ticker Broker", etc. all match.
_KNOWN_TICKER_LABELS = ("codigo", "papel", "ticker", "ativo", "simbolo")
_KNOWN_NAME_LABELS = ("ativo", "nome", "descricao", "papel")
_KNOWN_QTY_LABELS = ("quantidade", "qty", "qtd", "qtde")
_KNOWN_AVG_LABELS = (
    "preco medio",
    "preco de compra",
    "preco de aquisicao",
    "avg price",
    "avg cost",
)
_KNOWN_CUR_LABELS = ("preco atual", "preco de mercado", "current price", "preco")

# Known footer labels. Footer rows are detected by ticker-cell match
# (col 0) or, in some broker statements, by the first non-empty
# cell. Substring match so "Total Geral", "Conta corrente",
# "Subtotal", "X ativos" all hit.
_KNOWN_FOOTER_LABELS = ("total", "subtotal", "conta", "ativos", "resumo", "patrimonio liquido")

# Category column labels — when the broker statement carries a
# "Minha Categoria" / "Categoria" / "Category" cell, we read it
# into ``RawPosition.suggested_category`` so the review screen can
# pre-select a class for the user.
_KNOWN_CATEGORY_LABELS = ("minha categoria", "categoria", "category", "asset class", "classe")

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
    number"). ``suggested_category`` is the value of the file's
    "Minha Categoria" column (if any) — the S04 review screen uses
    it via :func:`suggest_class_id` to pre-select a class for the
    user, who can still override via the dropdown.
    """

    broker_ticker: str
    name: str
    qty: Decimal
    avg_price: Decimal
    current_price: Decimal
    row_index: int
    suggested_category: str | None = None


@dataclass(frozen=True)
class ColumnMap:
    """Result of :func:`_detect_columns` — column indices for each field.

    ``name`` is ``None`` when the header carries only a single
    "Ativo"-style column (e.g. the broker file the user uploads
    has "Ativo, Qtd, Preço médio, ..." with no separate name
    column). The parser then uses the ticker value as the name —
    which is correct, because the file's first column IS the
    asset's identifier.
    """

    ticker: int
    name: int | None
    qty: int
    avg_price: int
    current_price: int
    category: int | None


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


def _is_known_category(cell: str) -> bool:
    """True if the cell looks like a category-column label."""
    n = _normalize_cell(cell)
    if not n:
        return False
    return any(label in n for label in _KNOWN_CATEGORY_LABELS)


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


def _parse_data_row(
    row: list[str],
    row_index: int,
    col_map: ColumnMap | None = None,
) -> RawPosition | None:
    """Convert one CSV data row to a :class:`RawPosition`, or ``None`` to skip.

    ``col_map`` is the result of :func:`_detect_columns` when a
    header was present; ``None`` falls back to the original
    positional scheme (col 0 = ticker, col 1 = name, col 2 = qty,
    col 3 = avg, col 4 = current). The label-driven path is
    necessary because the user's real broker file is shaped
    "Ativo, Qtd, Preço médio, ..., Minha Categoria" — no separate
    "Codigo" + "Ativo" + "Quantidade" trio — and a positional
    parser would mistake the qty for the asset name.

    Skips rows whose ticker cell is empty (phantom rows some broker
    files insert between sections) and rows whose ticker matches a
    known footer label. Malformed numeric cells (e.g. ``"abc"``)
    raise :class:`~decimal.InvalidOperation` inside
    :func:`_parse_brazilian_number`; the caller turns that into a
    ``None`` skip so the parser never crashes on a single bad row.
    """
    if col_map is not None:
        if len(row) <= col_map.ticker:
            return None
        ticker_cell = row[col_map.ticker].strip()
        # When the header has no separate name column, use the ticker
        # as the name — the file's first column IS the asset's
        # identifier, and ``match_positions`` normalizes the name for
        # comparison, so the two are interchangeable here.
        if col_map.name is not None and col_map.name < len(row):
            name_cell = row[col_map.name].strip() or ticker_cell
        else:
            name_cell = ticker_cell
        if not ticker_cell:
            return None
        if _is_known_footer(ticker_cell):
            return None
        if name_cell and _is_known_footer(name_cell):
            return None
        try:
            qty = (
                _parse_brazilian_number(row[col_map.qty])
                if col_map.qty < len(row)
                else Decimal("0")
            )
        except (InvalidOperation, IndexError):
            return None
        try:
            avg_price = (
                _parse_brazilian_number(row[col_map.avg_price])
                if col_map.avg_price < len(row)
                else Decimal("0")
            )
        except (InvalidOperation, IndexError):
            return None
        try:
            current_price = (
                _parse_brazilian_number(row[col_map.current_price])
                if col_map.current_price < len(row)
                else Decimal("0")
            )
        except (InvalidOperation, IndexError):
            return None
        category_cell = None
        if col_map.category is not None and col_map.category < len(row):
            category_cell = row[col_map.category].strip() or None
        return RawPosition(
            broker_ticker=ticker_cell,
            name=name_cell,
            qty=qty,
            avg_price=avg_price,
            current_price=current_price,
            row_index=row_index,
            suggested_category=category_cell,
        )

    # Positional fallback — no header detected. Keep this path so
    # CSVs that omit the header (e.g. ad-hoc position lists) still
    # parse.
    if len(row) < 2:
        return None
    ticker_cell = row[0].strip()
    name_cell = row[1].strip()
    if not ticker_cell:
        return None
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


def _detect_columns(header_row: list[str]) -> ColumnMap | None:
    """Inspect a header row and return a :class:`ColumnMap`.

    Returns ``None`` when the header is not informative enough to
    drive column-aligned parsing (e.g. a header with only a
    category column and no qty column). The caller falls back to
    positional parsing in that case.

    Each header cell is assigned to the FIRST label group that
    (a) it matches and (b) has not yet been assigned. Group
    priority is the order below — ticker is the most specific
    (matches "Codigo", "Ticker", "Simbolo") and is consumed
    before name (matches "Ativo", "Nome"), so a file with
    "Codigo, Ativo, Quantidade, ..." correctly resolves
    ticker=0, name=1.
    """
    ticker_col: int | None = None
    name_col: int | None = None
    qty_col: int | None = None
    avg_col: int | None = None
    cur_col: int | None = None
    cat_col: int | None = None

    for i, cell in enumerate(header_row):
        if _is_known_label(cell):
            if ticker_col is None and any(
                label in _normalize_cell(cell) for label in _KNOWN_TICKER_LABELS
            ):
                ticker_col = i
                continue
            if name_col is None and any(
                label in _normalize_cell(cell) for label in _KNOWN_NAME_LABELS
            ):
                name_col = i
                continue
            if qty_col is None and any(
                label in _normalize_cell(cell) for label in _KNOWN_QTY_LABELS
            ):
                qty_col = i
                continue
            if avg_col is None and any(
                label in _normalize_cell(cell) for label in _KNOWN_AVG_LABELS
            ):
                avg_col = i
                continue
            if cur_col is None and any(
                label in _normalize_cell(cell) for label in _KNOWN_CUR_LABELS
            ):
                cur_col = i
                continue
        if cat_col is None and _is_known_category(cell):
            cat_col = i

    if ticker_col is None or qty_col is None:
        return None  # not enough information
    return ColumnMap(
        ticker=ticker_col,
        name=name_col,
        qty=qty_col,
        avg_price=avg_col if avg_col is not None else qty_col + 1,
        current_price=cur_col if cur_col is not None else (avg_col or qty_col) + 1,
        category=cat_col,
    )


def parse_positions(text: str) -> list[RawPosition]:
    """Parse the text of a broker CSV into a list of :class:`RawPosition`.

    Detection order: skip blank lines, then skip leading banner
    rows, then detect a header row (>=2 label hits) and use it to
    align columns by label, then parse every remaining row
    against the resulting :class:`ColumnMap`. If no header is
    detected the first non-banner row is treated as data using
    the original positional scheme (col 0 = ticker, col 1 = name,
    col 2 = qty, col 3 = avg, col 4 = current).

    The label-driven path matters because the user's real broker
    file is shaped "Ativo, Qtd, Preço médio, ..., Minha Categoria"
    — no separate "Codigo" + "Ativo" + "Quantidade" trio. A
    positional parser would mistake the qty (col 1) for the
    asset name. With label detection, the qty column is found by
    its "Qtd" label and the ticker column by its "Ativo" label,
    and ``ColumnMap.name is None`` tells the row parser to use
    the ticker value as the name.

    A row whose numeric cells don't parse is silently dropped —
    the importer surfaces "X rows imported, Y skipped" rather
    than blowing up the whole upload. An exception in a single
    row never aborts the rest of the file.
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
    # row starts the data section. The column map tells the row
    # parser which cell holds which field, which is the whole
    # point of this refactor (positional parsing breaks on files
    # where the qty column is the SECOND column, not the third).
    col_map: ColumnMap | None = None
    if _is_header_row(rows[idx]):
        col_map = _detect_columns(rows[idx])
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
        parsed = _parse_data_row(row, row_index, col_map)
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


# Mapping from a broker-file category string (normalized) to a
# substring that must appear (also normalized) in the class name.
# Order matters: the FIRST matching key wins. This is a curated
# list, not a generic translator — the user's broker speaks a
# fixed set of categories ("RF Pós", "Ações", "FII", "Cripto",
# "Internacional", "(Não configurado)") and the user's class
# names follow the same vocabulary ("Renda Fixa", "Acoes",
# "FIIs", "Cripto", "Internacional"). Keys are checked in
# declaration order, so longer / more specific forms (e.g.
# "acoes") are placed before their prefixes ("acao") — otherwise
# the prefix would match first and the class-substring lookup
# would target the wrong stem.
_CATEGORY_KEYWORD_MAP: tuple[tuple[str, str], ...] = (
    ("renda fixa", "fixa"),
    ("renda", "fixa"),
    ("rf", "fixa"),
    ("acoes", "acoes"),
    ("acao", "acoes"),
    ("dividend", "fii"),
    ("fiagro", "fii"),
    ("fii", "fii"),
    ("criptomoeda", "cripto"),
    ("cripto", "cripto"),
    ("internacional", "internacional"),
    ("exterior", "internacional"),
    ("global", "internacional"),
)


class _ClassLike(Protocol):
    """Anything with an id and a name is enough for the suggester."""

    id: int
    name: str


def suggest_class_id(
    suggested_category: str | None,
    classes: Iterable[_ClassLike],
) -> int | None:
    """Pick a class that best matches the file's "Minha Categoria" hint.

    The user uploads a broker file whose "Minha Categoria" column
    carries a label like "RF Pós", "Ações", "FII", "Cripto". This
    function maps that label to one of the user's configured
    classes (e.g. "RF Pós" → "Renda Fixa") and returns the
    matching class id, or ``None`` when no class is a confident
    match. The S04 review screen uses the returned id to
    pre-select the dropdown — the user can always override.

    The match is substring-based on the normalized category
    string and the normalized class name, with a curated
    :data:`_CATEGORY_KEYWORD_MAP` translating the broker's
    vocabulary to the user's class vocabulary. For example, the
    category "BR Dividendos" maps to the keyword "fii" (a
    Fiagro) which is then located in the class name "FIIs 10%".
    """
    if not suggested_category:
        return None
    cat_norm = normalize_name(suggested_category)
    if not cat_norm:
        return None
    target_keyword: str | None = None
    for keyword, class_substring in _CATEGORY_KEYWORD_MAP:
        if keyword in cat_norm:
            target_keyword = class_substring
            break
    if not target_keyword:
        return None
    for cls in classes:
        cls_norm = normalize_name(cls.name)
        if target_keyword in cls_norm:
            return cls.id
    return None
