"""
Browser session helpers
=======================
Open a headed browser for Instagram login, export cookies, and
optionally restore a session from stored cookies.
"""

import asyncio
import tempfile
import shutil
from playwright.async_api import async_playwright
from browser.launcher import (
    launch_persistent_async,
    launch_browser_async,
    launch_with_cookies_async,
    get_page_async,
    BrowserType,
    DEFAULT_BROWSER,
    DEFAULT_HEADLESS,
)


async def open_login_and_export_cookies(
    timeout: int = 120,
    browser_type: BrowserType = DEFAULT_BROWSER,
) -> list[dict]:
    """
    Open a **headful** browser, navigate to Instagram login, wait for the
    user to log in, then export and return all cookies.

    The browser closes **immediately** once a successful login is detected.
    Detection uses two signals (whichever fires first):
      1. A ``ds_user`` cookie appears (Instagram sets it on login)
      2. The page URL navigates away from the login page

    If neither signal fires within ``timeout`` seconds, the browser closes
    anyway and returns whatever cookies exist.
    """
    tmp_dir = tempfile.mkdtemp(prefix="ig_login_")
    try:
        async with async_playwright() as p:
            context = await launch_persistent_async(
                p,
                tmp_dir,
                browser_type=browser_type,
                headless=False,          # always visible for manual login
                slow_mo=500,
            )
            page = await get_page_async(context)
            await page.goto("https://www.instagram.com/accounts/login/")

            # Poll for successful login — two detection methods
            logged_in = False
            elapsed = 0
            poll_interval = 1  # check every second for fast response

            while elapsed < timeout:
                # Method 1: check cookies across all IG domains
                all_cookies = await context.cookies([
                    "https://www.instagram.com",
                    "https://instagram.com",
                    "https://i.instagram.com",
                ])
                if any(c.get("name") == "ds_user" for c in all_cookies):
                    logged_in = True
                    break

                # Method 2: URL navigated away from login page
                current_url = page.url
                if (
                    "instagram.com" in current_url
                    and "/accounts/login" not in current_url
                    and "/challenge" not in current_url  # skip 2FA challenge page
                ):
                    # Give it a moment for cookies to finalize
                    await asyncio.sleep(2)
                    logged_in = True
                    break

                await asyncio.sleep(poll_interval)
                elapsed += poll_interval

            # Export all cookies before closing
            cookies = await context.cookies([
                "https://www.instagram.com",
                "https://instagram.com",
                "https://i.instagram.com",
            ])
            await context.close()
    finally:
        # Clean up temp profile directory
        shutil.rmtree(tmp_dir, ignore_errors=True)

    return cookies


class CookieBrowser:
    """
    Context manager for a browser session restored from stored cookies.
    Handles cleanup of Playwright, Browser, Context on exit.

    Usage::

        async with CookieBrowser(cookies) as cb:
            await cb.page.goto("https://www.instagram.com/explore/")
    """

    def __init__(
        self,
        cookies: list[dict],
        browser_type: BrowserType = DEFAULT_BROWSER,
        headless: bool = DEFAULT_HEADLESS,
        goto_url: str = "https://www.instagram.com/",
    ):
        self.cookies = cookies
        self.browser_type = browser_type
        self.headless = headless
        self.goto_url = goto_url
        self._pw = None
        self._browser = None
        self.context = None
        self.page = None

    async def __aenter__(self):
        from playwright.async_api import async_playwright as _ap

        self._pw = await _ap().start()
        self._browser = await launch_browser_async(
            self._pw,
            browser_type=self.browser_type,
            headless=self.headless,
        )
        self.context = await self._browser.new_context(
            viewport={"width": 1280, "height": 720},
        )
        await self.context.add_cookies(self.cookies)
        self.page = await self.context.new_page()
        await self.page.goto(self.goto_url)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.context:
            await self.context.close()
        if self._browser:
            await self._browser.close()
        if self._pw:
            await self._pw.stop()
        return False


async def open_browser_with_cookies(
    cookies: list[dict],
    browser_type: BrowserType = DEFAULT_BROWSER,
    headless: bool = DEFAULT_HEADLESS,
    goto_url: str = "https://www.instagram.com/",
):
    """
    Launch a fresh browser, inject stored cookies, then navigate to
    Instagram so the session is already authenticated.

    .. deprecated:: Use :class:`CookieBrowser` context manager instead
       to avoid resource leaks.

    Returns ``(context, page)`` — the caller is responsible for closing.
    """
    cb = CookieBrowser(cookies, browser_type, headless, goto_url)
    await cb.__aenter__()
    return cb.context, cb.page
