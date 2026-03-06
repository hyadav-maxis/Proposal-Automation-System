"""
Pricing Config API router — /api/pricing-config/*
"""

from fastapi import APIRouter, Depends

from app.api.deps import get_db
from app.schemas.pricing_config import PricingConfigCreate, PricingConfigUpdate
from app.services.pricing_config_service import PricingConfigService

router = APIRouter(prefix="/api/pricing-config", tags=["Pricing Config"])


@router.get("")
def get_pricing_config(db=Depends(get_db)):
    """Return all pricing configuration entries."""
    return PricingConfigService(db).get_all()


@router.put("/{config_key}")
def update_pricing_config(
    config_key: str,
    config_data: PricingConfigUpdate,
    db=Depends(get_db),
):
    """Update a pricing configuration entry by key."""
    return PricingConfigService(db).update(config_key, config_data)


@router.post("")
def create_pricing_config(config_data: PricingConfigCreate, db=Depends(get_db)):
    """Create a new pricing configuration entry."""
    return PricingConfigService(db).create(config_data)
