"""
Purchase Orders API router — /api/purchase-orders/*
"""

from fastapi import APIRouter, Depends

from app.api.deps import get_db
from app.schemas.purchase_order import POCreate
from app.services.purchase_order_service import PurchaseOrderService

router = APIRouter(prefix="/api/purchase-orders", tags=["Purchase Orders"])


@router.post("/create")
def create_purchase_order(request: POCreate, db=Depends(get_db)):
    """Create a purchase order from an existing proposal."""
    return PurchaseOrderService(db).create_purchase_order(request)


@router.get("")
def list_purchase_orders(db=Depends(get_db)):
    """List all purchase orders."""
    return PurchaseOrderService(db).list_purchase_orders()
