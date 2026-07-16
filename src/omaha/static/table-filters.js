// table-filters: shared JS filter logic for table column filters.
// Pure functions, zero dependencies. Consumed by rebalance, portfolio,
// PoC, and import modal components. Follows table-formatters.js pattern.

// ── Range computation ───────────────────────────────────────────

/**
 * Compute {min, max} bounds for a range key across rows.
 * @param {Array} rows - data rows
 * @param {string} key - column key (or range key)
 * @param {Function} [fieldFn] - maps key → data field name (identity if omitted)
 */
export function rangeBounds(rows, key, fieldFn) {
  var field = fieldFn ? fieldFn(key) : key;
  var values = rows.map(function (r) { return Number(r[field]) || 0; });
  if (values.length === 0) return { min: 0, max: 0 };
  return { min: Math.min.apply(null, values), max: Math.max.apply(null, values) };
}

/**
 * Compute step size for a range slider.
 * deviation_pct gets 0.01; others get 10^(floor(log10(span))-2), min 0.01.
 * @param {Array} rows - data rows
 * @param {string} key - range key
 * @param {Function} [fieldFn] - maps key → data field name
 */
export function rangeStep(rows, key, fieldFn) {
  if (key === 'deviation_pct') return 0.01;
  var bounds = rangeBounds(rows, key, fieldFn);
  var span = bounds.max - bounds.min;
  return span === 0 ? 0.01 : Math.max(Math.pow(10, Math.floor(Math.log10(span)) - 2), 0.01);
}

/**
 * Initialize null/empty filter bounds to data bounds.
 * Mutates filter in place.
 * @param {Object} filter - {min, max} object
 * @param {Array} rows - data rows
 * @param {string} key - range key
 * @param {Function} [fieldFn] - maps key → data field name
 */
export function ensureRangeBounds(filter, rows, key, fieldFn) {
  var bounds = rangeBounds(rows, key, fieldFn);
  if (filter.min === null || filter.min === '') filter.min = bounds.min;
  if (filter.max === null || filter.max === '') filter.max = bounds.max;
}

/**
 * Clamp filter.min: not > max, not < data min.
 * Mutates filter in place.
 * @param {Object} filter - {min, max} object
 * @param {Array} rows - data rows
 * @param {string} key - range key
 * @param {Function} [fieldFn] - maps key → data field name
 */
export function clampRangeMin(filter, rows, key, fieldFn) {
  ensureRangeBounds(filter, rows, key, fieldFn);
  var bounds = rangeBounds(rows, key, fieldFn);
  if (Number(filter.min) > Number(filter.max)) filter.min = filter.max;
  if (Number(filter.min) < bounds.min) filter.min = bounds.min;
}

/**
 * Clamp filter.max: not < min, not > data max.
 * Mutates filter in place.
 * @param {Object} filter - {min, max} object
 * @param {Array} rows - data rows
 * @param {string} key - range key
 * @param {Function} [fieldFn] - maps key → data field name
 */
export function clampRangeMax(filter, rows, key, fieldFn) {
  ensureRangeBounds(filter, rows, key, fieldFn);
  var bounds = rangeBounds(rows, key, fieldFn);
  if (Number(filter.max) < Number(filter.min)) filter.max = filter.min;
  if (Number(filter.max) > bounds.max) filter.max = bounds.max;
}

/**
 * Compute CSS left/right percentages for range fill bar.
 * @param {Object} filter - {min, max} object
 * @param {Array} rows - data rows
 * @param {string} key - range key
 * @param {Function} [fieldFn] - maps key → data field name
 * @returns {string} CSS style string
 */
export function rangeFillStyle(filter, rows, key, fieldFn) {
  var bounds = rangeBounds(rows, key, fieldFn);
  var span = bounds.max - bounds.min;
  if (span === 0) return 'left: 0%; right: 0%;';
  var min = filter.min === null || filter.min === '' ? bounds.min : Number(filter.min);
  var max = filter.max === null || filter.max === '' ? bounds.max : Number(filter.max);
  return 'left: ' + ((min - bounds.min) / span) * 100 + '%; right: ' +
    ((bounds.max - max) / span) * 100 + '%;';
}

/**
 * Format a range slider value for display.
 * @param {*} value - raw value
 * @param {string} [format] - 'deviationPp' for deviation format, falsy for BRL
 * @param {Object} [formatters] - {formatBRL, formatDeviationPp} from table-formatters
 * @returns {string} formatted string or '-'
 */
export function formatRangeValue(value, format, formatters) {
  if (value === null || value === '' || value === undefined) return '-';
  if (format === 'deviationPp') {
    if (formatters && formatters.formatDeviationPp) return formatters.formatDeviationPp(value);
    var n = Number(value) || 0;
    return (n >= 0 ? '+' : '') + n.toFixed(0) + '%';
  }
  if (formatters && formatters.formatBRL) return formatters.formatBRL(value);
  return String(value);
}

// ── Filter state ────────────────────────────────────────────────

/**
 * Check if a column has an active filter.
 * @param {Object} column - column definition
 * @param {Object} headerFilters - enum filter state {key: [values]}
 * @param {Object} headerRangeFilters - range filter state {key: {min, max}}
 * @param {Array} rows - data rows
 * @param {Function} [fieldFn] - maps key → data field name
 * @returns {boolean}
 */
export function filterActive(column, headerFilters, headerRangeFilters, rows, fieldFn) {
  var filterKey = column.filterKey || column.key;
  if (column.type === 'enum') return (headerFilters[filterKey] || []).length > 0;
  var keys = rangeKeysFor(column);
  return keys.some(function (key) {
    var bounds = rangeBounds(rows, key, fieldFn);
    var filter = headerRangeFilters[key];
    if (!filter) return false;
    return filter.min !== null && filter.min !== '' && filter.max !== null && filter.max !== '' &&
      (Number(filter.min) > bounds.min || Number(filter.max) < bounds.max);
  });
}

/**
 * Toggle a filter panel open/closed, closing others.
 * Mutates openFilter in place. Calls ensureRangeBounds if opening a range panel.
 * @param {string} key - column key
 * @param {Object} openFilter - panel open state {key: boolean}
 * @param {Array} columns - column definitions
 * @param {Object} headerRangeFilters - range filter state
 * @param {Array} rows - data rows
 * @param {Function} [fieldFn] - maps key → data field name
 */
export function toggleFilterPanel(key, openFilter, columns, headerRangeFilters, rows, fieldFn) {
  var column = columns.find(function (c) { return c.key === key; });
  Object.keys(openFilter).forEach(function (k) {
    if (k !== key) openFilter[k] = false;
  });
  if (!openFilter[key] && column && column.type !== 'enum') {
    rangeKeysFor(column).forEach(function (rk) {
      var filter = headerRangeFilters[rk];
      if (filter) ensureRangeBounds(filter, rows, rk, fieldFn);
    });
  }
  openFilter[key] = !openFilter[key];
}

/**
 * Clear a column's filter (enum → empty array, range → data bounds).
 * Mutates headerFilters/headerRangeFilters in place.
 * @param {string} key - column key
 * @param {Object} headerFilters - enum filter state
 * @param {Object} headerRangeFilters - range filter state
 * @param {Array} columns - column definitions
 * @param {Array} rows - data rows
 * @param {Function} [fieldFn] - maps key → data field name
 */
export function clearFilter(key, headerFilters, headerRangeFilters, columns, rows, fieldFn) {
  var column = columns.find(function (c) { return c.key === key; });
  if (!column) return;
  var filterKey = column.filterKey || column.key;
  if (column.type === 'enum') {
    headerFilters[filterKey] = [];
  } else {
    rangeKeysFor(column).forEach(function (rangeKey) {
      var bounds = rangeBounds(rows, rangeKey, fieldFn);
      headerRangeFilters[rangeKey].min = bounds.min;
      headerRangeFilters[rangeKey].max = bounds.max;
    });
  }
}

/**
 * Get the range keys for a column (composite → mapped keys, range → [key], enum → []).
 * @param {Object} column - column definition
 * @returns {string[]}
 */
export function rangeKeysFor(column) {
  if (column.type === 'composite') return column.ranges.map(function (r) { return r.key; });
  if (column.type === 'range') return [column.key];
  return [];
}

/**
 * Compute filtered rows applying all active filters.
 * @param {Array} rows - display rows
 * @param {Array} columns - column definitions
 * @param {Object} headerFilters - enum filter state
 * @param {Object} headerRangeFilters - range filter state
 * @param {Object} [options] - {fieldFn} maps key → data field name
 * @returns {Array} filtered rows
 */
export function computeFilteredRows(rows, columns, headerFilters, headerRangeFilters, options) {
  var fieldFn = options && options.fieldFn ? options.fieldFn : null;
  var result = rows;
  columns.forEach(function (column) {
    var filterKey = column.filterKey || column.key;
    if (column.type === 'enum') {
      var selected = headerFilters[filterKey] || [];
      if (selected.length > 0) {
        var field = fieldFn ? fieldFn(filterKey) : filterKey;
        result = result.filter(function (r) { return selected.includes(r[field]); });
      }
      return;
    }
    var keys = rangeKeysFor(column);
    keys.forEach(function (key) {
      var bounds = rangeBounds(result.length > 0 ? result : rows, key, fieldFn);
      var filter = headerRangeFilters[key];
      if (!filter) return;
      var min = filter.min === null || filter.min === '' ? bounds.min : Number(filter.min);
      var max = filter.max === null || filter.max === '' ? bounds.max : Number(filter.max);
      if (column.key === 'operation') {
        var action = key === 'buy_amount' ? 'buy' : 'sell';
        if (min > bounds.min) {
          result = result.filter(function (r) {
            return r.action !== action || (Number(r[key]) || 0) >= min;
          });
        }
        if (max < bounds.max) {
          result = result.filter(function (r) {
            return r.action !== action || (Number(r[key]) || 0) <= max;
          });
        }
      } else {
        if (min > bounds.min) {
          result = result.filter(function (r) { return (Number(r[key]) || 0) >= min; });
        }
        if (max < bounds.max) {
          result = result.filter(function (r) { return (Number(r[key]) || 0) <= max; });
        }
      }
    });
  });
  return result;
}
