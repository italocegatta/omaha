## REMOVED Requirements

### Requirement: Sidebar renders on the dashboard
**Reason**: Sidebar removed in F02 — replaced by top nav with 4 tabs
(`Patrimônio | Rebalanceamento | Rentabilidade | Proventos`). No
drawer mobile, no off-canvas substitute.
**Migration**: Use the new top nav at
`data-testid="app-tab-nav"`. Action triggers (`Importar CSV`,
`+ Classe`, `+ Ativo`) live at the top of the `/patrimonio` body
and carry the same testids they had before
(`dashboard-import-btn`, `dashboard-add-asset-open`,
`empty-state-create-class`).

### Requirement: Sidebar wordmark uses Source Serif 4
**Reason**: Sidebar removed. Wordmark has no replacement — top nav
uses sans-serif tab labels instead.
**Migration**: Active profile name is shown in the profile picker
in the top nav (`data-testid="app-profile-picker"`).

### Requirement: Sidebar carries the action trigger testids
**Reason**: Action triggers migrated from sidebar to top of
`/patrimonio` body (see `patrimonio-portfolio-header` /
`dashboard-inline-editing` specs). Testids preserved.
**Migration**: Look for `data-testid="dashboard-import-btn"`,
`data-testid="dashboard-add-asset-open"`, and
`data-testid="empty-state-create-class"` at the top of the
`/patrimonio` body (not inside any sidebar element).

### Requirement: Active state indicator on sidebar buttons
**Reason**: Sidebar buttons removed. The active indicator pattern
(3px vertical bar in `--accent`) is now expressed via the
`tab-nav__btn--active` class on the active top-nav tab.
**Migration**: `aria-current="true"` moves from sidebar buttons to
the active top-nav tab.

### Requirement: New class modal posts to /api/classes
**Reason**: The underlying modal + endpoint contract is unchanged
in F02. This requirement lived in the sidebar spec for historical
reasons and is being moved to its proper home.
**Migration**: Spec coverage continues under
`dashboard-inline-editing` (which owns the new-class modal
behaviour). No code change.

### Requirement: Mobile off-canvas drawer
**Reason**: Sidebar removed; off-canvas drawer has no surface left
to live in. There is no longer anything off-canvas in the product.
**Migration**: Top nav is always visible. On viewports narrower
than 480px the tab labels collapse to short labels or icons
(visual decision deferred to the F02 design pass; behaviour
contract: tabs remain reachable without any drawer).

### Requirement: Hamburger visibility is gated by active profile
**Reason**: Hamburger button removed (no drawer).
**Migration**: Profile picker in the top nav (`app-profile-picker`)
gates availability the same way — only present when an active
profile exists.

### Requirement: 3-step zero-classes onboarding card
**Reason**: Onboarding card migrated from dashboard body to the
new `/patrimonio` empty state. Spec coverage continues under the
`onboarding-card` spec (when written) or inline in
`patrimonio-portfolio-header`'s empty profile scenario.
**Migration**: Look for `data-testid="empty-state-onboarding"` in
the `/patrimonio` body, not in a sidebar.
