"""
Database connection smoke test.

Migrated from test_db_conn.py — now lives in tests/ where it belongs.

Run:  pytest tests/test_db_connection.py -v
      (requires a running PostgreSQL instance with .env loaded)
"""

import os
import pytest
import psycopg2
from dotenv import load_dotenv

load_dotenv()


@pytest.fixture(scope="module")
def db_conn():
    """Open a real psycopg2 connection for the duration of this module."""
    conn = psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        database=os.getenv("DB_NAME", "proposal_db"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", ""),
        port=os.getenv("DB_PORT", "5432"),
    )
    yield conn
    conn.close()


def test_connection_is_alive(db_conn):
    """The DB server should respond to a simple SELECT 1."""
    cursor = db_conn.cursor()
    cursor.execute("SELECT 1")
    result = cursor.fetchone()
    cursor.close()
    assert result == (1,)


def test_proposals_table_exists(db_conn):
    """proposals table must exist in the connected database."""
    cursor = db_conn.cursor()
    cursor.execute(
        """
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
          AND table_name = 'proposals'
        """
    )
    result = cursor.fetchone()
    cursor.close()
    assert result is not None, "Table 'proposals' does not exist"


def test_pricing_config_table_exists(db_conn):
    """pricing_config table must exist in the connected database."""
    cursor = db_conn.cursor()
    cursor.execute(
        """
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
          AND table_name = 'pricing_config'
        """
    )
    result = cursor.fetchone()
    cursor.close()
    assert result is not None, "Table 'pricing_config' does not exist"
