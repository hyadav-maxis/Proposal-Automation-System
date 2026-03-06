"""
Pricing Config Service — business logic for pricing configuration CRUD.
"""

from typing import Any, Dict

from fastapi import HTTPException

from app.repositories.pricing_config_repository import PricingConfigRepository
from app.schemas.pricing_config import PricingConfigCreate, PricingConfigUpdate


class PricingConfigService:
    """Handles reading and updating the pricing_config table."""

    def __init__(self, db) -> None:
        self._repo = PricingConfigRepository(db)

    def get_all(self) -> Dict[str, Any]:
        return self._repo.get_all()

    def update(self, config_key: str, data: PricingConfigUpdate) -> Dict[str, Any]:
        if not self._repo.exists(config_key):
            raise HTTPException(
                status_code=404,
                detail=f"Pricing config '{config_key}' not found",
            )
        try:
            self._repo.upsert(config_key, data.value, data.description)
            self._repo.commit()
            return {
                "message": f"Pricing config '{config_key}' updated successfully",
                "config_key": config_key,
                "value": data.value,
            }
        except HTTPException:
            self._repo.rollback()
            raise
        except Exception as exc:
            self._repo.rollback()
            raise HTTPException(
                status_code=500, detail=f"Error updating pricing config: {exc}"
            ) from exc

    def create(self, data: PricingConfigCreate) -> Dict[str, Any]:
        if self._repo.exists(data.config_key):
            raise HTTPException(
                status_code=400,
                detail=f"Pricing config '{data.config_key}' already exists",
            )
        try:
            self._repo.insert(data.config_key, data.value, data.description)
            self._repo.commit()
            return {
                "message": f"Pricing config '{data.config_key}' created successfully",
                "config_key": data.config_key,
            }
        except HTTPException:
            self._repo.rollback()
            raise
        except Exception as exc:
            self._repo.rollback()
            raise HTTPException(
                status_code=500, detail=f"Error creating pricing config: {exc}"
            ) from exc
