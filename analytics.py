"""
analytics.py — lightweight SQLite-based usage tracking for the ICT JobSpy app.

Events are stored in analytics.db (same folder as app.py).
On Streamlit Cloud the filesystem resets on each restart, so data is
session-scoped unless you swap DB_PATH for a persistent store later
(e.g., st.connection with PostgreSQL / Supabase).
"""

import sqlite3
import os
import pandas as pd
from datetime import datetime, timezone

DB_PATH = os.path.join(os.path.dirname(__file__), "analytics.db")


# ──────────────────────────── DB helpers ─────────────────────────────────────

def _get_conn() -> sqlite3.Connection:
    return sqlite3.connect(DB_PATH, check_same_thread=False)


def init_db() -> None:
    """Create tables if they don't already exist."""
    conn = _get_conn()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp      TEXT    NOT NULL,
            session_id     TEXT    NOT NULL,
            action         TEXT    NOT NULL,
            search_term    TEXT,
            location       TEXT,
            sites          TEXT,
            results_count  INTEGER,
            extra          TEXT
        )
    """)
    conn.commit()
    conn.close()


# ──────────────────────────── Write ──────────────────────────────────────────

def log_event(
    session_id: str,
    action: str,
    search_term: str = "",
    location: str = "",
    sites: str = "",
    results_count: int = 0,
    extra: str = "",
) -> None:
    """
    Log a single analytics event.

    action values used in the app:
      - "page_view"       – once per browser session on first load
      - "job_search"      – when the job scrape form is submitted
      - "profile_search"  – when the LinkedIn profile search runs
    """
    init_db()
    conn = _get_conn()
    conn.execute(
        "INSERT INTO events "
        "(timestamp, session_id, action, search_term, location, sites, results_count, extra) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (
            datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S"),
            session_id,
            action,
            search_term or "",
            location or "",
            sites or "",
            results_count or 0,
            extra or "",
        ),
    )
    conn.commit()
    conn.close()


# ──────────────────────────── Read ───────────────────────────────────────────

def get_events_df() -> pd.DataFrame:
    """Return all events as a DataFrame (newest first)."""
    init_db()
    try:
        conn = _get_conn()
        df = pd.read_sql_query(
            "SELECT * FROM events ORDER BY timestamp DESC", conn
        )
        conn.close()
        return df
    except Exception:
        return pd.DataFrame(
            columns=[
                "id", "timestamp", "session_id", "action",
                "search_term", "location", "sites", "results_count", "extra",
            ]
        )


def get_summary_stats() -> dict:
    """Return high-level KPIs."""
    df = get_events_df()
    if df.empty:
        return {
            "total_events": 0,
            "unique_sessions": 0,
            "job_searches": 0,
            "profile_searches": 0,
            "page_views": 0,
        }
    return {
        "total_events": len(df),
        "unique_sessions": int(df["session_id"].nunique()),
        "job_searches": int((df["action"] == "job_search").sum()),
        "profile_searches": int((df["action"] == "profile_search").sum()),
        "page_views": int((df["action"] == "page_view").sum()),
    }

