"""Regression test for the port-collision flake in tests/e2e/conftest.

Background
----------
``TestS04ImportJourney::test_expired_preview_shows_expirado`` failed
intermittently in ``task test`` (the full pytest session) but passed
in isolation. Investigation (see
``openspec/changes/investigate-expired-preview-flake``) ruled out
the inode-race hypothesis and landed on a port collision:

- ``tests/bdd/conftest.py`` binds ``BDD_PORT = 8766``
- ``tests/e2e/conftest.py::TEST_PORT_SHORT_TTL`` was also ``8766``

The bdd session-scoped uvicorn grabs 8766 first. When the e2e
``live_url_short_ttl`` fixture later tries to bind 8766, the bind
either fails or the kernel rebinds, but the test then talks to
whichever uvicorn is bound on 8766 (the bdd one, with the default
``PREVIEW_TTL_SECONDS=3600`` and ``data/test_bdd.db``). The
1.5-second ``wait_for_timeout`` is meaningless against an hourly
TTL → the GET returns 200, the test fails.

This test pins the contract that the three session-scoped ports
must be unique. If a future change reintroduces a collision, this
test fails with a clear message before the flake can return.
"""

from __future__ import annotations

import importlib

import pytest


@pytest.fixture(scope="module")
def e2e_conftest():
    """Import ``tests.e2e.conftest`` without triggering the e2e
    collection path. The module defines fixtures, not tests, so
    importing it does not start a browser or a uvicorn."""
    return importlib.import_module("tests.e2e.conftest")


@pytest.fixture(scope="module")
def bdd_conftest():
    """Import ``tests.bdd.conftest`` for the same reason as above."""
    return importlib.import_module("tests.bdd.conftest")


def test_e2e_ports_are_unique_across_suites(e2e_conftest, bdd_conftest) -> None:
    """All session-scoped uvicorn ports MUST be distinct.

    The bdd suite and the e2e suite both spin up a session-scoped
    uvicorn. If they share a port, the second to start either
    fails to bind (and the test that needed it crashes) or
    silently talks to the first uvicorn (and the test sees the
    wrong DB + wrong TTL, returning unexpected status codes).
    Either failure mode is invisible to the test that triggered
    it — the only signal is the e2e test failing with an
    unexpected status. Pinning the port assignment here makes
    the failure mode loud at collection time.
    """
    e2e_main = e2e_conftest.TEST_PORT
    e2e_short = e2e_conftest.TEST_PORT_SHORT_TTL
    bdd = bdd_conftest.BDD_PORT

    ports = {
        "tests.e2e TEST_PORT": e2e_main,
        "tests.e2e TEST_PORT_SHORT_TTL": e2e_short,
        "tests.bdd BDD_PORT": bdd,
    }
    assert len(set(ports.values())) == len(ports), (
        f"port collision between session-scoped uvicorn fixtures: "
        f"{ports}. Each uvicorn fixture MUST bind a unique port; "
        f"otherwise the second fixture either fails to bind or "
        f"silently proxies to the first. See "
        f"openspec/changes/investigate-expired-preview-flake."
    )


@pytest.mark.parametrize(
    "port_name,port_value",
    [
        ("tests.e2e TEST_PORT", "TEST_PORT"),
        ("tests.e2e TEST_PORT_SHORT_TTL", "TEST_PORT_SHORT_TTL"),
    ],
)
def test_e2e_ports_are_in_safe_range(e2e_conftest, port_name: str, port_value: str) -> None:
    """The e2e ports MUST sit in the IANA dynamic/private range.

    8765/8766/8767 are below 9000 by convention here; anything
    outside 1024-65535 is either privileged or reserved. This
    guards against typos (e.g. ``TEST_PORT = 876`` — drops the
    tens digit and collides with other test infra on 876).
    """
    port = getattr(e2e_conftest, port_value)
    assert 1024 <= port <= 65535, (
        f"{port_name}={port} is outside the safe IANA dynamic range "
        f"(1024-65535). Pick a port in the 8765-8799 band that no "
        f"other session-scoped uvicorn uses."
    )


def test_e2e_short_ttl_port_is_not_bdd_port(e2e_conftest, bdd_conftest) -> None:
    """Explicit guard for the original flake: e2e short_ttl MUST
    not bind the bdd port. The previous failure mode was exactly
    this collision (8766 shared by both), so call it out by name
    in the assertion message.
    """
    assert e2e_conftest.TEST_PORT_SHORT_TTL != bdd_conftest.BDD_PORT, (
        f"TEST_PORT_SHORT_TTL={e2e_conftest.TEST_PORT_SHORT_TTL} collides "
        f"with BDD_PORT={bdd_conftest.BDD_PORT}. This is the exact "
        f"collision that caused the expired-preview flake; see "
        f"openspec/changes/investigate-expired-preview-flake."
    )


def test_e2e_short_ttl_base_url_matches_declared_port(
    e2e_conftest,
) -> None:
    """The ``TEST_BASE_URL_SHORT_TTL`` string MUST encode the same
    port as ``TEST_PORT_SHORT_TTL``. A drift between the two
    means the e2e test calls a different URL than the fixture
    binds, which is the kind of bug that becomes invisible when
    another uvicorn is already listening on the bound port.
    """
    base = e2e_conftest.TEST_BASE_URL_SHORT_TTL
    port = e2e_conftest.TEST_PORT_SHORT_TTL
    assert base.endswith(f":{port}"), (
        f"TEST_BASE_URL_SHORT_TTL={base!r} does not end with "
        f":{port} (TEST_PORT_SHORT_TTL). The fixture's bound port "
        f"and the URL the tests point at MUST agree."
    )
