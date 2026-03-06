"""
conftest.py — shared pytest fixtures available to all test modules.
"""

import os
import sys

import pytest

# ── Ensure the project root is on sys.path so `from app.xxx import ...` works
sys.path.insert(0, os.path.dirname(__file__))


@pytest.fixture(autouse=False)
def no_real_db(monkeypatch):
    """
    Convenience fixture: prevents any accidental psycopg2.connect() call
    from reaching a real database during unit tests.

    Apply to a test with:  @pytest.mark.usefixtures("no_real_db")
    """
    import psycopg2

    def _blocked(*args, **kwargs):
        raise RuntimeError(
            "This test tried to open a real DB connection. "
            "Use a mock instead, or use the db_conn fixture from test_db_connection.py."
        )

    monkeypatch.setattr(psycopg2, "connect", _blocked)
