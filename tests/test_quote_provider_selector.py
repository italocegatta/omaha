"""Unit tests for :func:`omaha.quotes.provider.get_quote_provider`.

Four cases covering the settings-driven selector contract:

1. Default (``"yfinance"``) resolves to :class:`YFinanceProvider`.
2. ``"stub"`` resolves to :class:`StubProvider`.
3. Unknown value raises :class:`ValueError` quoting the offender.
4. The selector does not cache — two calls return two distinct
   instances (the :func:`functools.lru_cache` alternative was
   rejected in design D-R03.2; this test pins that decision).

Settings are mutated per-test via ``monkeypatch.setattr`` on
``omaha.config.settings``. The selector reads ``settings`` lazily
inside the function, so swapping the module attribute makes the
next call observe the new value.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from omaha.config import Settings
from omaha.quotes.provider import StubProvider, YFinanceProvider, get_quote_provider

if TYPE_CHECKING:
    pass


def _build_settings(**overrides: object) -> Settings:
    """Build a fresh ``Settings`` instance with the given overrides."""
    return Settings(**overrides)


def test_default_settings_resolve_to_yfinance_provider(monkeypatch) -> None:
    """``Settings()`` defaults to ``"yfinance"``; selector returns ``YFinanceProvider``."""
    import omaha.config as config_mod

    monkeypatch.setattr(config_mod, "settings", _build_settings())
    provider = get_quote_provider()
    assert isinstance(provider, YFinanceProvider)


def test_stub_setting_resolves_to_stub_provider(monkeypatch) -> None:
    """``Settings(QUOTE_PROVIDER="stub")`` resolves to ``StubProvider``."""
    import omaha.config as config_mod

    monkeypatch.setattr(config_mod, "settings", _build_settings(QUOTE_PROVIDER="stub"))
    provider = get_quote_provider()
    assert isinstance(provider, StubProvider)


def test_unknown_provider_name_raises_value_error(monkeypatch) -> None:
    """Defense-in-depth: the selector raises ``ValueError`` for an invalid name.

    Pydantic-settings ``Literal[...]`` validation normally rejects a
    bad value at ``Settings()`` construction time (the L1 guard). The
    selector carries an L2 ``ValueError`` so a runtime bypass — for
    example, an attribute set in a test that does not go through the
    validator — still fails loudly instead of silently returning
    ``None``. This test exercises the bypass path by mutating the
    attribute directly.
    """
    import omaha.config as config_mod

    fake_settings = _build_settings()
    fake_settings.QUOTE_PROVIDER = "brapi"  # bypass Literal validation
    monkeypatch.setattr(config_mod, "settings", fake_settings)
    try:
        get_quote_provider()
    except ValueError as exc:
        assert "brapi" in str(exc), f"expected 'brapi' in the error message, got: {exc!r}"
    else:
        raise AssertionError("expected ValueError for unknown QUOTE_PROVIDER")


def test_selector_does_not_cache(monkeypatch) -> None:
    """Two back-to-back calls return two distinct instances (no caching)."""
    import omaha.config as config_mod

    monkeypatch.setattr(config_mod, "settings", _build_settings())
    first = get_quote_provider()
    second = get_quote_provider()
    assert first is not second
