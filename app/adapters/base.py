"""Abstract Base Provider for Mutual Fund Data Sources (Port)."""

from abc import ABC, abstractmethod
from typing import List, Optional, Tuple
from app.models.domain import (
    FundSearchResult,
    FundSummary,
    FundDetail,
    CategoriesMetadata,
)


class FundDataProvider(ABC):
    """Interface defining operations required by the Fund Service."""

    @abstractmethod
    async def search_funds(self, query: str, limit: int = 10) -> List[FundSearchResult]:
        """Search and autocomplete mutual fund schemes."""
        pass

    @abstractmethod
    async def explore_funds(
        self,
        category: Optional[str] = None,
        sort_by: str = "popularity",
        page: int = 0,
        size: int = 15,
    ) -> Tuple[List[FundSummary], int]:
        """Explore, screen, and filter funds returning (funds, total_count)."""
        pass

    @abstractmethod
    async def get_fund_detail(self, fund_id: str) -> FundDetail:
        """Fetch full details and holdings for a specific fund scheme."""
        pass

    @abstractmethod
    async def get_categories_metadata(self) -> CategoriesMetadata:
        """Fetch available categories, subcategories, and sorting dimensions."""
        pass

    @abstractmethod
    async def check_health(self) -> bool:
        """Check availability of upstream provider."""
        pass
