"""Thin wrapper around ``omaha.audit.cli.main``.

Run this script from the repository root to generate the contrast
audit report::

    uv run python scripts/generate_contrast_audit.py

By default the report is written to ``reports/contrast_audit.html``.
Pass ``--output`` to override the destination::

    uv run python scripts/generate_contrast_audit.py --output /tmp/my-audit.html
"""

from __future__ import annotations

import sys

from omaha.audit.cli import main

if __name__ == "__main__":  # pragma: no cover - script entry point
    sys.exit(main())
