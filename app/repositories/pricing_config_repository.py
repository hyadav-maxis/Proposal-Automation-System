"""
Pricing Config Repository — all SQL for the pricing_config table.
"""

import json
from typing import Any, Dict, Optional
from psycopg2.extras import RealDictCursor


class PricingConfigRepository:
    """Data-access object for the pricing_config table."""

    def __init__(self, db) -> None:
        self._db = db

    def get_all(self) -> Dict[str, Any]:
        """Return all config rows as {key: {value, description}}."""
        cursor = self._db.cursor(cursor_factory=RealDictCursor)
        try:
            cursor.execute("SELECT * FROM pricing_config ORDER BY config_key")
            configs: Dict[str, Any] = {}
            for row in cursor.fetchall():
                config_value = row["config_value"]
                if isinstance(config_value, str):
                    try:
                        config_value = json.loads(config_value)
                    except (json.JSONDecodeError, ValueError):
                        pass
                configs[row["config_key"]] = {
                    "value": config_value,
                    "description": row["description"],
                }
            return configs
        finally:
            cursor.close()

    def get_by_key(self, config_key: str) -> Optional[Dict[str, Any]]:
        cursor = self._db.cursor(cursor_factory=RealDictCursor)
        try:
            cursor.execute(
                "SELECT * FROM pricing_config WHERE config_key = %s",
                (config_key,),
            )
            row = cursor.fetchone()
            return dict(row) if row else None
        finally:
            cursor.close()

    def upsert(self, config_key: str, value: Any, description: str) -> None:
        cursor = self._db.cursor()
        try:
            cursor.execute(
                """
                UPDATE pricing_config
                SET config_value = %s::jsonb,
                    description = %s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE config_key = %s
                """,
                (json.dumps(value), description, config_key),
            )
        finally:
            cursor.close()

    def insert(self, config_key: str, value: Any, description: str) -> None:
        cursor = self._db.cursor()
        try:
            cursor.execute(
                """
                INSERT INTO pricing_config (config_key, config_value, description)
                VALUES (%s, %s::jsonb, %s)
                """,
                (config_key, json.dumps(value), description),
            )
        finally:
            cursor.close()

    def exists(self, config_key: str) -> bool:
        cursor = self._db.cursor()
        try:
            cursor.execute(
                "SELECT 1 FROM pricing_config WHERE config_key = %s",
                (config_key,),
            )
            return cursor.fetchone() is not None
        finally:
            cursor.close()

    def get_raw_value(self, config_key: str) -> Optional[Any]:
        """Return the parsed JSON value for a single config key."""
        cursor = self._db.cursor()
        try:
            cursor.execute(
                "SELECT config_value FROM pricing_config WHERE config_key = %s",
                (config_key,),
            )
            row = cursor.fetchone()
            if not row:
                return None
            val = row[0]
            if isinstance(val, str):
                try:
                    return json.loads(val)
                except (json.JSONDecodeError, ValueError):
                    return val
            return val
        finally:
            cursor.close()

    def commit(self) -> None:
        self._db.commit()

    def rollback(self) -> None:
        self._db.rollback()
