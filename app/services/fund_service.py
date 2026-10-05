"""Fund Service orchestrating data provider calls, caching, and enrichment."""

from typing import List, Optional, Tuple
from app.adapters.base import FundDataProvider
from app.models.domain import (
    FundSearchResult,
    FundSummary,
    FundDetail,
    CategoriesMetadata,
    SIPProjectionResult,
)
from app.models.request import SIPCalculatorRequest
from app.services.calculator_service import CalculatorService
from app.core.cache import cache
from app.core.config import settings
from app.core.exceptions import ValidationError
from app.core.logging import logger


class FundService:
    """Core domain service for mutual fund operations."""

    def __init__(self, data_provider: FundDataProvider):
        self._provider = data_provider

    async def search_funds(self, query: str, limit: int = 10) -> List[FundSearchResult]:
        """Searches mutual funds with caching."""
        normalized_q = query.strip().lower()
        if len(normalized_q) < 2:
            raise ValidationError("Search query must be at least 2 characters long")

        cache_key = f"search:{normalized_q}:{limit}"
        cached = await cache.get(cache_key)
        if cached is not None:
            logger.debug("Cache hit for search: %s", cache_key)
            return cached

        results = await self._provider.search_funds(query=query, limit=limit)
        await cache.set(cache_key, results, settings.CACHE_SEARCH_TTL)
        return results

    async def explore_funds(
        self,
        category: Optional[str] = None,
        sort_by: str = "popularity",
        page: int = 0,
        size: int = 15,
    ) -> Tuple[List[FundSummary], int]:
        """Explores catalog with pagination and caching."""
        cache_key = f"explore:{category or 'all'}:{sort_by}:{page}:{size}"
        cached = await cache.get(cache_key)
        if cached is not None:
            logger.debug("Cache hit for explore: %s", cache_key)
            return cached

        funds, total_count = await self._provider.explore_funds(
            category=category,
            sort_by=sort_by,
            page=page,
            size=size,
        )
        result = (funds, total_count)
        await cache.set(cache_key, result, settings.CACHE_EXPLORE_TTL)
        return result

    async def get_fund_detail(self, fund_id: str) -> FundDetail:
        """Fetches complete scheme details with caching."""
        normalized_id = fund_id.strip().lower()
        cache_key = f"fund:{normalized_id}"
        cached = await cache.get(cache_key)
        if cached is not None:
            logger.debug("Cache hit for fund detail: %s", cache_key)
            return cached

        detail = await self._provider.get_fund_detail(fund_id=normalized_id)
        await cache.set(cache_key, detail, settings.CACHE_DETAIL_TTL)
        return detail

    async def get_categories_metadata(self) -> CategoriesMetadata:
        """Retrieves available categories and sort options."""
        cache_key = "categories:meta"
        cached = await cache.get(cache_key)
        if cached is not None:
            return cached

        meta = await self._provider.get_categories_metadata()
        await cache.set(cache_key, meta, settings.CACHE_CATEGORIES_TTL)
        return meta

    async def project_sip(self, req: SIPCalculatorRequest) -> SIPProjectionResult:
        """Projects SIP wealth accumulation, dynamically pulling CAGR if fund_id provided."""
        annual_rate = req.expected_return_rate
        benchmark_name = None

        if req.fund_id:
            # Dynamically derive expected return rate from scheme's historical CAGR
            fund = await self.get_fund_detail(req.fund_id)
            benchmark_name = fund.name
            if annual_rate is None:
                # Prefer 3Y returns, then 5Y, then 1Y, or fallback to 12%
                annual_rate = fund.returns.return_3y or fund.returns.return_5y or fund.returns.return_1y or 12.0

        if annual_rate is None:
            annual_rate = 12.0  # Industry standard benchmark default

        return CalculatorService.calculate_sip(
            monthly_investment=req.monthly_investment,
            tenure_years=req.tenure_years,
            annual_return_rate=annual_rate,
            benchmark_fund_id=req.fund_id,
            benchmark_fund_name=benchmark_name,
        )

    async def check_health(self) -> bool:
        """Checks upstream provider health status."""
        return await self._provider.check_health()
