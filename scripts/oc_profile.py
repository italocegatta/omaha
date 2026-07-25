"""Profile-based model/provider/effort launcher for OpenCode agents.

Resolves a named profile (built-in or TOML-defined), exports per-role
environment variables, and ``execv``'s into OpenCode so each terminal
session runs with its own isolated configuration.

Resolution chain (highest priority first):
  1. CLI ``--profile <name>``
  2. Env var ``OPENCODE_PROFILE``
  3. ``profiles.toml`` [default] profile
  4. Built-in default: ``xiaomi-balanced``

Usage::

    uv run task oc -- --profile openai-cheap
    uv run task oc -- --list-profiles
    uv run task oc                          # uses default profile

Dev tooling only — no production code change.
"""

from __future__ import annotations

import os
import sys
import tomllib
from dataclasses import dataclass
from pathlib import Path

# ── Data model ──────────────────────────────────────────────────────────────

ROLES: tuple[str, ...] = (
    "roadmap",
    "propose",
    "apply",
    "review",
    "finalize",
    "explore",
    "slice",
)


@dataclass(frozen=True, slots=True)
class Profile:
    """Per-role (provider, model, effort) triple."""

    provider: str
    model: str
    effort: str


# Built-in profiles — 7 roles × (provider, model, effort).
# Keys are role names; values are Profile instances.
_BUILTIN: dict[str, dict[str, Profile]] = {
    "openai-cheap": {
        "roadmap": Profile("openai", "gpt-5.4-mini", "high"),
        "propose": Profile("openai", "gpt-5.4-mini", "high"),
        "apply": Profile("openai", "gpt-5.4-mini", "high"),
        "review": Profile("openai", "gpt-5.4-mini", "high"),
        "finalize": Profile("openai", "gpt-5.4-mini", "high"),
        "explore": Profile("openai", "gpt-5.4-mini", "high"),
        "slice": Profile("openai", "gpt-5.4-mini", "high"),
    },
    "openai-balanced": {
        "roadmap": Profile("openai", "gpt-5.4", "high"),
        "propose": Profile("openai", "gpt-5.4", "high"),
        "apply": Profile("openai", "gpt-5.4", "high"),
        "review": Profile("openai", "gpt-5.4-mini", "high"),
        "finalize": Profile("openai", "gpt-5.4-mini", "high"),
        "explore": Profile("openai", "gpt-5.4", "high"),
        "slice": Profile("openai", "gpt-5.4", "high"),
    },
    "openai-xiaomi-balanced": {
        "roadmap": Profile("openai", "gpt-5.4-mini", "high"),
        "propose": Profile("xiaomi-token-plan-sgp", "mimo-v2.5-pro", "medium"),
        "apply": Profile("xiaomi-token-plan-sgp", "mimo-v2.5-pro", "medium"),
        "review": Profile("xiaomi-token-plan-sgp", "mimo-v2.5", "medium"),
        "finalize": Profile("xiaomi-token-plan-sgp", "mimo-v2.5", "medium"),
        "explore": Profile("xiaomi-token-plan-sgp", "mimo-v2.5-pro", "medium"),
        "slice": Profile("openai", "gpt-5.4-mini", "high"),
    },
    "xiaomi-balanced": {
        "roadmap": Profile("xiaomi-token-plan-sgp", "mimo-v2.5-pro", "medium"),
        "propose": Profile("xiaomi-token-plan-sgp", "mimo-v2.5-pro", "medium"),
        "apply": Profile("xiaomi-token-plan-sgp", "mimo-v2.5-pro", "medium"),
        "review": Profile("xiaomi-token-plan-sgp", "mimo-v2.5", "medium"),
        "finalize": Profile("xiaomi-token-plan-sgp", "mimo-v2.5", "medium"),
        "explore": Profile("xiaomi-token-plan-sgp", "mimo-v2.5-pro", "medium"),
        "slice": Profile("xiaomi-token-plan-sgp", "mimo-v2.5-pro", "medium"),
    },
}

BUILTIN_PROFILES: dict[str, dict[str, Profile]] = dict(_BUILTIN)

DEFAULT_PROFILE = "xiaomi-balanced"

PROFILE_DESCRIPTIONS: dict[str, str] = {
    "openai-cheap": "All roles: gpt-5.4-mini, high effort (cheapest OpenAI)",
    "openai-balanced": "Heavy roles: gpt-5.4, light roles: gpt-5.4-mini, high effort",
    "openai-xiaomi-balanced": "OpenAI for routing/slice, Xiaomi for execution, mixed effort",
    "xiaomi-balanced": "All roles: Xiaomi mimo models, medium effort (default, cheapest)",
}

REPO_ROOT = Path(__file__).resolve().parent.parent
TOML_PATH = REPO_ROOT / "profiles.toml"


# ── Profile resolution ──────────────────────────────────────────────────────


def _load_toml_profiles(path: Path = TOML_PATH) -> dict[str, dict[str, Profile]]:
    """Load profiles from a TOML file. Returns empty dict if file missing."""
    if not path.exists():
        return {}
    with open(path, "rb") as fh:
        data = tomllib.load(fh)
    profiles: dict[str, dict[str, Profile]] = {}
    for name, roles in data.get("profiles", {}).items():
        profiles[name] = {}
        for role_name, role_cfg in roles.items():
            profiles[name][role_name] = Profile(
                provider=role_cfg["provider"],
                model=role_cfg["model"],
                effort=role_cfg["effort"],
            )
    return profiles


def _resolve_profile_name(
    cli_arg: str | None = None,
    toml_path: Path = TOML_PATH,
) -> str:
    """Determine which profile name to use (resolution chain).

    Priority: CLI arg > OPENCODE_PROFILE env > TOML default > built-in default.
    """
    if cli_arg:
        return cli_arg

    env_val = os.environ.get("OPENCODE_PROFILE")
    if env_val:
        return env_val

    if toml_path.exists():
        with open(toml_path, "rb") as fh:
            data = tomllib.load(fh)
        toml_default = data.get("default", {}).get("profile")
        if toml_default:
            return toml_default

    return DEFAULT_PROFILE


def resolve_profile(
    name: str | None = None,
    toml_path: Path = TOML_PATH,
) -> dict[str, Profile]:
    """Resolve a profile by name, merging TOML overrides on top of built-in.

    Args:
        name: Profile name. If ``None``, uses resolution chain.
        toml_path: Path to profiles.toml.

    Returns:
        Dict mapping role name → Profile.

    Raises:
        ValueError: If profile name is unknown.
    """
    profile_name = _resolve_profile_name(cli_arg=name, toml_path=toml_path)

    # Merge built-in + TOML (TOML overrides).
    merged = dict(BUILTIN_PROFILES)
    toml_profiles = _load_toml_profiles(toml_path)
    for pname, roles in toml_profiles.items():
        if pname in merged:
            merged[pname] = {**merged[pname], **roles}
        else:
            merged[pname] = roles

    if profile_name not in merged:
        available = ", ".join(sorted(merged))
        raise ValueError(f"Unknown profile: {profile_name!r}. Available: {available}")

    return merged[profile_name]


# ── Env var export ──────────────────────────────────────────────────────────


def export_env_vars(profile: dict[str, Profile]) -> None:
    """Set ``OPENCODE_{ROLE}_MODEL``, ``_PROVIDER``, ``_EFFORT`` in os.environ."""
    for role_name, role_profile in profile.items():
        prefix = f"OPENCODE_{role_name.upper()}"
        os.environ[f"{prefix}_MODEL"] = role_profile.model
        os.environ[f"{prefix}_PROVIDER"] = role_profile.provider
        os.environ[f"{prefix}_EFFORT"] = role_profile.effort


# ── CLI ─────────────────────────────────────────────────────────────────────


def _print_profiles() -> None:
    """Print available profiles with one-line descriptions."""
    print("Available profiles:\n")
    for name in sorted(BUILTIN_PROFILES):
        desc = PROFILE_DESCRIPTIONS.get(name, "")
        marker = " (default)" if name == DEFAULT_PROFILE else ""
        print(f"  {name}{marker}")
        print(f"    {desc}")
    print()
    print(f"Default: {DEFAULT_PROFILE}")
    print("Override: --profile <name> or OPENCODE_PROFILE=<name>")


def _build_parser() -> object:
    """Minimal argparse parser (stdlib)."""
    import argparse

    parser = argparse.ArgumentParser(
        prog="oc_profile",
        description="Launch OpenCode with a named profile.",
    )
    parser.add_argument(
        "--profile",
        default=None,
        help="Profile name (default: xiaomi-balanced or profiles.toml default)",
    )
    parser.add_argument(
        "--list-profiles",
        action="store_true",
        help="Print available profiles and exit",
    )
    parser.add_argument(
        "--export-only",
        action="store_true",
        help="Print export commands instead of exec'ing (for testing)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Entry point. Returns exit code."""

    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.list_profiles:
        _print_profiles()
        return 0

    try:
        profile = resolve_profile(name=args.profile)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    export_env_vars(profile)

    if args.export_only:
        # Print exports for testing/debugging (don't exec).
        for role_name, role_profile in profile.items():
            prefix = f"OPENCODE_{role_name.upper()}"
            print(f"export {prefix}_MODEL={role_profile.model}")
            print(f"export {prefix}_PROVIDER={role_profile.provider}")
            print(f"export {prefix}_EFFORT={role_profile.effort}")
        return 0

    # execv into OpenCode — replaces this process.
    os.execvp("opencode", ["opencode"])
    # unreachable, but satisfy type checkers
    return 0  # pragma: no cover


if __name__ == "__main__":
    sys.exit(main())
