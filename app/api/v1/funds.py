"""Mutual Fund API Endpoints (Discovery, Catalog, Details)."""

from typing import Optional, List
from fastapi import APIRouter, Depends, Query, Path, status
from app.services.fund_service import FundService
from app.api.deps import get_fund_service
from app.models.domain import (
    FundSearchResult,
    FundSummary,
    FundDetail,
    CategoriesMetadata,
)
from app.models.response import ApiResponse, PaginatedResponse, PaginationMeta

router = APIRouter(prefix="/funds", tags=["Mutual Funds"])


@router.get(
    "/search",
    response_model=ApiResponse[List[FundSearchResult]],
    summary="Search & Autocomplete Mutual Funds",
    description="Fuzzy search across active mutual fund schemes by name, keyword, or AMC.",
)
async def search_funds(
    q: str = Query(..., min_length=2, max_length=100, description="Search term", examples=["Parag Parikh"]),
    limit: int = Query(10, ge=1, le=50, description="Maximum number of items to return"),
    service: FundService = Depends(get_fund_service),
) -> ApiResponse[List[FundSearchResult]]:
    results = await service.search_funds(query=q, limit=limit)
    return ApiResponse(data=results)


@router.get(
    "/explore",
    response_model=PaginatedResponse[FundSummary],
    summary="Explore & Screen Fund Catalog",
    description="Filter, sort, and paginate through mutual funds with returns and risk metrics.",
)
async def explore_funds(
    category: Optional[str] = Query(None, description="Asset class filter: Equity, Debt, Hybrid, or all"),
    sort_by: str = Query(
        "popularity",
        pattern=r"^(popularity|returns_1y|returns_3y|returns_5y|rating)$",
        description="Sort dimension",
    ),
    page: int = Query(0, ge=0, description="Zero-based page index"),
    size: int = Query(15, ge=1, le=50, description="Items per page"),
    service: FundService = Depends(get_fund_service),
) -> PaginatedResponse[FundSummary]:
    funds, total_count = await service.explore_funds(
        category=category,
        sort_by=sort_by,
        page=page,
        size=size,
    )
    has_next = ((page + 1) * size) < total_count
    return PaginatedResponse(
        pagination=PaginationMeta(
            page=page,
            size=size,
            total_records=total_count,
            has_next=has_next,
        ),
        data=funds,
    )


@router.get(
    "/categories",
    response_model=ApiResponse[CategoriesMetadata],
    summary="Get Filter Categories & Metadata",
    description="Lists supported asset classes, subcategories, and sorting dimensions.",
)
async def get_categories(
    service: FundService = Depends(get_fund_service),
) -> ApiResponse[CategoriesMetadata]:
    meta = await service.get_categories_metadata()
    return ApiResponse(data=meta)


@router.get(
    "/{fund_id}",
    response_model=ApiResponse[FundDetail],
    summary="Get Fund Profile & Portfolio Holdings",
    description="Fetches comprehensive fund profile, including NAV, AUM, top 20 holdings, and manager details.",
)
async def get_fund_detail(
    fund_id: str = Path(..., min_length=3, max_length=150, pattern=r"^[a-z0-9\-]+$", description="Fund scheme slug"),
    service: FundService = Depends(get_fund_service),
) -> ApiResponse[FundDetail]:
    detail = await service.get_fund_detail(fund_id=fund_id)
    return ApiResponse(data=detail)
