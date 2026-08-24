## ADDED Requirements

### Requirement: Additive MyProfit preview contract remains accepted by integration gate

The MyProfit sync-job integration contract SHALL preserve legacy preview keys
while accepting additive F65 `triage` data. The canonical blocking pre-push
integration gate SHALL continue to execute this contract through
`uv run task test-integration-parallel`; stale exact-shape expectations MUST be
corrected rather than hidden or bypassed.

#### Scenario: F65 additive preview passes without mutation regression

- **WHEN** `_process_downloaded_csv` publishes a preview containing
  `preview_id`, `auto_matched`, `unmatched`, `asset_classes`, and additive
  `triage`
- **THEN** the integration assertion accepts all five keys
- **AND** legacy keys, job status, no-Asset/Position/DbMutation-mutation
  behavior, cleanup, and security assertions remain enforced
- **AND** the pre-push hook continues to block on a real failure without
  skip, xfail, retry, or bypass behavior
