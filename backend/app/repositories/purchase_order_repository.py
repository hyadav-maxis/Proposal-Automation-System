"""
Purchase Order Repository — all SQL for purchase orders.
"""

from typing import Any, Dict, List, Optional
from psycopg2.extras import RealDictCursor


class PurchaseOrderRepository:
    """Data-access object for purchase_orders."""

    def __init__(self, db) -> None:
        self._db = db

    def get_proposal_summary(self, proposal_id: int) -> Optional[Dict[str, Any]]:
        """Return (total_price, client_name) for a proposal."""
        cursor = self._db.cursor()
        try:
            cursor.execute(
                "SELECT total_price, client_name FROM proposals WHERE id = %s",
                (proposal_id,),
            )
            row = cursor.fetchone()
            if not row:
                return None
            return {"total_price": row[0], "client_name": row[1]}
        finally:
            cursor.close()

    def insert_purchase_order(
        self,
        po_number: str,
        proposal_id: int,
        client_name: str,
        total_amount: float,
    ) -> int:
        cursor = self._db.cursor()
        try:
            cursor.execute(
                """
                INSERT INTO purchase_orders
                    (po_number, proposal_id, client_name, total_amount, status)
                VALUES (%s, %s, %s, %s, 'pending')
                RETURNING id
                """,
                (po_number, proposal_id, client_name, total_amount),
            )
            return cursor.fetchone()[0]
        finally:
            cursor.close()

    def update_po_document_path(self, po_id: int, doc_path: str) -> None:
        cursor = self._db.cursor()
        try:
            cursor.execute(
                "UPDATE purchase_orders SET po_document_path = %s WHERE id = %s",
                (doc_path, po_id),
            )
        finally:
            cursor.close()

    def list_purchase_orders(self) -> List[Dict[str, Any]]:
        cursor = self._db.cursor(cursor_factory=RealDictCursor)
        try:
            cursor.execute("SELECT * FROM purchase_orders ORDER BY created_at DESC")
            return [dict(row) for row in cursor.fetchall()]
        finally:
            cursor.close()

    def commit(self) -> None:
        self._db.commit()

    def rollback(self) -> None:
        self._db.rollback()
