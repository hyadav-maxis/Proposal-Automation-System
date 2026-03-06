"""Pydantic schemas for Purchase Orders."""

from typing import Optional
from pydantic import BaseModel


class POCreate(BaseModel):
    """Request body for creating a purchase order."""

    proposal_id: int
    client_name: Optional[str] = None
    total_amount: Optional[float] = None
