"""
Account & Session Router
========================
Manages Instagram browser sessions (login/save).
"""

import asyncio
from fastapi import APIRouter, BackgroundTasks
from api.shared.models import (
    SessionRequest, TaskResponse,
    create_task, update_task, make_log_fn, TaskStatus,
)

router = APIRouter(prefix="/session", tags=["Account & Session"])


async def _save_session_worker(task_id: str, account_path: str, timeout: int):
    """Background worker – opens a browser for manual login and saves the session."""
    log = make_log_fn(task_id)
    update_task(task_id, status=TaskStatus.RUNNING)
    log(f"Launching browser at profile '{account_path}' – you have {timeout}s to login")

    try:
        from playwright.async_api import async_playwright

        async with async_playwright() as p:
            context = await p.chromium.launch_persistent_context(
                account_path,
                headless=False,
                slow_mo=500,
            )
            page = context.pages[0] if context.pages else await context.new_page()
            await page.goto("https://www.instagram.com/accounts/login/")
            log("Instagram login page opened – waiting for manual login…")

            await asyncio.sleep(timeout)
            await context.close()

        log(f"Session saved to '{account_path}'!")
        update_task(task_id, status=TaskStatus.COMPLETED, message="Session saved successfully")

    except Exception as e:
        log(f"Error: {e}")
        update_task(task_id, status=TaskStatus.FAILED, message=str(e))


@router.post("/save", response_model=TaskResponse)
async def save_session(req: SessionRequest, bg: BackgroundTasks):
    """
    Open a headed browser pointed at the Instagram login page.
    The user logs in manually within the timeout window.
    Session cookies are persisted to `account_path` for later reuse.
    """
    task = create_task(f"Save session → {req.account_path}")
    bg.add_task(_save_session_worker, task.task_id, req.account_path, req.timeout)
    return TaskResponse(
        task_id=task.task_id,
        status="accepted",
        message=f"Session save started. Check /tasks/{task.task_id} for progress.",
    )


@router.get("/check")
async def check_session(account_path: str = "instagram_session"):
    """Check whether a saved session directory exists."""
    import os
    exists = os.path.isdir(account_path)
    return {
        "account_path": account_path,
        "session_exists": exists,
        "message": "Session found – ready to use" if exists else "No session found – call POST /session/save first",
    }
