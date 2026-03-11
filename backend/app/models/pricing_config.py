"""Pydantic models for Pricing Configuration."""

from typing import Any, Dict
from pydantic import BaseModel


class PricingConfigUpdate(BaseModel):
    """Request body for updating a pricing config entry."""

    value: Any
    description: str = ""


class PricingConfigCreate(BaseModel):
    """Request body for creating a new pricing config entry."""

    config_key: str
    value: Dict[str, Any] = {}
    description: str = ""
