"""app/api/v1 package — registers all v1 routers on a single APIRouter."""

from fastapi import APIRouter

from .proposals import router as proposals_router
from .purchase_orders import router as purchase_orders_router
from .pricing_config import router as pricing_config_router
from .exports import router as exports_router
from .chat import router as chat_router
from .settings import router as settings_router

# Single router that groups all v1 endpoints — included once in app/main.py
api_v1_router = APIRouter()
api_v1_router.include_router(proposals_router)
api_v1_router.include_router(purchase_orders_router)
api_v1_router.include_router(pricing_config_router)
api_v1_router.include_router(exports_router)
api_v1_router.include_router(chat_router)
api_v1_router.include_router(settings_router)

__all__ = ["api_v1_router"]
