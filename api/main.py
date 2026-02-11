"""
FastAPI RPA – Instagram Automation API
======================================
Main application entry point.
Run with:  uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
"""

import sys
import os

# Ensure the project root is on sys.path so all existing modules resolve
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routers import session, brain, scraper, scrolling, search
from api.shared.models import (
    get_task, list_all_tasks, stop_task,
    TaskStatus, TaskInfo, TaskResponse,
)

app = FastAPI(
    title="Instagram RPA Automation API",
    description=(
        "Production-ready REST API wrapping Playwright-based Instagram automation. "
        "Organised into five modules: **Session**, **Brain (Analysis)**, **Scraper**, "
        "**Scrolling Automation**, and **Search & Explore**."
    ),
    version="1.0.0",
)

# CORS – allow all in dev; tighten for production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Register Routers ────────────────────────────────────────────────
app.include_router(session.router)
app.include_router(brain.router)
app.include_router(scraper.router)
app.include_router(scrolling.router)
app.include_router(search.router)


# ── Global Task Endpoints ──────────────────────────────────────────
@app.get("/", tags=["Health"])
async def health_check():
    """Health-check / root endpoint."""
    return {"status": "ok", "service": "Instagram RPA API"}


@app.get("/tasks", response_model=list[TaskInfo], tags=["Tasks"])
async def get_all_tasks():
    """List every background task and its current status."""
    return list_all_tasks()


@app.get("/tasks/{task_id}", response_model=TaskInfo, tags=["Tasks"])
async def get_task_status(task_id: str):
    """Get the status, logs and result of a specific task."""
    task = get_task(task_id)
    if not task:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@app.post("/tasks/{task_id}/stop", response_model=TaskResponse, tags=["Tasks"])
async def stop_running_task(task_id: str):
    """Send a stop signal to a running background task."""
    task = get_task(task_id)
    if not task:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Task not found")
    stop_task(task_id)
    return TaskResponse(task_id=task_id, status="stopping", message="Stop signal sent")
