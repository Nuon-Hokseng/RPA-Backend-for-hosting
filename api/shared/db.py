"""Supabase client helpers for cookie storage."""

from __future__ import annotations

import os
import json
from typing import Any
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

_client: Client | None = None


def get_supabase() -> Client:
    """Return a singleton Supabase client."""
    global _client
    if _client is None:
        url = os.getenv("URL")
        key = os.getenv("ANNON")
        if not url or not key:
            raise RuntimeError("URL and ANNON must be set in .env")
        _client = create_client(url, key)
    return _client


# ── Cookie CRUD ─────────────────────────────────────────────────────

def insert_user_cookies(user_id: int, cookies: list[dict]) -> dict:
    """
    Insert a new cookie snapshot for a user.
    One user can have multiple cookie rows at the same time.
    Returns the inserted row.
    """
    sb = get_supabase()
    result = (
        sb.table("user_cookies")
        .insert({"user_id": user_id, "cookies": cookies})
        .execute()
    )
    return result.data[0] if result.data else {}


def fetch_all_user_cookies(user_id: int) -> list[dict]:
    """
    Fetch ALL cookie snapshots for a user (newest first).
    One account can have multiple cookies at the same time.
    """
    sb = get_supabase()
    result = (
        sb.table("user_cookies")
        .select("*")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .execute()
    )
    return result.data


def fetch_latest_user_cookies(user_id: int) -> dict | None:
    """Fetch only the most recent cookie snapshot for a user."""
    sb = get_supabase()
    result = (
        sb.table("user_cookies")
        .select("*")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )
    return result.data[0] if result.data else None


def delete_user_cookies(cookie_id: int) -> bool:
    """Delete a specific cookie row by its id."""
    sb = get_supabase()
    result = (
        sb.table("user_cookies")
        .delete()
        .eq("id", cookie_id)
        .execute()
    )
    return bool(result.data)
