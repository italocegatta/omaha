// table-formatters: shared JS formatting functions for numeric values,
// sign logic, row/cell presentation. Pure functions, zero dependencies.
// Consumed by rebalance, portfolio, and import modal components.

// ── Numeric formatting ──────────────────────────────────────────

/**
 * Format value as currency with pt-BR locale.
 * Uses narrowSymbol display (R$ without space).
 * Returns '—' for null/undefined/NaN.
 */
export function formatMoney(value, currency) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return '—';
  var code = currency || 'BRL';
  return Number(value).toLocaleString('pt-BR', {
    style: 'currency',
    currency: code,
    currencyDisplay: 'narrowSymbol',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  });
}

/**
 * Format value as BRL currency with optional fractionDigits.
 * Uses default symbol display (R$ with non-breaking space).
 * Null/undefined/NaN treated as 0 in all paths.
 * Thin wrapper delegating to formatMoney when no fractionDigits.
 */
export function formatBRL(value, fractionDigits) {
  var n = (value === null || value === undefined || Number.isNaN(Number(value))) ? 0 : Number(value);
  if (fractionDigits === undefined || fractionDigits === null) {
    return formatMoney(n, 'BRL');
  }
  return n.toLocaleString('pt-BR', {
    style: 'currency',
    currency: 'BRL',
    minimumFractionDigits: fractionDigits,
    maximumFractionDigits: fractionDigits,
  });
}

/**
 * Format value as percentage with 2 decimal places (X.XX%).
 * Returns '—' for null/undefined/NaN.
 */
export function formatPct(value) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return '—';
  return Number(value).toFixed(2) + '%';
}

/**
 * Format value as percentage rounded to 0 decimals (X%).
 * Returns '—' for null/undefined/NaN.
 */
export function formatPctRounded(value) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return '—';
  return Math.round(Number(value)) + '%';
}

/**
 * Format quantity with pt-BR locale.
 * BTC assets get 3 fraction digits; all others get 1.
 * Returns '—' for null/undefined/NaN.
 */
export function formatQty(value, assetName) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return '—';
  var normalizedAssetName = String(assetName || '').trim().toUpperCase();
  var fractionDigits = normalizedAssetName === 'BTC' ? 3 : 1;
  return Number(value).toLocaleString('pt-BR', {
    minimumFractionDigits: fractionDigits,
    maximumFractionDigits: fractionDigits,
  });
}

/**
 * Format deviation in percentage points with explicit sign (+X% or -X%).
 * 0 decimals. Returns '0%' for zero.
 */
export function formatDeviationPp(value) {
  var n = Number(value) || 0;
  var sign = n >= 0 ? '+' : '';
  return sign + n.toFixed(0) + '%';
}

// ── Sign logic ──────────────────────────────────────────────────

/**
 * CSS class based on value sign.
 * 'metric-positive' > 0.0001, 'metric-negative' < -0.0001,
 * 'metric-neutral' otherwise (null/undefined/NaN/zero).
 */
export function signClass(value) {
  if (value === null || value === undefined || Math.abs(Number(value)) < 0.0001) return 'metric-neutral';
  return Number(value) > 0 ? 'metric-positive' : 'metric-negative';
}

/**
 * Material icon name based on value sign.
 * 'arrow_upward' > 0.0001, 'arrow_downward' < -0.0001,
 * 'remove' otherwise.
 */
export function signIcon(value) {
  if (value === null || value === undefined || Math.abs(Number(value)) < 0.0001) return 'remove';
  return Number(value) > 0 ? 'arrow_upward' : 'arrow_downward';
}

// ── Row and cell presentation ───────────────────────────────────

/**
 * Human-readable action label.
 * 'buy' → 'Comprar', 'sell' → 'Vender', default → 'Manter'.
 */
export function actionLabel(action) {
  if (action === 'buy') return 'Comprar';
  if (action === 'sell') return 'Vender';
  return 'Manter';
}

/**
 * Row CSS class based on row action.
 * hold → neutral, buy → buy, sell → sell.
 */
export function rowClass(row) {
  if (row.action === 'hold') return 'rebalance-asset-row--neutral';
  if (row.action === 'buy') return 'rebalance-asset-row--buy';
  return 'rebalance-asset-row--sell';
}

/**
 * Cell CSS class based on column type and row data.
 * Numeric columns get '--num', action columns get '--action',
 * deviation columns get sign-based class.
 */
export function cellClass(row, column) {
  var classes = 'rebalance-asset-cell';
  if (column.type !== 'enum') classes += ' rebalance-asset-cell--num';
  if (column.key === 'action' || column.cellFormat === 'operation') {
    classes += ' rebalance-asset-cell--action';
  }
  if (column.key === 'deviation') {
    classes += Number(row.deviation_value) >= 0 ? ' rebalance-deviation--pos' : ' rebalance-deviation--neg';
  }
  return classes;
}

/**
 * Format cell value based on column configuration.
 * Delegates to formatters object for operation/deviation/BRL formatting.
 */
export function formatCell(row, column, formatters) {
  var f = formatters || {};
  if (column.cellFormat === 'operation') {
    return f.formatOperation ? f.formatOperation(row) : '';
  }
  if (column.key === 'action') return actionLabel(row.action);
  if (column.key === 'deviation') {
    return f.formatDeviationCombined ? f.formatDeviationCombined(row) : '';
  }
  if (column.type === 'enum') return row[column.key];
  return (f.formatBRL || formatBRL)(row[column.key], column.fractionDigits);
}
