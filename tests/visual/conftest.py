"""Fixtures and helpers for page-level visual regression tests.

Browser process is session-scoped so each screenshot test still gets a
fresh context/page but pays launch cost once per suite. That stays
safe because visual tests never share browser state across cases.
"""

from __future__ import annotations

import os
import sys
import zlib
from dataclasses import dataclass
from pathlib import Path
from struct import unpack
from typing import Literal

import pytest

from tests.support.browser import (
    compose_server_env,
    launch_chromium,
    resolve_chromium,
    run_setup_command,
)
from tests.support.constants import (
    REPO_ROOT,
    TEST_ADMIN_PASSWORD,
    TEST_SECRET_KEY,
)
from tests.support.import_flow import login_as_italo  # noqa: F401  (re-exported)
from tests.support.server import run_test_server

TEST_DB_PATH = REPO_ROOT / "data" / "test_visual.db"
TEST_PORT = 8768
TEST_BASE_URL = f"http://127.0.0.1:{TEST_PORT}"

BASELINE_DIR = Path(__file__).resolve().parent / "baselines"
RESULTS_DIR = Path(__file__).resolve().parent / "results"
DEFAULT_MAX_DIFF_RATIO = 0.005

ViewportName = Literal["desktop", "mobile"]


@dataclass(frozen=True)
class VisualViewport:
    name: ViewportName
    width: int
    height: int


VIEWPORTS: tuple[VisualViewport, ...] = (
    VisualViewport("desktop", 1440, 900),
    VisualViewport("mobile", 375, 667),
)


def _visual_env() -> dict[str, str]:
    return compose_server_env(
        TEST_DB_PATH,
        admin_password=TEST_ADMIN_PASSWORD,
        secret_key=TEST_SECRET_KEY,
        extra={"QUOTE_PROVIDER": "stub", "OMAHA_SKIP_STARTUP": "1"},
    )


def _run_setup_command(args: list[str], env: dict[str, str]) -> None:
    run_setup_command(args, repo_root=REPO_ROOT, env=env)


@pytest.fixture(scope="session")
def _browser():
    """Launch one chromium process for visual suite."""
    from playwright.sync_api import sync_playwright

    executable = resolve_chromium()
    with sync_playwright() as p:
        browser = launch_chromium(p, executable)
        try:
            yield browser
        finally:
            browser.close()


@pytest.fixture(scope="session")
def live_url_visual() -> str:
    """Start isolated visual-test server with canonical CSV-seeded DB."""
    if TEST_DB_PATH.exists():
        TEST_DB_PATH.unlink()

    env = _visual_env()
    migrate_env = {**env, "OMAHA_SKIP_STARTUP": ""}
    _run_setup_command([sys.executable, "-m", "alembic", "upgrade", "head"], migrate_env)
    _run_setup_command([sys.executable, "-m", "omaha.seed"], migrate_env)
    _run_setup_command([sys.executable, "-m", "scripts.reset_both_profiles"], migrate_env)

    with run_test_server(
        TEST_DB_PATH,
        TEST_PORT,
        label="visual-live-url",
        secret_key=TEST_SECRET_KEY,
        admin_password=TEST_ADMIN_PASSWORD,
        extra_env={"QUOTE_PROVIDER": "stub", "OMAHA_SKIP_STARTUP": "1"},
    ) as url:
        yield url


@pytest.fixture(params=VIEWPORTS, ids=[v.name for v in VIEWPORTS])
def visual_viewport(request: pytest.FixtureRequest) -> VisualViewport:
    return request.param


@pytest.fixture()
def visual_page(_browser, visual_viewport: VisualViewport):
    context = _browser.new_context(
        viewport={"width": visual_viewport.width, "height": visual_viewport.height},
        reduced_motion="reduce",
    )
    page = context.new_page()
    try:
        yield page
    finally:
        context.close()


def assert_structural_content(page, *selectors: str, text: str | None = None) -> None:
    for selector in selectors:
        page.wait_for_selector(selector, state="visible", timeout=10_000)
    if text is not None:
        assert text in page.locator("main").inner_text()


def snapshot_name(page_state: str, viewport: VisualViewport) -> str:
    return f"{page_state}-{viewport.name}.png"


def compare_or_update_screenshot(
    page,
    page_state: str,
    viewport: VisualViewport,
    *,
    max_diff_ratio: float = DEFAULT_MAX_DIFF_RATIO,
) -> None:
    BASELINE_DIR.mkdir(parents=True, exist_ok=True)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    name = snapshot_name(page_state, viewport)
    baseline_path = BASELINE_DIR / name
    actual_path = RESULTS_DIR / name

    page.screenshot(path=str(actual_path), full_page=True, animations="disabled")

    update = os.environ.get("UPDATE_VISUAL_BASELINES") == "1"
    if update or not baseline_path.exists():
        if not update and not baseline_path.exists():
            raise AssertionError(
                f"missing visual baseline {baseline_path}; rerun with UPDATE_VISUAL_BASELINES=1"
            )
        baseline_path.write_bytes(actual_path.read_bytes())
        return

    expected = baseline_path.read_bytes()
    actual = actual_path.read_bytes()
    if expected == actual:
        return

    changed, total = _png_pixel_diff(expected, actual)
    ratio = changed / total if total else 0.0
    assert ratio <= max_diff_ratio, (
        f"{name} visual diff {ratio:.4%} exceeds {max_diff_ratio:.2%} ({changed}/{total} pixels)"
    )


def _png_pixel_diff(expected: bytes, actual: bytes) -> tuple[int, int]:
    """Return changed-pixel count for two same-size 8-bit RGB/RGBA PNGs.

    Assumes helper already handled exact-byte match short-circuit and both
    inputs use standard browser screenshot encoding: deflate-compressed,
    non-interlaced PNG with RGB or RGBA scanlines.
    """

    exp_w, exp_h, exp_pixels = _decode_png_rgba(expected)
    act_w, act_h, act_pixels = _decode_png_rgba(actual)
    assert (act_w, act_h) == (exp_w, exp_h), (
        f"screenshot size changed: expected {exp_w}x{exp_h}, got {act_w}x{act_h}"
    )
    changed = sum(
        exp_pixels[i : i + 4] != act_pixels[i : i + 4] for i in range(0, len(exp_pixels), 4)
    )
    return changed, exp_w * exp_h


def _decode_png_rgba(data: bytes) -> tuple[int, int, bytes]:
    """Decode browser screenshot PNG into RGBA bytes.

    Supported input: PNG signature, IHDR bit depth 8, color type RGB/RGBA,
    deflate compression, standard PNG filters, no Adam7 interlace, at least
    one IDAT chunk.
    """

    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise AssertionError("not a PNG")

    pos = 8
    width = height = bit_depth = color_type = None
    compressed = bytearray()
    while pos < len(data):
        length = unpack(">I", data[pos : pos + 4])[0]
        chunk_type = data[pos + 4 : pos + 8]
        chunk_data = data[pos + 8 : pos + 8 + length]
        pos += 12 + length
        if chunk_type == b"IHDR":
            assert len(chunk_data) == 13, "invalid PNG IHDR length"
            width, height, bit_depth, color_type, compression, flt, interlace = unpack(
                ">IIBBBBB", chunk_data
            )
            assert bit_depth == 8 and color_type in (2, 6), "only 8-bit RGB/RGBA PNG supported"
            assert compression == 0 and flt == 0 and interlace == 0, "unsupported PNG encoding"
        elif chunk_type == b"IDAT":
            compressed.extend(chunk_data)
        elif chunk_type == b"IEND":
            break

    assert width is not None and height is not None and bit_depth is not None
    assert compressed, "PNG missing IDAT chunk"
    raw = zlib.decompress(bytes(compressed))
    channels = 4 if color_type == 6 else 3
    stride = width * channels
    expected_raw_len = height * (stride + 1)
    assert len(raw) == expected_raw_len, "unexpected PNG scanline length"
    out = bytearray()
    prev = bytearray(stride)
    offset = 0
    for _row in range(height):
        filter_type = raw[offset]
        offset += 1
        scanline = bytearray(raw[offset : offset + stride])
        offset += stride
        recon = _unfilter_scanline(scanline, prev, channels, filter_type)
        if channels == 3:
            for i in range(0, len(recon), 3):
                out.extend((recon[i], recon[i + 1], recon[i + 2], 255))
        else:
            out.extend(recon)
        prev = recon
    return width, height, bytes(out)


def _unfilter_scanline(row: bytearray, prev: bytearray, bpp: int, filter_type: int) -> bytearray:
    recon = bytearray(row)
    for i, value in enumerate(row):
        left = recon[i - bpp] if i >= bpp else 0
        up = prev[i]
        up_left = prev[i - bpp] if i >= bpp else 0
        if filter_type == 0:
            recon[i] = value
        elif filter_type == 1:
            recon[i] = (value + left) & 0xFF
        elif filter_type == 2:
            recon[i] = (value + up) & 0xFF
        elif filter_type == 3:
            recon[i] = (value + ((left + up) // 2)) & 0xFF
        elif filter_type == 4:
            recon[i] = (value + _paeth(left, up, up_left)) & 0xFF
        else:
            raise AssertionError(f"unsupported PNG filter {filter_type}")
    return recon


def _paeth(left: int, up: int, up_left: int) -> int:
    p = left + up - up_left
    pa = abs(p - left)
    pb = abs(p - up)
    pc = abs(p - up_left)
    if pa <= pb and pa <= pc:
        return left
    if pb <= pc:
        return up
    return up_left
