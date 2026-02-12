"""Shared Pydantic models and task manager for all API routers."""

from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum
import uuid
import asyncio
from datetime import datetime


# ── Task Management ─────────────────────────────────────────────────

class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    STOPPED = "stopped"


class TaskInfo(BaseModel):
    task_id: str
    status: TaskStatus
    created_at: str
    message: str = ""
    result: Optional[dict] = None
    logs: list[str] = []


# In-memory store for background tasks
_tasks: dict[str, TaskInfo] = {}
_stop_flags: dict[str, bool] = {}


def create_task(description: str = "") -> TaskInfo:
    task_id = str(uuid.uuid4())[:8]
    task = TaskInfo(
        task_id=task_id,
        status=TaskStatus.PENDING,
        created_at=datetime.now().isoformat(),
        message=description,
    )
    _tasks[task_id] = task
    _stop_flags[task_id] = False
    return task


def get_task(task_id: str) -> Optional[TaskInfo]:
    return _tasks.get(task_id)


def update_task(task_id: str, **kwargs):
    if task_id in _tasks:
        task = _tasks[task_id]
        for k, v in kwargs.items():
            setattr(task, k, v)


def add_task_log(task_id: str, msg: str):
    if task_id in _tasks:
        _tasks[task_id].logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")


def stop_task(task_id: str):
    _stop_flags[task_id] = True


def is_stopped(task_id: str) -> bool:
    return _stop_flags.get(task_id, False)


def list_all_tasks() -> list[TaskInfo]:
    return list(_tasks.values())


def make_log_fn(task_id: str):
    """Create a log function that appends to the task's log list."""
    def log(msg: str):
        add_task_log(task_id, msg)
    return log


def make_stop_fn(task_id: str):
    """Create a stop-flag callable for Playwright loops."""
    def should_stop() -> bool:
        return is_stopped(task_id)
    return should_stop


# ── Request / Response Models ───────────────────────────────────────

class SessionRequest(BaseModel):
    user_id: int = Field(..., description="User id from the authentication table")
    account_path: str = Field(..., description="Path to the browser profile directory")
    timeout: int = Field(120, description="Seconds to wait for manual login")


class AnalyzeAccountsRequest(BaseModel):
    users: list[dict] = Field(..., description="List of user dicts with at least a 'username' key")
    target_customer: str = Field(..., description="Target customer key, e.g. 'car', 'skincare', 'ideal'")
    model: str = Field("llama3:8b", description="Ollama model name")


class ClassifyAccountsRequest(BaseModel):
    users: list[dict] = Field(..., description="List of user dicts (username, bio, post_summary, etc.)")
    model: str = Field("llama3:8b", description="Ollama model name")


class ExportCSVRequest(BaseModel):
    results: list[dict] = Field(..., description="List of analyzed result dicts")
    target_customer: str = Field(..., description="Target customer key")
    output_dir: str = Field("output", description="Directory to save CSV files")


class ValidateCSVRequest(BaseModel):
    csv_path: str = Field(..., description="Path to the CSV file to validate")


class CreateSampleCSVRequest(BaseModel):
    output_path: str = Field(..., description="Path to save the sample CSV file")
    target_type: str = Field("hashtag", description="'hashtag' or 'username'")
    samples: Optional[list[str]] = Field(None, description="Custom sample values")


class ScrapeRequest(BaseModel):
    account_path: str = Field("instagram_session", description="Browser profile directory")
    target_customer: str = Field(..., description="Target customer key")
    headless: bool = Field(True, description="Run browser in headless mode")
    max_commenters: int = Field(15, description="Max commenters to extract per post")
    model: str = Field("llama3:8b", description="Ollama model for analysis")


class ScrollRequest(BaseModel):
    account_path: str = Field(..., description="Browser profile directory")
    duration: int = Field(60, description="Session duration in seconds")
    headless: bool = Field(True, description="Run browser in headless mode")
    infinite_mode: bool = Field(False, description="Enable infinite scroll mode with rest cycles")


class CombinedScrollRequest(BaseModel):
    account_path: str = Field(..., description="Browser profile directory")
    duration: int = Field(60, description="Session duration in seconds")
    headless: bool = Field(True, description="Run browser in headless mode")
    infinite_mode: bool = Field(False, description="Enable infinite mode with rest cycles")
    search_targets: Optional[list[str]] = Field(None, description="Targets to randomly search/explore")
    search_chance: float = Field(0.30, description="Probability of exploring a target per scroll cycle")
    profile_scroll_count_min: int = Field(3, description="Min scrolls on a profile page")
    profile_scroll_count_max: int = Field(8, description="Max scrolls on a profile page")


class ScraperScrollRequest(BaseModel):
    account_path: str = Field(..., description="Browser profile directory")
    duration: int = Field(60, description="Session duration in seconds")
    headless: bool = Field(True, description="Run browser in headless mode")
    infinite_mode: bool = Field(False, description="Enable infinite mode")
    target_customer: str = Field("car", description="Target customer key for scraper pipeline")
    scraper_chance: float = Field(0.20, description="Probability of triggering scraper per scroll")
    model: str = Field("llama3:8b", description="Ollama model name")
    search_targets: Optional[list[str]] = Field(None, description="Extra search targets")
    search_chance: float = Field(0.30, description="Probability of random explore")
    profile_scroll_count_min: int = Field(3)
    profile_scroll_count_max: int = Field(8)


class CSVProfileVisitRequest(BaseModel):
    account_path: str = Field(..., description="Browser profile directory")
    csv_path: str = Field(..., description="Path to CSV file containing targets to visit")
    headless: bool = Field(True, description="Run browser in headless mode")
    scroll_count_min: int = Field(3, description="Min scrolls per profile")
    scroll_count_max: int = Field(8, description="Max scrolls per profile")
    delay_min: int = Field(5, description="Min seconds delay between profile visits")
    delay_max: int = Field(15, description="Max seconds delay between profile visits")
    like_chance: float = Field(0.10, description="Probability of liking a post while scrolling")


class SearchRequest(BaseModel):
    account_path: str = Field(..., description="Browser profile directory")
    search_term: str = Field(..., description="The term to search for")
    search_type: str = Field("hashtag", description="'hashtag' or 'username'")
    headless: bool = Field(True, description="Run browser in headless mode")
    keep_open: bool = Field(False, description="Keep browser open after search (blocks until stopped)")


class TaskResponse(BaseModel):
    task_id: str
    status: str
    message: str


class TargetListResponse(BaseModel):
    targets: list[str]
    details: dict[str, str] = {}
