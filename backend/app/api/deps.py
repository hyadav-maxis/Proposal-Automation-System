"""
Shared FastAPI dependencies.

Import get_db here so every router only needs to import from one place.
"""

from app.core.database import get_db  # re-export

__all__ = ["get_db"]
