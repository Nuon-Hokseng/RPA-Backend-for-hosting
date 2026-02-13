"""
Centralized Browser Launcher
=============================
Supports **all** Playwright browsers: chromium (Chrome), firefox, webkit.
Defaults to **headful** mode so users can see everything.
Uses the real Chrome channel by default (instead of raw Chromium).

When Chromium is selected the launcher will try `channel="chrome"` first,
and silently fall back to plain Chromium if Chrome is not installed.

Usage (sync):
    from browser.launcher import launch_persistent, get_page, BrowserType

    with sync_playwright() as p:
        context = launch_persistent(p, "profile_dir", browser_type="firefox")
        page = get_page(context)
        ...

Usage (async):
    from browser.launcher import launch_persistent_async, get_page_async

    async with async_playwright() as p:
        context = await launch_persistent_async(p, "profile_dir")
        page = await get_page_async(context)
        ...
"""

from __future__ import annotations
from typing import Literal


# ── Public types & defaults ──────────────────────────────────────────

BrowserType = Literal["chromium", "firefox", "webkit"]

SUPPORTED_BROWSERS: list[BrowserType] = ["chromium", "firefox", "webkit"]
DEFAULT_BROWSER: BrowserType = "chromium"
DEFAULT_HEADLESS: bool = False          # headful so the user can watch
DEFAULT_CHANNEL: str = "chrome"         # real Chrome instead of raw Chromium


# ── Internal helpers ─────────────────────────────────────────────────

def _engine(playwright, browser_type: BrowserType):
    """Return the browser-engine object from a playwright instance."""
    engines = {
        "chromium": playwright.chromium,
        "firefox": playwright.firefox,
        "webkit":  playwright.webkit,
    }
    engine = engines.get(browser_type)
    if engine is None:
        raise ValueError(
            f"Unsupported browser_type={browser_type!r}. "
            f"Choose from: {', '.join(SUPPORTED_BROWSERS)}"
        )
    return engine


def _build_opts(
    browser_type: BrowserType,
    headless: bool,
    extra: dict,
) -> dict:
    """Build the kwargs dict for launch / launch_persistent_context."""
    opts: dict = {"headless": headless, **extra}
    # Only Chromium supports the `channel` option
    if browser_type == "chromium":
        opts.setdefault("channel", DEFAULT_CHANNEL)
    return opts


# ── Sync API ─────────────────────────────────────────────────────────

def launch_persistent(
    playwright,
    user_data_dir: str,
    browser_type: BrowserType = DEFAULT_BROWSER,
    headless: bool = DEFAULT_HEADLESS,
    **extra,
):
    """Launch a **persistent** browser context (sync).

    Persistent contexts keep cookies / local-storage between runs.
    Works with all three engines.
    """
    engine = _engine(playwright, browser_type)
    opts = _build_opts(browser_type, headless, extra)

    try:
        return engine.launch_persistent_context(user_data_dir, **opts)
    except Exception:
        # Chrome channel not installed → fall back to plain Chromium
        if "channel" in opts:
            opts.pop("channel")
            return engine.launch_persistent_context(user_data_dir, **opts)
        raise


def launch_browser(
    playwright,
    browser_type: BrowserType = DEFAULT_BROWSER,
    headless: bool = DEFAULT_HEADLESS,
    **extra,
):
    """Launch a non-persistent browser (sync)."""
    engine = _engine(playwright, browser_type)
    opts = _build_opts(browser_type, headless, extra)

    try:
        return engine.launch(**opts)
    except Exception:
        if "channel" in opts:
            opts.pop("channel")
            return engine.launch(**opts)
        raise


def get_page(context):
    """Return the first page of a context, or create one (sync)."""
    return context.pages[0] if context.pages else context.new_page()


# ── Async API ────────────────────────────────────────────────────────

async def launch_persistent_async(
    playwright,
    user_data_dir: str,
    browser_type: BrowserType = DEFAULT_BROWSER,
    headless: bool = DEFAULT_HEADLESS,
    **extra,
):
    """Launch a **persistent** browser context (async)."""
    engine = _engine(playwright, browser_type)
    opts = _build_opts(browser_type, headless, extra)

    try:
        return await engine.launch_persistent_context(user_data_dir, **opts)
    except Exception:
        if "channel" in opts:
            opts.pop("channel")
            return await engine.launch_persistent_context(user_data_dir, **opts)
        raise


async def launch_browser_async(
    playwright,
    browser_type: BrowserType = DEFAULT_BROWSER,
    headless: bool = DEFAULT_HEADLESS,
    **extra,
):
    """Launch a non-persistent browser (async)."""
    engine = _engine(playwright, browser_type)
    opts = _build_opts(browser_type, headless, extra)

    try:
        return await engine.launch(**opts)
    except Exception:
        if "channel" in opts:
            opts.pop("channel")
            return await engine.launch(**opts)
        raise


async def get_page_async(context):
    """Return the first page of a context, or create one (async)."""
    return context.pages[0] if context.pages else await context.new_page()


# ── Cookie-based launch (no persistent profile needed) ───────────────

_DEFAULT_VIEWPORT = {"width": 1280, "height": 720}


def launch_with_cookies(
    playwright,
    cookies: list[dict],
    browser_type: BrowserType = DEFAULT_BROWSER,
    headless: bool = DEFAULT_HEADLESS,
    goto_url: str = "https://www.instagram.com/",
    **extra,
):
    """
    Launch a **non-persistent** browser, inject *cookies*, navigate to
    Instagram and return ``(browser, context, page)`` (sync).

    The caller MUST close ``context`` and ``browser`` when done.
    """
    browser = launch_browser(playwright, browser_type=browser_type, headless=headless, **extra)
    context = browser.new_context(viewport=_DEFAULT_VIEWPORT)
    context.add_cookies(cookies)
    page = context.new_page()
    page.goto(goto_url)
    return browser, context, page


async def launch_with_cookies_async(
    playwright,
    cookies: list[dict],
    browser_type: BrowserType = DEFAULT_BROWSER,
    headless: bool = DEFAULT_HEADLESS,
    goto_url: str = "https://www.instagram.com/",
    **extra,
):
    """
    Async version of :func:`launch_with_cookies`.
    Returns ``(browser, context, page)``.
    """
    browser = await launch_browser_async(playwright, browser_type=browser_type, headless=headless, **extra)
    context = await browser.new_context(viewport=_DEFAULT_VIEWPORT)
    await context.add_cookies(cookies)
    page = await context.new_page()
    await page.goto(goto_url)
    return browser, context, page
