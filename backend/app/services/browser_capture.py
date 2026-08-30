"""Headless browser screenshots for live app URLs and HTML deliverables."""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


async def screenshot_url(url: str, *, wait_ms: int = 2500) -> bytes | None:
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        logger.debug("Playwright not installed — skipping URL screenshot")
        return None

    try:
        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(headless=True)
            try:
                page = await browser.new_page(viewport={"width": 1280, "height": 800})
                await page.goto(url, wait_until="domcontentloaded", timeout=45000)
                await page.wait_for_timeout(wait_ms)
                return await page.screenshot(full_page=True, type="png")
            finally:
                await browser.close()
    except Exception as exc:
        logger.info("URL screenshot failed for %s: %s", url, exc)
        return None


async def screenshot_html(html: str, *, base_url: str | None = None) -> bytes | None:
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        return None

    try:
        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(headless=True)
            try:
                page = await browser.new_page(viewport={"width": 1280, "height": 800})
                if base_url:
                    await page.goto(base_url, wait_until="domcontentloaded", timeout=15000)
                await page.set_content(html, wait_until="domcontentloaded")
                await page.wait_for_timeout(1500)
                return await page.screenshot(full_page=True, type="png")
            finally:
                await browser.close()
    except Exception as exc:
        logger.info("HTML screenshot failed: %s", exc)
        return None
