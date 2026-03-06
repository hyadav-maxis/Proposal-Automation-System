"""
Purchase Order Service — business logic for PO creation.
"""

from datetime import datetime
from typing import Any, Dict, List

from fastapi import HTTPException

from app.repositories.purchase_order_repository import PurchaseOrderRepository
from app.schemas.purchase_order import POCreate
from app.services.contract_service import ContractService


class PurchaseOrderService:
    """Handles all business logic related to purchase orders."""

    def __init__(self, db) -> None:
        self._repo = PurchaseOrderRepository(db)
        self._contract_svc = ContractService()

    def create_purchase_order(self, request: POCreate) -> Dict[str, Any]:
        proposal = self._repo.get_proposal_summary(request.proposal_id)
        if not proposal:
            raise HTTPException(status_code=404, detail="Proposal not found")

        total_amount = request.total_amount or float(proposal["total_price"])
        client_name = request.client_name or proposal["client_name"]

        po_number = (
            f"PO-{datetime.now().strftime('%Y%m%d')}-"
            f"{datetime.now().strftime('%H%M%S')}"
        )

        try:
            po_id = self._repo.insert_purchase_order(
                po_number=po_number,
                proposal_id=request.proposal_id,
                client_name=client_name,
                total_amount=total_amount,
            )

            po_data = {
                "po_number": po_number,
                "client_name": client_name,
                "total_amount": total_amount,
            }
            doc_path = self._contract_svc.generate_po_document(po_data)
            self._repo.update_po_document_path(po_id, doc_path)

            self._repo.commit()

            return {
                "po_id": po_id,
                "po_number": po_number,
                "total_amount": total_amount,
                "status": "pending",
                "document_path": doc_path,
            }
        except HTTPException:
            self._repo.rollback()
            raise
        except Exception as exc:
            self._repo.rollback()
            raise HTTPException(
                status_code=500, detail=f"Error creating PO: {exc}"
            ) from exc

    def list_purchase_orders(self) -> List[Dict[str, Any]]:
        return self._repo.list_purchase_orders()
