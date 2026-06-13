"""CSS color-contrast audit tooling for the Omaha app.

Each submodule provides the building blocks for a static analysis
audit that inventories every CSS custom property that resolves to a
color and computes its WCAG 2.1 AA contrast ratio. The package
itself is intentionally empty so future slices can add new audit
modules without touching the import list.
"""

from __future__ import annotations

__all__: list[str] = []
