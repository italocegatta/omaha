# 2.3 Dashboard inline editor's PATCH URL

## Resolves: design §OQ2 (does the dashboard depend on PATCH /api/assets/{id}?)

## Inspection

### dashboard.html line 828 (commitEdit)
```js
fetch('/api/assets/' + id, {
  method: 'PATCH',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({target_pct: String(pct)}),
})
```
→ `PATCH /api/assets/{id}` with `{"target_pct": "<str>"}`.

### dashboard.html line 986 (confirmDeleteAsset)
```js
fetch('/api/assets/' + id, { method: 'DELETE' })
```
→ `DELETE /api/assets/{id}`.

### dashboard.html line 922 (saveNewAsset)
```js
fetch('/api/assets', { method: 'POST', ... })
```
→ `POST /api/assets`.

## Match against route contract

| Caller | Route | Body | Expected response |
|---|---|---|---|
| `commitEdit` (line 828) | `PATCH /api/assets/{id}` | `{"target_pct": "40"}` | `200 {"id", "target_pct"}` or `422 {"detail": "..."}` |
| `confirmDeleteAsset` (line 986) | `DELETE /api/assets/{id}` | — | `204` |
| `saveNewAsset` (line 922) | `POST /api/assets` | `{"name", "asset_class_id", "target_pct"}` | `201 {"id", "name", "target_pct"}` |

The route handlers at `src/omaha/routes/assets.py` match these
contracts exactly (lines 226, 343, 421).

## Decision input
PATCH /api/assets/{id} is **load-bearing** — the dashboard's
inline edit feature depends on it. The route must continue to
return the documented contract.

This pins the direction for §3.1/§3.2: the **route is correct**;
the divergence is in the test fixture username (per 1.1/1.2
notes).
