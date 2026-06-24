"""Shared test fixtures for RelayOS."""
from __future__ import annotations

import json
import sqlite3
import uuid
from pathlib import Path
from typing import Any, Optional

import pytest


# ── Fixtures for in-memory SQLite stores ──────────────────────


class MemoryDB:
    """An in-memory SQLite wrapper for testing store classes.

    Replaces the filesystem-backed stores used in production.
    Call connect() to get a connection, then use it in place of
    the store's own connection.
    """

    def __init__(self):
        self._conn = sqlite3.connect(":memory:")
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA journal_mode=WAL")

    @property
    def conn(self) -> sqlite3.Connection:
        return self._conn

    def close(self):
        self._conn.close()


@pytest.fixture
def memory_db():
    """Provide a temporary in-memory database."""
    db = MemoryDB()
    yield db
    db.close()


# ── Fixtures for pure-function modules (no mocking needed) ────


@pytest.fixture
def sample_capability_scores() -> dict:
    """Sample capability data for scheduler tests."""
    return {
        "claude-sonnet-4-20250514": {
            "coding": 9, "architecture": 10, "review": 8, "research": 7,
            "reasoning": 10, "quick": 5, "writing": 8,
        },
        "gpt-4o": {
            "coding": 9, "architecture": 8, "review": 7, "research": 7,
            "reasoning": 8, "quick": 6, "writing": 9,
        },
    }


@pytest.fixture
def sample_task_patterns() -> dict:
    """Sample task decomposition patterns for planner tests."""
    return {
        "coding": [
            {"id": "req", "description": "Requirements analysis", "terminal": "architect",
             "prompt_template": "Analyze requirements: {task}", "provider": "anthropic",
             "model": "claude-sonnet-4-20250514"},
        ],
    }


@pytest.fixture
def temp_dir(tmpdir) -> Path:
    """Temporary directory for config file tests."""
    return Path(tmpdir)
