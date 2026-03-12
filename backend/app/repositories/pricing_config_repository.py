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

    # ── Email Templates (client_email_templates table) ────────────────────────

    _SYSTEM_SUBJECT = "Proposal {{proposal_number}} — {{project_name}}"
    _SYSTEM_BODY = """Dear {{client_name}},

We are pleased to inform you that the proposal for your project "{{project_name}}" has been prepared and is ready for your review. 

Please find the detailed proposal attached with this email. It includes the scope of work, pricing details, and timeline for the project.

If you have any questions, require clarification, or would like to discuss any part of the proposal, please feel free to reply to this email. We will be happy to assist you.

Thank you for the opportunity to work with you, and we look forward to your feedback.

Best regards,
Proposal Automation Team"""

    def ensure_system_template_exists(self) -> None:
        """Seed the SYSTEM default template if none exists yet."""
        cursor = self._db.cursor()
        try:
            cursor.execute(
                "SELECT id FROM client_email_templates WHERE template_type = 'SYSTEM' LIMIT 1"
            )
            if cursor.fetchone() is None:
                cursor.execute(
                    """
                    INSERT INTO client_email_templates
                        (template_name, template_type, subject, body)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (
                        "System Default Template",
                        "SYSTEM",
                        self._SYSTEM_SUBJECT,
                        self._SYSTEM_BODY,
                    ),
                )
                self._db.commit()
        finally:
            cursor.close()

    def get_all_email_templates(self) -> list:
        """Return all email templates ordered by type (SYSTEM first) then name."""
        cursor = self._db.cursor(cursor_factory=RealDictCursor)
        try:
            cursor.execute("""
                SELECT id, template_name, template_type, subject, body, updated_at
                FROM client_email_templates
                ORDER BY
                    CASE WHEN template_type = 'SYSTEM' THEN 0 ELSE 1 END,
                    template_name
            """)
            return [dict(r) for r in cursor.fetchall()]
        finally:
            cursor.close()

    def get_email_template_by_id(self, template_id: int) -> Optional[Dict[str, Any]]:
        """Return a single template by its ID."""
        cursor = self._db.cursor(cursor_factory=RealDictCursor)
        try:
            cursor.execute(
                "SELECT id, template_name, template_type, subject, body, updated_at "
                "FROM client_email_templates WHERE id = %s",
                (template_id,),
            )
            row = cursor.fetchone()
            return dict(row) if row else None
        finally:
            cursor.close()

    def create_email_template(
        self, template_name: str, subject: str, body: str, template_type: str = "CUSTOM"
    ) -> int:
        """Insert a new email template and return its ID."""
        cursor = self._db.cursor()
        try:
            cursor.execute(
                """
                INSERT INTO client_email_templates
                    (template_name, template_type, subject, body)
                VALUES (%s, %s, %s, %s)
                RETURNING id
                """,
                (template_name, template_type, subject, body),
            )
            new_id = cursor.fetchone()[0]
            return new_id
        finally:
            cursor.close()

    def update_email_template(
        self, template_id: int, template_name: str, subject: str, body: str
    ) -> bool:
        """Update an existing template. Returns True if a row was modified."""
        cursor = self._db.cursor()
        try:
            cursor.execute(
                """
                UPDATE client_email_templates
                SET template_name = %s,
                    subject = %s,
                    body = %s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
                """,
                (template_name, subject, body, template_id),
            )
            return cursor.rowcount > 0
        finally:
            cursor.close()

    def delete_email_template(self, template_id: int) -> bool:
        """Delete a template by ID. Returns True if a row was removed."""
        cursor = self._db.cursor()
        try:
            cursor.execute(
                "DELETE FROM client_email_templates WHERE id = %s AND template_type != 'SYSTEM'",
                (template_id,),
            )
            return cursor.rowcount > 0
        finally:
            cursor.close()

    # ── Active template selection (stored in pricing_config) ───────────────

    def get_active_template_id(self) -> Optional[int]:
        """Return the ID of the currently active email template, or None."""
        val = self.get_raw_value("active_email_template_id")
        if val is not None:
            try:
                return int(val)
            except (ValueError, TypeError):
                return None
        return None

    def set_active_template_id(self, template_id: int) -> None:
        """Persist the active email template selection."""
        if self.exists("active_email_template_id"):
            self.upsert(
                "active_email_template_id",
                template_id,
                "ID of the globally-active email template",
            )
        else:
            self.insert(
                "active_email_template_id",
                template_id,
                "ID of the globally-active email template",
            )

    def get_active_template(self) -> Optional[Dict[str, Any]]:
        """Convenience: return the full active template dict, or the SYSTEM template."""
        tid = self.get_active_template_id()
        if tid is not None:
            tpl = self.get_email_template_by_id(tid)
            if tpl:
                return tpl
        # Fallback: return the first SYSTEM template
        cursor = self._db.cursor(cursor_factory=RealDictCursor)
        try:
            cursor.execute(
                "SELECT id, template_name, template_type, subject, body, updated_at "
                "FROM client_email_templates WHERE template_type = 'SYSTEM' "
                "ORDER BY id LIMIT 1"
            )
            row = cursor.fetchone()
            return dict(row) if row else None
        finally:
            cursor.close()
