"""
Proposal Repository — all SQL for the proposals domain.

Receives a live psycopg2 connection and returns plain dicts.
No business logic lives here.
"""

from typing import Any, Dict, List, Optional
from psycopg2.extras import RealDictCursor


class ProposalRepository:
    """Data-access object for proposals, proposal_details and pricing_components."""

    def __init__(self, db) -> None:
        self._db = db

    # ── Proposals ────────────────────────────────────────────────────────────

    def insert_proposal(
        self,
        proposal_number: str,
        client_name: str,
        client_email: Optional[str],
        project_name: str,
        total_price: float,
    ) -> int:
        """Insert a proposal row and return the new id."""
        cursor = self._db.cursor()
        try:
            cursor.execute(
                """
                INSERT INTO proposals
                    (proposal_number, client_name, client_email,
                     project_name, total_price, status)
                VALUES (%s, %s, %s, %s, %s, 'draft')
                RETURNING id
                """,
                (proposal_number, client_name, client_email, project_name, total_price),
            )
            return cursor.fetchone()[0]
        finally:
            cursor.close()

    def insert_proposal_details(
        self,
        proposal_id: int,
        database_size_gb: float,
        number_of_runs: int,
        deployment_type: str,
        has_where_clauses: bool,
        has_birt_reports: bool,
        complexity_score: int,
        complexity_reason: Optional[str],
        source_dialect: Optional[str],
        target_dialect: Optional[str],
        sql_content: Optional[str],
        resource_location: str = "standard",
    ) -> None:
        cursor = self._db.cursor()
        try:
            cursor.execute(
                """
                INSERT INTO proposal_details
                    (proposal_id, database_size_gb, number_of_runs,
                     deployment_type, has_where_clauses, has_birt_reports,
                     complexity_score, complexity_reason,
                     source_dialect, target_dialect, sql_content, resource_location)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    proposal_id, database_size_gb, number_of_runs,
                    deployment_type, has_where_clauses, has_birt_reports,
                    complexity_score, complexity_reason,
                    source_dialect, target_dialect, sql_content, resource_location,
                ),
            )
        finally:
            cursor.close()

    def insert_pricing_component(
        self,
        proposal_id: int,
        comp_type: str,
        comp_name: str,
        quantity: float,
        unit_price: float,
        total_price: float,
    ) -> None:
        cursor = self._db.cursor()
        try:
            cursor.execute(
                """
                INSERT INTO pricing_components
                    (proposal_id, component_type, component_name,
                     quantity, unit_price, total_price)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (proposal_id, comp_type, comp_name, quantity, unit_price, total_price),
            )
        finally:
            cursor.close()

    def insert_complexity_breakdown(
        self,
        proposal_id: int,
        complexity_score: int,
        number_of_reports: int,
        price_per_report: float,
        total_price: float,
    ) -> None:
        cursor = self._db.cursor()
        try:
            cursor.execute(
                """
                INSERT INTO report_complexity_breakdown
                    (proposal_id, complexity_score,
                     number_of_reports, price_per_report, total_price)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (proposal_id, complexity_score, number_of_reports, price_per_report, total_price),
            )
        finally:
            cursor.close()

    def get_proposal_by_id(self, proposal_id: int) -> Optional[Dict[str, Any]]:
        """Return a full proposal dict including details, components, and complexity breakdown."""
        cursor = self._db.cursor(cursor_factory=RealDictCursor)
        try:
            cursor.execute(
                """
                SELECT p.*, pd.database_size_gb, pd.number_of_runs,
                       pd.deployment_type, pd.has_where_clauses, pd.has_birt_reports,
                       pd.source_dialect, pd.target_dialect, pd.sql_content, pd.resource_location
                FROM proposals p
                LEFT JOIN proposal_details pd ON p.id = pd.proposal_id
                WHERE p.id = %s
                """,
                (proposal_id,),
            )
            proposal = cursor.fetchone()
            if not proposal:
                return None

            cursor.execute(
                "SELECT * FROM pricing_components WHERE proposal_id = %s",
                (proposal_id,),
            )
            components = cursor.fetchall()

            cursor.execute(
                """
                SELECT * FROM report_complexity_breakdown
                WHERE proposal_id = %s
                ORDER BY complexity_score
                """,
                (proposal_id,),
            )
            complexity_breakdown = cursor.fetchall()

            return {
                "proposal": dict(proposal),
                "components": [dict(c) for c in components],
                "complexity_breakdown": [dict(cb) for cb in complexity_breakdown],
            }
        finally:
            cursor.close()

    def replace_proposal_details(
        self,
        proposal_id: int,
        database_size_gb: float,
        number_of_runs: int,
        deployment_type: str,
        has_where_clauses: bool,
        has_birt_reports: bool,
        complexity_score: int,
        complexity_reason: Optional[str],
        source_dialect: Optional[str],
        target_dialect: Optional[str],
        sql_content: Optional[str],
        resource_location: str = "standard",
    ) -> None:
        """Upsert proposal_details for an existing proposal."""
        cursor = self._db.cursor()
        try:
            cursor.execute(
                "SELECT id FROM proposal_details WHERE proposal_id = %s",
                (proposal_id,),
            )
            exists = cursor.fetchone()
            if exists:
                cursor.execute(
                    """
                    UPDATE proposal_details SET
                        database_size_gb = %s, number_of_runs = %s,
                        deployment_type = %s, has_where_clauses = %s,
                        has_birt_reports = %s, complexity_score = %s,
                        complexity_reason = %s, source_dialect = %s,
                        target_dialect = %s, sql_content = %s, resource_location = %s
                    WHERE proposal_id = %s
                    """,
                    (
                        database_size_gb, number_of_runs, deployment_type,
                        has_where_clauses, has_birt_reports, complexity_score,
                        complexity_reason, source_dialect, target_dialect,
                        sql_content, resource_location, proposal_id,
                    ),
                )
            else:
                cursor.execute(
                    """
                    INSERT INTO proposal_details
                        (proposal_id, database_size_gb, number_of_runs,
                         deployment_type, has_where_clauses, has_birt_reports,
                         complexity_score, complexity_reason,
                         source_dialect, target_dialect, sql_content, resource_location)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        proposal_id, database_size_gb, number_of_runs,
                        deployment_type, has_where_clauses, has_birt_reports,
                        complexity_score, complexity_reason,
                        source_dialect, target_dialect, sql_content, resource_location,
                    ),
                )
        finally:
            cursor.close()

    def delete_pricing_components(self, proposal_id: int) -> None:
        """Remove all pricing components for a proposal (before reinserting)."""
        cursor = self._db.cursor()
        try:
            cursor.execute(
                "DELETE FROM pricing_components WHERE proposal_id = %s",
                (proposal_id,),
            )
        finally:
            cursor.close()

    def delete_complexity_breakdown(self, proposal_id: int) -> None:
        """Remove all complexity breakdown rows for a proposal (before reinserting)."""
        cursor = self._db.cursor()
        try:
            cursor.execute(
                "DELETE FROM report_complexity_breakdown WHERE proposal_id = %s",
                (proposal_id,),
            )
        finally:
            cursor.close()

    def update_proposal_total_price(self, proposal_id: int, total_price: float) -> None:
        """Update the total_price and updated_at on the proposals table."""
        cursor = self._db.cursor()
        try:
            cursor.execute(
                "UPDATE proposals SET total_price = %s, updated_at = NOW() WHERE id = %s",
                (total_price, proposal_id),
            )
        finally:
            cursor.close()

    def list_proposals(self, location: Optional[str] = None) -> List[Dict[str, Any]]:
        cursor = self._db.cursor(cursor_factory=RealDictCursor)
        try:
            query = """
                SELECT p.id, p.proposal_number, p.client_name, p.client_email,
                       p.project_name, p.total_price, p.status, p.created_at, p.updated_at,
                       pd.resource_location
                FROM proposals p
                LEFT JOIN proposal_details pd ON p.id = pd.proposal_id
            """
            params = []
            if location and location != "all":
                query += " WHERE pd.resource_location = %s"
                params.append(location)
            
            query += " ORDER BY p.created_at DESC"
            
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
        finally:
            cursor.close()

    def delete_proposal(self, proposal_id: int) -> bool:
        """Delete a proposal and all related rows. Returns True if a row was deleted."""
        cursor = self._db.cursor()
        try:
            # Child rows first (FK constraints)
            cursor.execute(
                "DELETE FROM report_complexity_breakdown WHERE proposal_id = %s",
                (proposal_id,),
            )
            cursor.execute(
                "DELETE FROM pricing_components WHERE proposal_id = %s",
                (proposal_id,),
            )
            cursor.execute(
                "DELETE FROM proposal_details WHERE proposal_id = %s",
                (proposal_id,),
            )
            cursor.execute(
                "DELETE FROM proposals WHERE id = %s",
                (proposal_id,),
            )
            return cursor.rowcount > 0
        finally:
            cursor.close()

    def update_proposal(
        self,
        proposal_id: int,
        client_name: Optional[str] = None,
        client_email: Optional[str] = None,
        project_name: Optional[str] = None,
        status: Optional[str] = None,
    ) -> bool:
        """Update editable proposal fields. Returns True if a row was updated."""
        fields, values = [], []
        if client_name is not None:
            fields.append("client_name = %s")
            values.append(client_name)
        if client_email is not None:
            fields.append("client_email = %s")
            values.append(client_email)
        if project_name is not None:
            fields.append("project_name = %s")
            values.append(project_name)
        if status is not None:
            fields.append("status = %s")
            values.append(status)
        if not fields:
            return False
        fields.append("updated_at = NOW()")
        values.append(proposal_id)
        cursor = self._db.cursor()
        try:
            cursor.execute(
                f"UPDATE proposals SET {', '.join(fields)} WHERE id = %s",
                values,
            )
            return cursor.rowcount > 0
        finally:
            cursor.close()

    def get_proposal_for_export(self, proposal_id: int) -> Optional[Dict[str, Any]]:
        """Minimal data needed for PDF/Excel export."""
        cursor = self._db.cursor(cursor_factory=RealDictCursor)
        try:
            cursor.execute(
                """
                SELECT p.id, p.proposal_number, p.client_name, p.project_name, p.total_price,
                       pd.database_size_gb, pd.number_of_runs, pd.deployment_type,
                       pd.has_where_clauses, pd.has_birt_reports, pd.resource_location
                FROM proposals p
                LEFT JOIN proposal_details pd ON p.id = pd.proposal_id
                WHERE p.id = %s
                """,
                (proposal_id,),
            )
            row = cursor.fetchone()
            if not row:
                return None

            cursor.execute(
                "SELECT * FROM pricing_components WHERE proposal_id = %s",
                (proposal_id,),
            )
            components = list(cursor.fetchall())

            cursor.execute(
                "SELECT * FROM report_complexity_breakdown "
                "WHERE proposal_id = %s ORDER BY complexity_score",
                (proposal_id,),
            )
            breakdown = list(cursor.fetchall())

            return {
                "row": dict(row),
                "components": [dict(c) for c in components],
                "breakdown": [dict(b) for b in breakdown],
            }
        finally:
            cursor.close()

    def commit(self) -> None:
        self._db.commit()

    def rollback(self) -> None:
        self._db.rollback()
