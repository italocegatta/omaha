# 1.3 GET /assets — 200 vs expected 302

## Reproduction
```bash
uv run pytest tests/test_s03_t05_assets_retire.py::test_get_assets_redirects_to_dashboard --tb=long -p no:cacheprovider
```
Captured traceback:
```
>       assert resp.status_code == 302
E       assert 200 == 302
```

## Diagnosis
Route registration: `src/omaha/routes/assets.py:87` — `@router.get("/assets", ...)`
returns a rendered `assets.html` template (200).

The test's docstring (`tests/test_s03_t05_assets_retire.py:3-10`)
explicitly states:
> The /assets page was retired in S03/T05 — the dedicated editor
> is replaced by inline asset management on the dashboard (S03/T03 + T04).
> Any request to GET /assets now returns 302 with Location "/".

`.planning/MILESTONES.md:14` confirms:
> Asset inline create/delete, retired `/assets` route.

The dashboard template (`src/omaha/templates/dashboard.html`) is
the canonical asset surface — it uses `POST /api/assets` and
`PATCH /api/assets/{id}` (lines 828, 922, 986). No template
references GET `/assets`.

The form-encoded `POST /assets` (create) and
`POST /assets/{id}/delete` (delete) routes remain wired (per the
docstring on line 9: "a future polish slice may prune them") but
the GET surface is dead and the dashboard replaces it.

## Decision
Per D2 + the route's own docstring + MILESTONES.md, this is a
**code edit** — retire the GET handler to a 302 → `/` redirect.
The other handlers stay; only the GET changes.

## Fix
```python
@router.get("/assets")
def get_assets(...) -> Response:
    """S03/T05 retired: the page is replaced by dashboard inline editing."""
    return RedirectResponse("/", status_code=302)
```

Update the route's docstring (the long one above the handler) to
mark `GET /assets` as retired.