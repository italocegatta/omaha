"""S06/T04 \u2014 Dockerfile + prod.yml sanity checks.

The three tests are opt-in via the ``RUN_DOCKER_E2E=1`` env var
because they require a working docker daemon + the ``omaha:prod``
image (built by T03's ``docker build -t omaha:prod .``). In CI and
on dev hosts without docker, the tests skip cleanly. The first
test in the file is the gate; setting ``RUN_DOCKER_E2E=1`` enables
all three.

What this file does NOT do: it does not bring up prod.yml (that
needs a real cert in ./certs and would race against the
``omaha-data`` named volume). The user's homelab is the only
environment where ``docker compose -f prod.yml up -d`` is meant
to run; this file is the smoke check, not a full e2e.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
DOCKER_IMAGE = "omaha:prod-test"


def _docker_available() -> bool:
    """Return True if a docker daemon is reachable and the CLI works.

    Skipping on a host without docker (CI runners, dev machines
    without the daemon) is the right behaviour; pytest's own
    collection should not fail just because docker is missing.
    """
    return shutil.which("docker") is not None and subprocess.run(
        ["docker", "info"], capture_output=True, check=False
    ).returncode == 0


def _run(cmd: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
    """Run ``cmd`` from the repo root and return the completed process.

    ``text=True`` so ``.stdout``/``.stderr`` come back as str (the
    default in pytest 7+ is bytes, which makes the assertion messages
    ugly).
    """
    return subprocess.run(  # noqa: S603 \u2014 controlled input
        cmd,
        cwd=str(REPO_ROOT),
        check=False,
        capture_output=True,
        text=True,
        **kwargs,
    )


# Opt-in gate. The first assertion the file makes is on this env
# var; the rest of the file is reachable only when the operator
# explicitly asked for the docker e2e.
_RUN_DOCKER_E2E = os.environ.get("RUN_DOCKER_E2E") == "1"


@pytest.mark.skipif(
    not _RUN_DOCKER_E2E, reason="set RUN_DOCKER_E2E=1 to enable docker e2e checks"
)
def test_docker_build_pro_image_succeeds() -> None:
    """``docker build -t omaha:prod-test .`` returns exit code 0.

    Uses a separate tag (``omaha:prod-test``) so this test does
    not clobber a ``omaha:prod`` image the operator has built by
    hand.
    """
    if not _docker_available():
        pytest.skip("docker daemon not reachable on this host")
    result = _run(
        ["docker", "build", "-t", DOCKER_IMAGE, "."],
        timeout=300,
    )
    assert result.returncode == 0, (
        f"docker build failed (exit={result.returncode}):\n"
        f"stdout={result.stdout!r}\nstderr={result.stderr!r}"
    )


@pytest.mark.skipif(
    not _RUN_DOCKER_E2E, reason="set RUN_DOCKER_E2E=1 to enable docker e2e checks"
)
def test_docker_run_pro_image_runs_as_omaha_user() -> None:
    """``docker run --rm omaha:prod-test id`` reports uid 1000(omaha).

    Confirms the USER directive in the prod Dockerfile actually
    applied (a typo there would let the container run as root).
    """
    if not _docker_available():
        pytest.skip("docker daemon not reachable on this host")
    # Build-on-demand so the previous test's image is not a
    # silent dependency.
    build = _run(["docker", "build", "-t", DOCKER_IMAGE, "."], timeout=300)
    assert build.returncode == 0, f"docker build failed: {build.stderr!r}"

    result = _run(["docker", "run", "--rm", DOCKER_IMAGE, "id"], timeout=30)
    assert result.returncode == 0, (
        f"docker run id failed: stdout={result.stdout!r} stderr={result.stderr!r}"
    )
    # ``id`` in the runtime image writes ``uid=1000(omaha) gid=1000(omaha) groups=1000(omaha)``
    # to stdout. The substring check is exact enough to catch
    # either a wrong UID (e.g. still 0 from a missed USER) or a
    # wrong username (e.g. ``app`` instead of ``omaha``).
    assert "uid=1000(omaha)" in result.stdout, (
        f"expected uid=1000(omaha) in id output, got: {result.stdout!r}"
    )


def test_prod_yml_is_valid_yaml() -> None:
    """``prod.yml`` parses as valid YAML (via tomllib on the YAML body).

    The plan called for ``tomllib.loads(...)`` as a smoke check;
    that was a typo \u2014 tomllib is TOML, not YAML. The right module
    is ``yaml`` (PyYAML) which is already a transitive dep via
    FastAPI; if it ever stops being a dep, we can fall back to
    ``python -c "import json; json.loads(...)"`` after running
    prod.yml through ``yq`` or a docker compose config dry-run.

    This test does NOT require RUN_DOCKER_E2E \u2014 the YAML parse
    runs in-process and is fast enough to be a default-green
    lint check.
    """
    prod_yml = REPO_ROOT / "prod.yml"
    assert prod_yml.exists(), f"{prod_yml} not found at expected path"

    # PyYAML is the import; we fail with a clear message if the
    # dev environment has dropped it.
    try:
        import yaml  # type: ignore[import-untyped]
    except ImportError:  # pragma: no cover - PyYAML is a hard dep
        pytest.fail(
            "PyYAML is not installed; the prod.yml validity check cannot run. "
            "Add `pyyaml` to pyproject.toml dependencies."
        )

    with prod_yml.open("rb") as fh:
        data = yaml.safe_load(fh)

    # Pin the three top-level services and the named volume. If
    # any of these is missing, an operator who runs `docker
    # compose -f prod.yml up -d` will get a confusing error from
    # compose; we catch it here first.
    assert isinstance(data, dict), f"prod.yml top-level is not a mapping: {type(data)}"
    services = data.get("services")
    assert isinstance(services, dict), "prod.yml is missing the `services` mapping"
    for name in ("web", "nginx", "backup"):
        assert name in services, (
            f"prod.yml is missing the {name!r} service under `services`"
        )
    # The backup service must be on a profile \u2014 otherwise it
    # would start with `up` and race the web container for the
    # same named volume mount.
    backup = services["backup"]
    assert "backup" in backup.get("profiles", []), (
        "prod.yml: backup service must declare `profiles: [backup]` so it does not "
        "start with `docker compose -f prod.yml up -d`"
    )
    # The named volume is the persistent DB.
    assert "omaha-data" in data.get("volumes", {}), (
        "prod.yml: top-level `volumes: omaha-data:` is required for SQLite persistence"
    )
    # Sanity: the web service must NOT publish ports. The
    # public/private split is the whole point of nginx in
    # front; an accidental `ports: [\"8000:8000\"]` would
    # bypass TLS and the https_only cookie flag.
    web_ports = services["web"].get("ports")
    assert not web_ports, (
        f"prod.yml: web service must not publish ports (nginx is the public bind), "
        f"got: {web_ports!r}"
    )
