"""
Database connectivity — psycopg2 ThreadedConnectionPool.

Uses a connection pool so that individual HTTP requests do NOT open a
brand-new TCP connection to PostgreSQL every time.  This keeps the
total connection count low and avoids the "could not fork new process /
Bad file descriptor" error that occurs when PostgreSQL runs out of
available backend slots.

Pool sizing (env-configurable):
  DB_POOL_MIN  – minimum connections kept open (default 1)
  DB_POOL_MAX  – maximum connections in the pool (default 10)
"""

import logging
import threading
import time

import psycopg2
from psycopg2 import pool as pg_pool
from psycopg2.extras import RealDictCursor
from fastapi import HTTPException

from app.core.config import settings

logger = logging.getLogger(__name__)

# ── Pool singleton ────────────────────────────────────────────────────────────
_pool: pg_pool.ThreadedConnectionPool | None = None
_pool_lock = threading.Lock()

# Pool size limits
_POOL_MIN = int(getattr(settings, "DB_POOL_MIN", 1))
_POOL_MAX = int(getattr(settings, "DB_POOL_MAX", 10))


def _build_dsn() -> dict:
    return dict(
        host=settings.DB_HOST,
        database=settings.DB_NAME,
        user=settings.DB_USER,
        password=settings.DB_PASSWORD,
        port=settings.DB_PORT,
        connect_timeout=10,          # don't hang forever if PG is down
        application_name="proposal_api",
    )


def get_pool() -> pg_pool.ThreadedConnectionPool:
    """Return (and lazily create) the shared connection pool."""
    global _pool
    if _pool is not None and not _pool.closed:
        return _pool

    with _pool_lock:
        # Double-checked locking
        if _pool is not None and not _pool.closed:
            return _pool
        try:
            logger.info("Creating PostgreSQL connection pool (min=%d, max=%d)…", _POOL_MIN, _POOL_MAX)
            _pool = pg_pool.ThreadedConnectionPool(_POOL_MIN, _POOL_MAX, **_build_dsn())
            logger.info("PostgreSQL pool ready.")
        except psycopg2.OperationalError as exc:
            raise RuntimeError(f"Cannot create DB pool: {exc}") from exc
    return _pool


def close_pool() -> None:
    """Gracefully close all pool connections (call on app shutdown)."""
    global _pool
    if _pool and not _pool.closed:
        _pool.closeall()
        logger.info("PostgreSQL connection pool closed.")
    _pool = None


# ── FastAPI dependency ────────────────────────────────────────────────────────

def get_db():
    """
    FastAPI dependency — yields a psycopg2 connection from the pool.

    The connection is returned to the pool (not closed) after the request
    so that the next request can reuse it immediately.

    Usage in a route:
        def my_route(db=Depends(get_db)):
            ...
    """
    conn = None
    try:
        p = get_pool()
        conn = p.getconn()
        # Roll back any stale state from a previous failed request
        conn.rollback()
        yield conn
        # Commit if the handler didn't explicitly commit/rollback
        try:
            conn.commit()
        except Exception:
            pass
    except (psycopg2.OperationalError, psycopg2.InterfaceError, RuntimeError) as exc:
        # Pool or connection is dead — recreate pool on next request
        global _pool
        logger.warning("DB connection error, resetting pool: %s", exc)
        try:
            close_pool()
        except Exception:
            pass
        raise HTTPException(
            status_code=503,
            detail=(
                f"Database connection failed: {exc}. "
                "Check your .env configuration or restart the PostgreSQL service."
            ),
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Database error: {exc}",
        ) from exc
    finally:
        if conn is not None:
            try:
                p = get_pool()
                p.putconn(conn)
            except Exception:
                # If pool is broken just close the connection
                try:
                    conn.close()
                except Exception:
                    pass
