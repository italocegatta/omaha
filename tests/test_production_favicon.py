"""Pure source contracts for F64's production favicon."""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
FAVICON_PATH = REPO_ROOT / "src" / "omaha" / "static" / "favicon.svg"
BASE_TEMPLATE_PATH = REPO_ROOT / "src" / "omaha" / "templates" / "base.html"
FAVICON_HREF = "/static/favicon.svg"
BACKGROUND = "#303446"
ACCENT = "#81c8be"


def _relative_luminance(hex_color: str) -> float:
    channels = [int(hex_color[index : index + 2], 16) / 255 for index in (1, 3, 5)]
    linear = [
        channel / 12.92 if channel <= 0.04045 else ((channel + 0.055) / 1.055) ** 2.4
        for channel in channels
    ]
    return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]


def test_favicon_svg_structure_and_palette() -> None:
    assert FAVICON_PATH.is_file()
    source = FAVICON_PATH.read_text(encoding="utf-8")
    root = ET.fromstring(source)

    assert root.tag == "{http://www.w3.org/2000/svg}svg"
    assert root.attrib["viewBox"] == "0 0 32 32"
    assert root.attrib["width"] == "32"
    assert root.attrib["height"] == "32"
    assert [child.tag.rsplit("}", 1)[-1] for child in root] == ["rect", "path"]

    rect, mark = root
    assert rect.attrib == {"width": "32", "height": "32", "fill": BACKGROUND}
    assert mark.attrib["fill"] == ACCENT
    assert mark.attrib["fill-rule"] == "evenodd"
    assert "stroke" not in mark.attrib
    assert re.fullmatch(r"[A-Za-z0-9.\- ]+", mark.attrib["d"])
    assert all(
        float(number).is_integer() for number in re.findall(r"\d+(?:\.\d+)?", mark.attrib["d"])
    )

    forbidden = re.compile(
        r"<text\b|<title\b|<desc\b|<animate\b|<script\b|gradient|emoji|"
        r"url\(|@import|<use\b|(?:xlink:)?href\s*=",
        re.IGNORECASE,
    )
    assert forbidden.search(source) is None

    background_luminance = _relative_luminance(BACKGROUND)
    accent_luminance = _relative_luminance(ACCENT)
    contrast = (max(background_luminance, accent_luminance) + 0.05) / (
        min(background_luminance, accent_luminance) + 0.05
    )
    assert contrast >= 4.5


def test_base_head_has_single_favicon_link() -> None:
    source = BASE_TEMPLATE_PATH.read_text(encoding="utf-8")
    expected = '<link rel="icon" type="image/svg+xml" href="/static/favicon.svg">'

    assert source.count(expected) == 1
    assert source.count('rel="icon"') == 1
    assert source.count(FAVICON_HREF) == 1


def test_base_extenders_do_not_add_favicon_candidates() -> None:
    template_dir = REPO_ROOT / "src" / "omaha" / "templates"
    for template_path in template_dir.rglob("*.html"):
        if template_path == BASE_TEMPLATE_PATH:
            continue
        source = template_path.read_text(encoding="utf-8")
        assert 'rel="icon"' not in source, template_path.relative_to(REPO_ROOT)
