"""
Account & Session Router
========================
Manages Instagram browser sessions (login/save).
Cookies are exported from Playwright and stored in the Supabase
`user_cookies` table so one user can have multiple cookie snapshots.
"""

import asyncio
from fastapi import APIRouter, BackgroundTasks, HTTPException
from api.shared.models import (
    SessionRequest, TaskResponse,
    create_task, update_task, make_log_fn, TaskStatus,
)
from api.shared.db import (
    insert_user_cookies,
    fetch_all_user_cookies,
    fetch_latest_user_cookies,
    delete_user_cookies,
)

router = APIRouter(prefix="/session", tags=["Account & Session"])


async def _save_session_worker(task_id: str, user_id: int, account_path: str, timeout: int):
    """Background worker – opens a browser for manual login, exports cookies to Supabase."""
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

            # ── Export cookies and store in Supabase ─────────────
            cookies = await context.cookies()
            log(f"Extracted {len(cookies)} cookies from browser")

            row = insert_user_cookies(user_id, cookies)
            cookie_row_id = row.get("id", "?")
            log(f"Cookies stored in Supabase user_cookies (row id={cookie_row_id})")

            await context.close()

        log(f"Session saved to '{account_path}' and cookies stored for user_id={user_id}!")
        update_task(
            task_id,
            status=TaskStatus.COMPLETED,
            message=f"Session saved – cookies row id={cookie_row_id}",
        )

    except Exception as e:
        log(f"Error: {e}")
        update_task(task_id, status=TaskStatus.FAILED, message=str(e))


@router.post("/save", response_model=TaskResponse)
async def save_session(req: SessionRequest, bg: BackgroundTasks):
    """
    Open a headed browser pointed at the Instagram login page.
    The user logs in manually within the timeout window.
    Cookies are exported and stored in the Supabase `user_cookies` table.
    """
    task = create_task(f"Save session → user {req.user_id} / {req.account_path}")
    bg.add_task(_save_session_worker, task.task_id, req.user_id, req.account_path, req.timeout)
    return TaskResponse(
        task_id=task.task_id,
        status="accepted",
        message=f"Session save started. Check /tasks/{task.task_id} for progress.",
    )


# ── Cookie retrieval endpoints ──────────────────────────────────────

@router.get("/cookies/{user_id}")
async def get_cookies(user_id: int, latest: bool = True):
    """
    Fetch stored cookies for a user.
    - `latest=true` (default): returns the most recent cookie snapshot.
    - `latest=false`: returns ALL cookie snapshots (one user can have many).
    """
    try:
        if latest:
            row = fetch_latest_user_cookies(user_id)
            if not row:
                raise HTTPException(status_code=404, detail="No cookies found for this user")
            return {"user_id": user_id, "cookies": row}
        else:
            rows = fetch_all_user_cookies(user_id)
            if not rows:
                raise HTTPException(status_code=404, detail="No cookies found for this user")
            return {"user_id": user_id, "count": len(rows), "cookies": rows}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/cookies/{cookie_id}")
async def remove_cookie(cookie_id: int):
    """Delete a specific cookie snapshot by its row id."""
    deleted = delete_user_cookies(cookie_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Cookie row not found")
    return {"deleted": True, "cookie_id": cookie_id}


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
