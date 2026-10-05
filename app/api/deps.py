"""Dependency Injection providers for FastAPI routes."""

from fastapi import Depends
import httpx
from app.core.http_client import HTTPClientManager
from app.adapters.base import FundDataProvider
from app.adapters.groww_adapter import GrowwWebAdapter
from app.services.fund_service import FundService


def get_http_client() -> httpx.AsyncClient:
    """Provides singleton managed httpx.AsyncClient."""
    return HTTPClientManager.get_client()


def get_data_provider(
    client: httpx.AsyncClient = Depends(get_http_client),
) -> FundDataProvider:
    """
    Provides FundDataProvider instance.
    To replace Groww with an official API, swap this factory function to return
    e.g. OfficialAmfiAdapter(client=client).
    """
    return GrowwWebAdapter(client=client)


def get_fund_service(
    provider: FundDataProvider = Depends(get_data_provider),
) -> FundService:
    """Provides business domain service."""
    return FundService(data_provider=provider)
