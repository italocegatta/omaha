## 1. Spec and surface alignment

- [x] 1.1 Add dashboard-form-legibility spec with modal-width, spinner-free number input, and left-aligned profile selector requirements.
- [x] 1.2 Keep scope tight to `src/omaha/templates/_patrimonio_add_asset_modal.html`, `src/omaha/templates/base.html`, and `src/omaha/static/app.css`.

## 2. UI polish implementation

- [x] 2.1 Introduce modal-specific width/contrast treatment for add-asset modal fields.
- [x] 2.2 Remove native number spinner chrome from modal numeric inputs only, preserving keyboard stepping.
- [x] 2.3 Left-align profile-switcher option text / selected value and improve contrast for `Família`.

## 3. Verification

- [ ] 3.1 Check rendered header/modal visuals for spacing, alignment, and legibility.
- [ ] 3.2 Confirm no unrelated forms inherit the new spinner/width treatment.
