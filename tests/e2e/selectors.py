"""Central selector inventory for the e2e suite.

Every ``data-testid`` / ``aria-*`` / role selector referenced by
the e2e tests MUST be sourced from this module so UI changes
surface as a single inventory update rather than hidden
per-file rot. See spec ``e2e-selector-pinning``.

This module is intentionally pytest-free: it is plain data so
that the central import has no fixture or runtime cost.
"""

from __future__ import annotations

SELECTORS: dict[str, str] = {
    # ── Login + header ─────────────────────────────────────────────
    "login_user": 'input[name="username"]',
    "login_pass": 'input[name="password"]',
    "login_submit": 'button[type="submit"]',
    "app_header_wordmark": '[data-testid="app-header-wordmark"]',
    # F02: profile-name removed in favour of profile-switcher <select>.
    # Tests should reference profile_switcher instead of profile-name.
    "profile_switcher": '[data-testid="profile-switcher"]',
    "profile_picker": "form.profile-picker button",
    # ── Tab nav (F02 D2) ───────────────────────────────────────────
    "app_tab_btn_patrimonio": '[data-testid="app-tab-btn-patrimonio"]',
    "app_tab_btn_rebalanceamento": '[data-testid="app-tab-btn-rebalanceamento"]',
    "app_tab_btn_rentabilidade": '[data-testid="app-tab-btn-rentabilidade"]',
    "app_tab_btn_proventos": '[data-testid="app-tab-btn-proventos"]',
    "app_tab_nav": '[data-testid="app-tab-nav"]',
    # ── Patrimonio portfolio header ────────────────────────────────
    "patrimonio_portfolio_header": '[data-testid="patrimonio-portfolio-header"]',
    "patrimonio_actions": '[data-testid="patrimonio-actions"]',
    # Legacy portfolio header (kept for back-compat with the S05 suite
    # until that slice retires the alias).
    "portfolio_header": '[data-testid="portfolio-header"]',
    "portfolio_invested": '[data-testid="portfolio-invested"]',
    "portfolio_total": '[data-testid="portfolio-total"]',
    "portfolio_gain": '[data-testid="portfolio-gain"]',
    # ── Class summary ──────────────────────────────────────────────
    "class_summary_row": '[data-testid="class-summary-row"]',
    "class_section_header": '[data-testid="class-section-header"]',
    "dashboard_class_section": '[data-testid="class-section-header"]',
    "class_chevron": '[data-testid="class-chevron"]',
    "class_section_name": '[data-testid="class-section-name"]',
    "class_color_swatch": '[data-testid="class-color-swatch"]',
    "class_target_pct": '[data-testid="class-target-pct-view"]',
    "class_current_pct": '[data-testid="class-current-pct"]',
    "class_delta_badge": '[data-testid="class-delta-badge"]',
    "class_delete_btn": '[data-testid="class-delete-btn"]',
    "class_delete_confirm": '[data-testid="class-delete-confirm"]',
    "class_delete_confirm_yes": '[data-testid="class-delete-confirm-yes"]',
    "class_delete_confirm_no": '[data-testid="class-delete-confirm-no"]',
    "class_delete_confirm_error": '[data-testid="class-delete-confirm-error"]',
    # ── Asset row + table ──────────────────────────────────────────
    "dashboard_asset_row": '[data-testid="dashboard-asset-row"]',
    "asset_row_name": '[data-testid="asset-row-name"]',
    "asset_row_name_text": '[data-testid="asset-row-name-text"]',
    "asset_position_count": '[data-testid="asset-position-count"]',
    "asset_avg_price": '[data-testid="asset-avg-price"]',
    "asset_current_value": '[data-testid="asset-current-value"]',
    "asset_position_deviation": '[data-testid="asset-position-deviation"]',
    "asset_pct": '[data-testid="asset-pct"]',
    "asset_target_pct_class": '[data-testid="asset-target-pct-class"]',
    "asset_current_pct_class": '[data-testid="asset-current-pct-class"]',
    "asset_class_deviation": '[data-testid="asset-class-deviation"]',
    "asset_target_pct_total": '[data-testid="asset-target-pct-total"]',
    "asset_current_pct_total": '[data-testid="asset-current-pct-total"]',
    "asset_portfolio_deviation": '[data-testid="asset-portfolio-deviation"]',
    "asset_target_pct_total_edit_input": '[data-testid="asset-target-pct-total-edit-input"]',
    "asset_inline_edit_input": '[data-testid="asset-inline-edit-input"]',
    "asset_table": '[data-testid="asset-table"]',
    "asset_table_th_name": '[data-testid="asset-table-th-name"]',
    "asset_table_th_qty": '[data-testid="asset-table-th-qty"]',
    "asset_table_th_avg_price": '[data-testid="asset-table-th-avg-price"]',
    "asset_table_th_gain": '[data-testid="asset-table-th-gain"]',
    "asset_table_th_position": '[data-testid="asset-table-th-position"]',
    "asset_table_th_position_deviation": '[data-testid="asset-table-th-position-deviation"]',
    "asset_table_th_current_value": '[data-testid="asset-table-th-current-value"]',
    "asset_table_th_class_current": '[data-testid="asset-table-th-class-current"]',
    "asset_table_th_class_target": '[data-testid="asset-table-th-class-target"]',
    "asset_table_th_class_deviation": '[data-testid="asset-table-th-class-deviation"]',
    "asset_table_th_target_pct_class": '[data-testid="asset-table-th-target-pct-class"]',
    "asset_table_th_portfolio_current": '[data-testid="asset-table-th-portfolio-current"]',
    "asset_table_th_portfolio_target": '[data-testid="asset-table-th-portfolio-target"]',
    "asset_table_th_portfolio_deviation": '[data-testid="asset-table-th-portfolio-deviation"]',
    "asset_table_th_target_pct_total": '[data-testid="asset-table-th-target-pct-total"]',
    "asset_table_th_current_pct_total": '[data-testid="asset-table-th-current-pct-total"]',
    "asset_allocation_alert": '[data-testid="asset-allocation-alert"]',
    "asset_allocation_alert_portfolio": '[data-testid="asset-allocation-alert-portfolio"]',
    "asset_allocation_alert_class": '[data-testid="asset-allocation-alert-class"]',
    "dashboard_asset_delete_btn": '[data-testid="dashboard-asset-delete-btn"]',
    "dashboard_asset_delete_confirm": '[data-testid="dashboard-asset-delete-confirm"]',
    "dashboard_asset_delete_confirm_yes": '[data-testid="dashboard-asset-delete-confirm-yes"]',
    "dashboard_asset_delete_confirm_no": '[data-testid="dashboard-asset-delete-confirm-no"]',
    "dashboard_asset_delete_confirm_error": '[data-testid="dashboard-asset-delete-confirm-error"]',
    # ── Add-asset modal ────────────────────────────────────────────
    "dashboard_add_asset_open": '[data-testid="dashboard-add-asset-open"]',
    "add_asset_modal_overlay": '[data-testid="add-asset-modal-overlay"]',
    "dashboard_add_asset_modal": '[data-testid="add-asset-modal-overlay"]',
    "dashboard_add_asset_class": '[data-testid="dashboard-add-asset-modal-class"]',
    "dashboard_add_asset_name": '[data-testid="dashboard-add-asset-name"]',
    "dashboard_add_asset_pct": '[data-testid="dashboard-add-asset-target-pct"]',
    "dashboard_add_asset_target_pct": '[data-testid="dashboard-add-asset-target-pct"]',
    "dashboard_add_asset_submit": '[data-testid="dashboard-add-asset-submit"]',
    "dashboard_add_asset_cancel": '[data-testid="dashboard-add-asset-cancel"]',
    "dashboard_add_asset_error": '[data-testid="dashboard-add-asset-error"]',
    # ── New-class modal ────────────────────────────────────────────
    "new_class_modal_overlay": '[data-testid="new-class-modal-overlay"]',
    "new_class_modal_name_input": '[data-testid="new-class-modal-name-input"]',
    "new_class_modal_pct_input": '[data-testid="new-class-modal-pct-input"]',
    "new_class_modal_submit": '[data-testid="new-class-modal-submit"]',
    "new_class_modal_cancel": '[data-testid="new-class-modal-cancel"]',
    "new_class_modal_error": '[data-testid="new-class-modal-error"]',
    "empty_state": '[data-testid="empty-state-onboarding"]',
    "empty_state_create_class_btn": '[data-testid="empty-state-create-class"]',
    "empty_state_create_class": '[data-testid="empty-state-create-class"]',
    # ── F07 Família-as-profile option (peer of real profiles) ─────
    # The Família sentinel renders as a ``<option>`` inside the
    # ``profile-switcher`` ``<select>``; the legacy F01/F06 header
    # toggle is gone (``family-toggle*`` and ``household-toggle*``
    # testids are no longer emitted by any template). New code MUST
    # target ``profile_option_family`` (or
    # ``profile-switcher-optgroup`` for the visual separator).
    "profile_option_family": '[data-testid="profile-option-family"]',
    "profile_switcher_optgroup": '[data-testid="profile-switcher-optgroup"]',
    # ── Import modal ───────────────────────────────────────────────
    "dashboard_import_btn": '[data-testid="dashboard-import-btn"]',
    "import_modal_overlay": '[data-testid="import-modal-overlay"]',
    "import_file_input": '[data-testid="import-file-input"]',
    "import_upload_btn": '[data-testid="import-upload-btn"]',
    "import_modal_error": '[data-testid="import-upload-error"]',
    "import_upload_error": '[data-testid="import-upload-error"]',
    "import_commit_btn": '[data-testid="import-commit-btn"]',
    "import_commit_error": '[data-testid="import-commit-error"]',
    "import_unmatched_table": '[data-testid="import-unmatched-table"]',
    "import_unmatched_row": '[data-testid="import-unmatched-row"]',
    "import_existing_table": '[data-testid="import-existing-table"]',
    "import_existing_row": '[data-testid="import-existing-row"]',
    "import_class_cell_assignment": '[data-testid="import-class-cell-assignment"]',
    "import_class_swatch": ".import-class-swatch",
    "import_assignment_class": '[data-testid="import-assignment-class"]',
    "import_assignment_name": '[data-testid="import-assignment-name"]',
    "import_matched_summary": '[data-testid="import-matched-summary"]',
    # ── Rebalance page (in-body form, F02 D9) ──────────────────────
    "rebalance_form": '[data-testid="rebalance-form"]',
    "rebalance_contribution_input": '[data-testid="rebalance-contribution-input"]',
    "rebalance_submit_btn": '[data-testid="rebalance-submit-btn"]',
    "rebalance_card": '[data-testid="rebalance-card"]',
    "rebalance_empty_state": '[data-testid="rebalance-empty-state"]',
    "rebalance_placeholder": '[data-testid="rebalance-placeholder"]',
    "rebalance_plan": '[data-testid="rebalance-plan"]',
    "rebalance_applied_policy": '[data-testid="rebalance-applied-policy"]',
    "rebalance_stub_banner": '[data-testid="rebalance-stub-banner"]',
    "rebalance_warnings": '[data-testid="rebalance-warnings"]',
    "rebalance_stat_grid": '[data-testid="rebalance-stat-grid"]',
    "rebalance_stat_contribution": '[data-testid="rebalance-stat-contribution"]',
    "rebalance_stat_total_buy": '[data-testid="rebalance-stat-total-buy"]',
    "rebalance_stat_total_sell": '[data-testid="rebalance-stat-total-sell"]',
    "rebalance_stat_residual_cash": '[data-testid="rebalance-stat-residual-cash"]',
    "rebalance_stat_current_deviation": '[data-testid="rebalance-stat-current-deviation"]',
    "rebalance_stat_projected_deviation": '[data-testid="rebalance-stat-projected-deviation"]',
    "rebalance_asset_table": '[data-testid="rebalance-asset-table"]',
    "rebalance_asset_th_current_value": '[data-testid="rebalance-asset-th-current-value"]',
    "rebalance_category_table": '[data-testid="rebalance-category-table"]',
    "rebalance_form_error": '[data-testid="rebalance-form-error"]',
}


# Subset of SELECTORS that MUST resolve on the /patrimonio page
# (when authenticated with at least one class). Used by the
# selector-inventory smoke. Anything not in this set lives on a
# different page (login, /rebalanceamento, etc.) and is exempt
# from the smoke check.
DASHBOARD_SELECTORS: dict[str, str] = {
    k: v
    for k, v in SELECTORS.items()
    if k
    not in (
        # Login surface (different page).
        "login_user",
        "login_pass",
        "login_submit",
        # Header chip — only present when an active profile is
        # bound, which the smoke already does, but the
        # ``<select>`` options are rendered from a store, not a
        # DOM ``data-testid``.
        "profile_switcher",
        # /rebalanceamento-only surface.
        "rebalance_form",
        "rebalance_contribution_input",
        "rebalance_submit_btn",
        "rebalance_card",
        "rebalance_empty_state",
        "rebalance_placeholder",
        "rebalance_plan",
        "rebalance_applied_policy",
        "rebalance_stub_banner",
        "rebalance_warnings",
        "rebalance_stat_grid",
        "rebalance_stat_contribution",
        "rebalance_stat_total_buy",
        "rebalance_stat_total_sell",
        "rebalance_stat_residual_cash",
        "rebalance_stat_current_deviation",
        "rebalance_stat_projected_deviation",
        "rebalance_asset_table",
        "rebalance_asset_th_current_value",
        "rebalance_category_table",
        "rebalance_form_error",
        # Import modal — only visible after ``$store.importModal.open``
        # is true. The smoke does not open it.
        "import_modal_overlay",
        "import_file_input",
        "import_upload_btn",
        "import_modal_error",
        "import_upload_error",
        "import_commit_btn",
        "import_commit_error",
        "import_unmatched_table",
        "import_unmatched_row",
        "import_existing_table",
        "import_existing_row",
        "import_class_cell_assignment",
        "import_class_swatch",
        "import_assignment_class",
        "import_assignment_name",
        "import_matched_summary",
        # Add-asset modal — same gating.
        "add_asset_modal_overlay",
        "dashboard_add_asset_modal",
        "dashboard_add_asset_class",
        "dashboard_add_asset_name",
        "dashboard_add_asset_pct",
        "dashboard_add_asset_target_pct",
        "dashboard_add_asset_submit",
        "dashboard_add_asset_cancel",
        "dashboard_add_asset_error",
        # New-class modal — same gating.
        "new_class_modal_overlay",
        "new_class_modal_name_input",
        "new_class_modal_pct_input",
        "new_class_modal_submit",
        "new_class_modal_cancel",
        "new_class_modal_error",
        # Empty-state create-class button — only visible when the
        # active profile has zero classes (smoke seeds one).
        "empty_state",
        "empty_state_create_class_btn",
        "empty_state_create_class",
        # Class-section chevron — only on the asset-table view.
        "class_chevron",
        # Asset-table per-column header cells — only rendered when
        # the table is expanded. The class section starts
        # collapsed by default.
        "asset_table_th_name",
        "asset_table_th_class",
        "asset_table_th_qty",
        "asset_table_th_current_value",
        "asset_table_th_target_pct_class",
        "asset_table_th_current_pct_class",
        "asset_table_th_target_pct_total",
        "asset_table_th_current_pct_total",
        # Legacy S05 portfolio-header aliases — retired in F02.
        "portfolio_header",
        "portfolio_invested",
        "portfolio_total",
        "portfolio_gain",
        # Class delete confirmation surfaces — only after the
        # destructive button is clicked.
        "class_delete_btn",
        "class_delete_confirm",
        "class_delete_confirm_yes",
        "class_delete_confirm_no",
        "class_delete_confirm_error",
        # Asset delete confirmation surfaces.
        "dashboard_asset_delete_btn",
        "dashboard_asset_delete_confirm",
        "dashboard_asset_delete_confirm_yes",
        "dashboard_asset_delete_confirm_no",
        "dashboard_asset_delete_confirm_error",
        # Inline-edit input — only visible while editing a cell.
        "asset_inline_edit_input",
        "asset_target_pct_total_edit_input",
        # Allocation alert — only renders when the portfolio is
        # off-target.
        "asset_allocation_alert",
        "asset_allocation_alert_portfolio",
        "asset_allocation_alert_class",
        # Profile picker button — only on the no-active-profile
        # landing. Smoke has an active profile.
        "profile_picker",
        # App-header wordmark — retired in F02 alongside the
        # sidebar. The top nav replaces it.
        "app_header_wordmark",
    )
}
