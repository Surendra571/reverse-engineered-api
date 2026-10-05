"""Groww Concrete Web Adapter implementing FundDataProvider."""

import asyncio
from typing import List, Optional, Tuple, Dict, Any
import httpx

from app.adapters.base import FundDataProvider
from app.models.domain import (
    FundSearchResult,
    FundSummary,
    FundDetail,
    CategoriesMetadata,
    CategoryOption,
)
from app.parsers.groww_json_parser import GrowwJsonParser
from app.parsers.html_fallback_parser import HTMLFallbackParser
from app.core.config import settings
from app.core.exceptions import (
    ResourceNotFoundError,
    UpstreamServiceUnavailableError,
    UpstreamRateLimitedError,
    MalformedUpstreamDataError,
)
from app.core.logging import logger


class GrowwWebAdapter(FundDataProvider):
    """Adapts Groww's public web microservices to the standard FundDataProvider interface."""

    SORT_MAPPING = {
        "popularity": "3",
        "returns_3y": "0",
        "returns_1y": "4",
        "returns_5y": "5",
        "rating": "1",
    }

    def __init__(self, client: httpx.AsyncClient):
        self._client = client
        self._base_url = settings.UPSTREAM_BASE_URL

    async def _execute_request(self, method: str, url: str, **kwargs) -> httpx.Response:
        """Executes HTTP request with bounded retries and exponential backoff for idempotent operations."""
        retries = settings.UPSTREAM_MAX_RETRIES
        backoff = settings.UPSTREAM_BACKOFF_FACTOR

        for attempt in range(retries + 1):
            try:
                response = await self._client.request(method, url, **kwargs)

                # Check HTTP status codes
                if response.status_code == 404:
                    raise ResourceNotFoundError(f"Requested upstream resource not found at {url}")

                if response.status_code == 429:
                    raise UpstreamRateLimitedError("Upstream service returned rate limit (429)", details={"url": url})

                if response.status_code == 403:
                    # Cloudflare challenge or forbidden
                    raise UpstreamRateLimitedError("Upstream access restricted or challenged by WAF (403)", details={"url": url})

                if response.status_code >= 500:
                    if attempt < retries:
                        await asyncio.sleep(backoff * (2 ** attempt))
                        continue
                    raise UpstreamServiceUnavailableError(
                        f"Upstream service error (HTTP {response.status_code})",
                        details={"status": response.status_code, "url": url},
                    )

                response.raise_for_status()
                return response

            except (httpx.ConnectError, httpx.ReadTimeout, httpx.ConnectTimeout) as exc:
                logger.warning(
                    "Network error during upstream request to %s (attempt %d/%d): %s",
                    url,
                    attempt + 1,
                    retries + 1,
                    str(exc),
                )
                if attempt < retries:
                    await asyncio.sleep(backoff * (2 ** attempt))
                    continue
                raise UpstreamServiceUnavailableError(
                    "Failed to connect to upstream service within timeout limits",
                    details={"error": str(exc), "url": url},
                ) from exc

        raise UpstreamServiceUnavailableError("Exhausted retries calling upstream service", details={"url": url})

    async def search_funds(self, query: str, limit: int = 10) -> List[FundSearchResult]:
        url = f"{self._base_url}/v1/api/search/v1/entity"
        params = {"app": "false", "page": 0, "q": query, "size": limit}

        response = await self._execute_request("GET", url, params=params)
        try:
            data = response.json()
        except Exception as exc:
            raise MalformedUpstreamDataError("Upstream did not return valid JSON for search") from exc

        return GrowwJsonParser.parse_search_results(data)

    async def explore_funds(
        self,
        category: Optional[str] = None,
        sort_by: str = "popularity",
        page: int = 0,
        size: int = 15,
    ) -> Tuple[List[FundSummary], int]:
        url = f"{self._base_url}/v1/api/search/v3/query/filter_derived_data/st_filter"
        mapped_sort = self.SORT_MAPPING.get(sort_by.lower(), "3")
        params: Dict[str, Any] = {
            "doc_type": "scheme",
            "page": page,
            "size": min(size, settings.MAX_PAGE_SIZE),
            "sort_by": mapped_sort,
        }

        if category and category.lower() != "all":
            # Groww accepts category parameter (e.g. Equity, Debt, Hybrid)
            params["category"] = category.capitalize()

        response = await self._execute_request("GET", url, params=params)
        try:
            data = response.json()
        except Exception as exc:
            raise MalformedUpstreamDataError("Upstream did not return valid JSON for explore") from exc

        return GrowwJsonParser.parse_explore_results(data)

    async def get_fund_detail(self, fund_id: str) -> FundDetail:
        url = f"{self._base_url}/v1/api/data/mf/web/v4/scheme/search/{fund_id}"
        response = await self._execute_request("GET", url)

        content_type = response.headers.get("content-type", "")
        if "application/json" in content_type:
            try:
                data = response.json()
                return GrowwJsonParser.parse_fund_detail(data, fund_id)
            except Exception as exc:
                if isinstance(exc, (ResourceNotFoundError, MalformedUpstreamDataError)):
                    raise
                raise MalformedUpstreamDataError(f"Error parsing scheme detail JSON: {str(exc)}") from exc
        else:
            # Fallback for HTML responses (Next.js server-rendered HTML)
            logger.info("Received HTML response for %s, applying HTML fallback parser", fund_id)
            html_text = response.text
            page_props = HTMLFallbackParser.extract_page_props(html_text)
            scheme_data = page_props.get("schemeData") or page_props.get("schemeDetails")
            if not scheme_data:
                raise ResourceNotFoundError(f"Fund scheme '{fund_id}' not found in HTML page state")
            return GrowwJsonParser.parse_fund_detail(scheme_data, fund_id)

    async def get_categories_metadata(self) -> CategoriesMetadata:
        """Returns standard mutual fund categorization structure."""
        return CategoriesMetadata(
            categories=[
                CategoryOption(key="Equity", display_name="Equity (Growth Oriented)"),
                CategoryOption(key="Debt", display_name="Debt (Income & Capital Preservation)"),
                CategoryOption(key="Hybrid", display_name="Hybrid (Balanced Equity & Debt)"),
                CategoryOption(key="Solution Oriented", display_name="Solution Oriented (Retirement & Children)"),
                CategoryOption(key="Other", display_name="Index Funds, ETFs & Fund of Funds"),
            ],
            sub_categories=[
                CategoryOption(key="Large Cap Fund", display_name="Large Cap"),
                CategoryOption(key="Mid Cap Fund", display_name="Mid Cap"),
                CategoryOption(key="Small Cap Fund", display_name="Small Cap"),
                CategoryOption(key="Flexi Cap Fund", display_name="Flexi Cap"),
                CategoryOption(key="ELSS", display_name="ELSS (Tax Saver)"),
                CategoryOption(key="Liquid Fund", display_name="Liquid"),
                CategoryOption(key="Overnight Fund", display_name="Overnight"),
                CategoryOption(key="Arbitrage Fund", display_name="Arbitrage"),
            ],
            sort_options=[
                CategoryOption(key="popularity", display_name="Popularity"),
                CategoryOption(key="returns_3y", display_name="3-Year Returns"),
                CategoryOption(key="returns_1y", display_name="1-Year Returns"),
                CategoryOption(key="returns_5y", display_name="5-Year Returns"),
                CategoryOption(key="rating", display_name="Crisil / Groww Rating"),
            ],
        )

    async def check_health(self) -> bool:
        """Checks if upstream responds within 3 seconds."""
        try:
            url = f"{self._base_url}/v1/api/search/v1/entity"
            params = {"app": "false", "page": 0, "q": "sbi", "size": 1}
            response = await self._client.get(url, params=params, timeout=3.0)
            return response.status_code == 200
        except Exception as exc:
            logger.warning("Upstream health check failed: %s", str(exc))
            return False
