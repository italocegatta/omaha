## ADDED Requirements

### Requirement: Both profiles ship configured and populated with seed, classes, assets, and target allocation

The system MUST, after any canonical delivery task (`uv run
task db-reset` or equivalent), hold two profiles — `Italo` and
`Ana` — and BOTH profiles MUST be populated from the
per-profile CSV triplet:

- `data/seed/{profile}_classes.csv` → `AssetClass` rows with
  `target_pct` summing to 100 (the **target allocation**).
- `data/seed/{profile}_assets.csv` → `Asset` rows under each
  class, with per-class `target_pct` summing to 100.
- `data/seed/{profile}_positions.csv` → `Position` rows linked
  to the `Asset` rows above.

The canonical delivery task SHALL seed both profiles in one
invocation (not require two separate `task db-seed-from-csv
--profile italo` + `--profile ana` calls). The pre-change state
(only Italo populated) is non-conformant.

#### Scenario: db-reset seeds Italo and Ana from their CSV triplets

- **WHEN** an operator runs `uv run task db-reset` on an empty
  database after `uv run task db-migrate` + `uv run task db-seed`
- **THEN** the `users` table holds rows for `Italo` and `Ana`
- **AND** the `profiles` table holds two rows, one per user,
  with `display_order` matching `seed.DEFAULT_USERS`
  (`Italo=0`, `Ana=1`)
- **AND** Italo's profile owns ≥6 `AssetClass` rows whose
  `target_pct` sums to 100 within tolerance 0.01
- **AND** Ana's profile owns ≥6 `AssetClass` rows whose
  `target_pct` sums to 100 within tolerance 0.01
- **AND** each profile owns `Asset` rows whose per-class
  `target_pct` sums to 100 within tolerance 0.01
- **AND** each profile owns `Position` rows for the assets
  listed in its `{profile}_positions.csv`

#### Scenario: Ana's CSV triplet is the source of truth for her profile

- **WHEN** an operator edits `data/seed/ana_classes.csv`,
  `ana_assets.csv`, or `ana_positions.csv` and re-runs the
  canonical delivery task
- **THEN** Ana's `AssetClass` / `Asset` / `Position` rows in
  the database reflect the CSV edits
- **AND** Italo's rows are NOT modified by the Ana edit

#### Scenario: Both profiles render populated dashboards after direct login

- **WHEN** Ana logs in (no manual `/profiles/{id}/select`
  needed) via the new direct-landing flow
- **THEN** `GET /` renders Ana's dashboard with her
  `AssetClass` rows visible (not the empty-state copy)
- **AND** when Ana switches to Italo via the header chip, `GET /`
  renders Italo's dashboard with his `AssetClass` rows visible
  (not Ana's)
- **AND** switching back to Ana restores Ana's populated
  dashboard

#### Scenario: Sum invariant is enforced per profile

- **WHEN** any `{profile}_classes.csv` is edited so its
  `target_pct` no longer sums to 100 within tolerance 0.01
- **THEN** the canonical delivery task aborts BEFORE any DB
  write for that profile, with a clear
  `Falta X%` / `Sobra X%` message naming the offending file
- **AND** no `AssetClass` row is created or updated for the
  failing profile in that run
- **AND** the other profile's data is left intact (the failure
  is scoped to the failing profile)

### Requirement: Seed path is the only path that creates AssetClass, Asset, and Position rows

The system SHALL NOT introduce inline literal, hardcoded, or
ad-hoc code paths that create `AssetClass`, `Asset`, or
`Position` rows outside the CSV path consumed by
`scripts/seed_from_csv.py`. `src/omaha/seed.py` remains the
canonical user + profile seed and SHALL NOT be extended to
seed asset or position data.

#### Scenario: No new asset/position seed paths outside CSV

- **WHEN** a reviewer inspects the change's diff
- **THEN** no production code under `src/omaha/` (other than
  `scripts/seed_from_csv.py`) creates `AssetClass`, `Asset`,
  or `Position` rows
- **AND** no demo / smoke / pre-population script bypasses the
  CSV path

### Requirement: Delivery finalization verifies both profiles are populated

The delivery checklist MUST, before reporting any browser-
visible change as done, verify that BOTH profiles render
populated dashboards (Ana, not only Italo, must show classes
and assets). An asset-free state after `db-reset` is a
delivery failure.

#### Scenario: Delivery check covers both profiles

- **WHEN** the `refresh-for-test` skill runs the finalization
  checklist after this change applies
- **THEN** the checklist asserts Italo's `AssetClass` count
  ≥ 6 AND Ana's `AssetClass` count ≥ 6
- **AND** asserts Italo's `Asset` count ≥ 1 AND Ana's
  `Asset` count ≥ 1
- **AND** reports the LAN URL with both profiles visible from
  either login
