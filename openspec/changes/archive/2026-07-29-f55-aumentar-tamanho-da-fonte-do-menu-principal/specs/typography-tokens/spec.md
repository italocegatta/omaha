## ADDED Requirements

### Requirement: Main nav labels render at maximal register size

The system SHALL render the four main tab-nav labels (Patrimônio, Rebalanceamento, Rentabilidade, Proventos — `.tab-nav__btn`) at `font-size: 1.35rem` on the desktop cascade and `font-size: 1.275rem` inside the `@media (max-width: 480px)` override. These sizes are +50% over the prior register (0.9rem / 0.85rem) and are part of the Status Invest maximal typography contract. The size change SHALL NOT alter face, weight, or color: inactive labels stay Inter 500 in `var(--ink-muted)`, and the active label stays Red Hat Display 700 in `var(--ink)` per the existing display-face requirement.

#### Scenario: Desktop nav label computes 1.35rem

- **WHEN** a page rendering the app tab nav (`data-testid="app-tab-nav"`) is loaded outside any mobile media query
- **THEN** `.tab-nav__btn` SHALL compute `font-size: 1.35rem` (21.6px at root 16px)
- **AND** the cascade rule in `app.css` SHALL declare `font-size: 1.35rem` for `.tab-nav__btn`

#### Scenario: Mobile nav label computes 1.275rem at ≤480px

- **WHEN** the viewport width is 480px or less
- **THEN** `.tab-nav__btn` SHALL compute `font-size: 1.275rem` (20.4px at root 16px) via the `@media (max-width: 480px)` override in `app.css`
- **AND** the override SHALL NOT change any other declaration on `.tab-nav__btn` beyond `font-size`

#### Scenario: Size change does not disturb the typography register

- **WHEN** the `.tab-nav__btn` rules in `app.css` are scanned after this change
- **THEN** `.tab-nav__btn` SHALL keep `font-weight: 500` and inactive color `var(--ink-muted)`
- **AND** `.tab-nav__btn--active` SHALL keep `"Red Hat Display"` first in its `font-family` chain at weight 700
- **AND** `font-family`, `gap`, `padding`, and `line-height` declarations SHALL be byte-identical to their pre-change state unless a deviation was explicitly justified in the change record
