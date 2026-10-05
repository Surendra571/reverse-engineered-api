"""Pytest test fixtures and mock upstream payloads."""

import pytest
import pytest_asyncio
import httpx
from httpx import ASGITransport
from typing import AsyncGenerator, Dict, Any

from app.main import app
from app.core.cache import cache


@pytest_asyncio.fixture(autouse=True)
async def clear_cache_before_each_test():
    """Ensures each test starts with a clean cache."""
    await cache.clear()
    yield
    await cache.clear()


@pytest_asyncio.fixture
async def async_client() -> AsyncGenerator[httpx.AsyncClient, None]:
    """Provides async HTTP test client communicating with FastAPI app."""
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest.fixture
def mock_search_response() -> Dict[str, Any]:
    return {
        "content": [
            {
                "id": "parag-parikh-long-term-value-fund-direct-growth",
                "search_id": "parag-parikh-long-term-value-fund-direct-growth",
                "title": "Parag Parikh Flexi Cap Fund",
                "scheme_code": "122639",
                "entity_type": "Scheme",
            },
            {
                "id": "parag-parikh-elss-tax-saver-fund-direct-growth",
                "search_id": "parag-parikh-elss-tax-saver-fund-direct-growth",
                "title": "Parag Parikh ELSS Tax Saver Fund",
                "scheme_code": "147481",
                "entity_type": "Scheme",
            },
            {
                "id": "parag-milk-foods-ltd",
                "search_id": "parag-milk-foods-ltd",
                "title": "Parag Milk Foods Ltd.",
                "scheme_code": None,
                "entity_type": "Stocks",
            },
        ]
    }


@pytest.fixture
def mock_explore_response() -> Dict[str, Any]:
    return {
        "total_results": 2,
        "content": [
            {
                "search_id": "bandhan-small-cap-fund-direct-growth",
                "scheme_name": "Bandhan Small Cap Fund Direct Growth",
                "scheme_code": "148123",
                "fund_house": "Bandhan Mutual Fund",
                "category": "Equity",
                "sub_category": "Small Cap Fund",
                "risk": "Very High",
                "nav": 42.18,
                "aum": 6245.8,
                "expense_ratio": 0.45,
                "return1d": 0.35,
                "return1y": 34.2,
                "return3y": 23.15,
                "return5y": 28.4,
                "min_sip_investment": 100.0,
            },
            {
                "search_id": "sbi-gold-direct-plan-growth",
                "scheme_name": "SBI Gold Direct Plan Growth",
                "scheme_code": "119821",
                "fund_house": "SBI Mutual Fund",
                "category": "Other",
                "sub_category": "Gold",
                "risk": "High",
                "nav": 24.5,
                "aum": 3120.0,
                "expense_ratio": 0.12,
                "return1d": -0.1,
                "return1y": 14.5,
                "return3y": 12.3,
                "return5y": 11.8,
                "min_sip_investment": 500.0,
            },
        ],
    }


@pytest.fixture
def mock_detail_response() -> Dict[str, Any]:
    return {
        "scheme_name": "Parag Parikh Flexi Cap Fund",
        "search_id": "parag-parikh-long-term-value-fund-direct-growth",
        "scheme_code": "122639",
        "fund_house": "PPFAS Mutual Fund",
        "category": "Equity",
        "sub_category": "Flexi Cap Fund",
        "risk": "Very High",
        "benchmark_name": "NIFTY 500 TRI",
        "nav": 86.42,
        "nav_date": "2026-10-03",
        "aum": 72340.5,
        "expense_ratio": 0.62,
        "exit_load": "2% if redeemed within 365 days",
        "stamp_duty": "0.005%",
        "lock_in": "Nil",
        "min_sip_investment": 1000.0,
        "min_investment_amount": 1000.0,
        "return1d": 0.15,
        "return_stats": {
            "return1y": 26.8,
            "return3y": 19.4,
            "return5y": 22.1,
        },
        "fund_manager_details": [
            {
                "fund_manager": "Rajeev Thakkar",
                "experience": "20+ years",
                "description": "Chief Investment Officer",
            }
        ],
        "holdings": [
            {
                "company_name": "HDFC Bank Ltd.",
                "sector_name": "Financial",
                "corpus_per": 7.82,
                "nature_name": "Equity",
            },
            {
                "company_name": "ITC Ltd.",
                "sector_name": "Consumer Goods",
                "corpus_per": 6.14,
                "nature_name": "Equity",
            },
        ],
    }
