# 1.1 PATCH /api/assets/{asset_id} — happy path 404

## Reproduction
```bash
uv run pytest tests/test_t99_assets_patch.py::test_patch_asset_updates_target_pct --tb=long -p no:cacheprovider
```
Captured traceback:
```
>       assert response.status_code == 200
E       assert 404 == 200
```

Response body (debug, captured via a probe at `tests/test_debug_patch.py`):
```
status: 404
body:   {"detail":"Not Found"}
```

## Diagnosis
Route registration (`PATCH /api/assets/{asset_id}`) is wired at
`src/omaha/routes/assets.py:343`. The handler runs and reaches
`require_active_profile`, which raises 404 with FastAPI's default
body (`{"detail":"Not Found"}` — no message) when no profile is
active.

The test helper `_login_and_select` uses `username="family"`:
```python
client.post("/login", data={"username": "family", "password": "test-password"}, ...)
```
The seed (`src/omaha/seed.py:26-29`) only creates `"Italo"` and
`"Ana"`. Login fails silently (the `/login` route returns 200 with
a form error and does not set a cookie). The subsequent
`POST /profiles/1/select` is unauthenticated and also bounces.
When `PATCH /api/assets/{asset_id}` runs, `require_active_profile`
finds no profile in the session → 404.

This is **not** a route-handler bug: the route is correctly
registered, the ownership check is correct, and the response
contract (404 with empty detail) is the documented behaviour of
`require_active_profile` (`src/omaha/auth.py:138-141`). The bug is
in the test fixture username.

`test_t02_assets_routes.py` uses the same login pattern with the
correct username (`"Italo"`) and passes — confirming the route is
fine.

## Decision
Per D2 (route is source of truth unless caller evidence pins
otherwise), this is a **test edit**. Replace `"family"` with
`"Italo"` in `_login_and_select` of
`tests/test_t99_assets_patch.py`. One-line change.

## Fix
```diff
-    data={"username": "family", "password": "test-password"},
+    data={"username": "Italo", "password": "test-password"},
```

Verified: `test_patch_asset_cross_profile_404` continues to pass
(it logs in as Italo and PATCHes Ana's seeded asset — the
ownership check rejects with 404, which is what the test asserts).