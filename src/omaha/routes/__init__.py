"""HTTP route packages for the Omaha app.

Each submodule mounts a :class:`fastapi.APIRouter` and ``main.py``
includes them with their respective prefixes (most are mounted at the
root for now). The package itself is intentionally empty so future
slices can add new route modules without touching ``main.py``'s import
list.
"""

from __future__ import annotations

__all__: list[str] = []
