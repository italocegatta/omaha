"""F64 browser discovery and 16px/32px favicon raster evidence."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from playwright.sync_api import Page

from .test_user_journey import _login_and_select_italo


def _favicon_raster(page: Page, size: int) -> dict[str, Any]:
    return page.evaluate(
        """
        async (size) => {
          const response = await fetch('/static/favicon.svg', {cache: 'no-store'});
          const svg = await response.text();
          const blob = new Blob([svg], {type: 'image/svg+xml'});
          const image = new Image();
          const objectUrl = URL.createObjectURL(blob);
          try {
            await new Promise((resolve, reject) => {
              image.onload = resolve;
              image.onerror = reject;
              image.src = objectUrl;
            });
            const canvas = document.createElement('canvas');
            canvas.width = size;
            canvas.height = size;
            const context = canvas.getContext('2d');
            if (!context) throw new Error('2D canvas unavailable');
            context.drawImage(image, 0, 0, size, size);
            const pixels = context.getImageData(0, 0, size, size).data;
            let tealPixels = 0;
            let darkPixels = 0;
            let minX = size;
            let minY = size;
            let maxX = -1;
            let maxY = -1;
            for (let y = 0; y < size; y += 1) {
              for (let x = 0; x < size; x += 1) {
                const offset = (y * size + x) * 4;
                const [red, green, blue, alpha] = pixels.slice(offset, offset + 4);
                if (alpha > 240 && red >= 90 && green >= 150 && blue >= 140) {
                  tealPixels += 1;
                  minX = Math.min(minX, x);
                  minY = Math.min(minY, y);
                  maxX = Math.max(maxX, x);
                  maxY = Math.max(maxY, y);
                }
                if (
                  alpha > 240 &&
                  red >= 35 && red <= 55 &&
                  green >= 35 && green <= 65 &&
                  blue >= 45 && blue <= 75
                ) {
                  darkPixels += 1;
                }
              }
            }
            return {
              status: response.status,
              contentType: response.headers.get('content-type'),
              background: Array.from(pixels.slice(0, 4)),
              tealPixels,
              darkPixels,
              bounds: [minX, minY, maxX, maxY],
            };
          } finally {
            URL.revokeObjectURL(objectUrl);
          }
        }
        """,
        size,
    )


def test_shared_head_discovers_favicon(page: Page, live_url: str) -> None:
    page.goto(f"{live_url}/login", wait_until="commit", timeout=60000)
    icon = page.locator('head link[rel="icon"]')
    assert icon.count() == 1
    assert icon.get_attribute("type") == "image/svg+xml"
    assert icon.get_attribute("href") == "/static/favicon.svg"

    for size in (16, 32):
        raster = _favicon_raster(page, size)
        assert raster["status"] == 200
        assert raster["contentType"].split(";", 1)[0] == "image/svg+xml"
        assert raster["background"][:3] == [48, 52, 70]
        assert raster["tealPixels"] > 0
        assert raster["darkPixels"] > 0
        min_x, min_y, max_x, max_y = raster["bounds"]
        assert 0 <= min_x < max_x < size
        assert 0 <= min_y < max_y < size
        print(f"F64 favicon {size}px: {raster}")

    _login_and_select_italo(page, live_url)
    app_icon = page.locator('head link[rel="icon"]')
    assert app_icon.count() == 1
    assert app_icon.get_attribute("href") == "/static/favicon.svg"
