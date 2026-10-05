"""API v1 Router aggregation."""

from fastapi import APIRouter
from app.api.v1 import funds, calculators

api_v1_router = APIRouter()
api_v1_router.include_router(funds.router)
api_v1_router.include_router(calculators.router)
