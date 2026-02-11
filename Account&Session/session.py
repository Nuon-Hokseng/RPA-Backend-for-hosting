import asyncio
from playwright.async_api import async_playwright


async def save_session(account_path, timeout=120):
    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            account_path, 
            headless=False,
            slow_mo=500
        )
        page = context.pages[0] if context.pages else await context.new_page()
        await page.goto("https://www.instagram.com/accounts/login/")

        # Wait for user to login
        await asyncio.sleep(timeout) 
        
        await context.close()
        print(f"Session saved to '{account_path}'!")
