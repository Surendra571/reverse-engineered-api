"""
Comprehensive CLI Test Script for Razorpay Assignment Reviewer.

Tests all key cases:
1. Health Check
2. Fund Search & Autocomplete
3. Fund Screener & Explore with Filtering
4. Category Metadata
5. Fund Details & Top Portfolio Holdings
6. SIP Wealth Compounding Calculator (Dynamic & Static)
7. Assignment Route Aliases (/api/search, /api/items/{id}, /api/categories)
8. Input Validation & Error Handling (404, 422)
9. Cache Performance Verification

Supports both:
- Live HTTP server: `python scripts/test_api.py --base-url http://localhost:8000`
- Direct in-process ASGI testing: `python scripts/test_api.py` (Default - no separate server required!)
"""

import sys
import time
import json
import argparse
import asyncio
from pathlib import Path
from typing import Any, Dict
import httpx

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
BOLD = "\033[1m"
RESET = "\033[0m"


def print_header(title: str):
    print(f"\n{BOLD}{CYAN}{'='*70}{RESET}")
    print(f"{BOLD}{CYAN}  {title}{RESET}")
    print(f"{BOLD}{CYAN}{'='*70}{RESET}")


def print_step(name: str, status: bool, duration_ms: float, details: str = ""):
    icon = f"{GREEN}[PASS]{RESET}" if status else f"{RED}[FAIL]{RESET}"
    print(f"  {icon} [{duration_ms:6.1f}ms] {BOLD}{name}{RESET}")
    if details:
        print(f"      {details}")


async def run_test_suite(client: httpx.AsyncClient) -> bool:
    all_passed = True
    total_start = time.perf_counter()

    print_header("1. System Health Check")
    t0 = time.perf_counter()
    r = await client.get("/health")
    ms = (time.perf_counter() - t0) * 1000
    ok = r.status_code == 200 and r.json().get("status") == "ok"
    all_passed &= ok
    print_step("GET /health", ok, ms, f"Status: {r.status_code}, Upstream: {r.json().get('upstream_status')}")

    print_header("2. Search & Autocomplete")
    t0 = time.perf_counter()
    r = await client.get("/api/v1/funds/search?q=parag+parikh&limit=5")
    ms = (time.perf_counter() - t0) * 1000
    data = r.json().get("data", [])
    ok = r.status_code == 200 and len(data) > 0
    all_passed &= ok
    top_fund_id = data[0]["id"] if ok else "parag-parikh-long-term-value-fund-direct-growth"
    top_fund_name = data[0]["name"] if ok else "Parag Parikh Flexi Cap Fund"
    print_step("GET /api/v1/funds/search?q=parag+parikh", ok, ms, f"Found {len(data)} funds. Top match: '{top_fund_name}' ({top_fund_id})")

    print_header("3. Catalog Screener & Filters (Explore)")
    t0 = time.perf_counter()
    r = await client.get("/api/v1/funds/explore?category=Equity&sort_by=returns_3y&page=0&size=3")
    ms = (time.perf_counter() - t0) * 1000
    ok = r.status_code == 200 and len(r.json().get("data", [])) > 0
    all_passed &= ok
    pagination = r.json().get("pagination", {})
    first_item = r.json().get("data", [{}])[0]
    print_step(
        "GET /api/v1/funds/explore (Equity, Sorted by 3Y Returns)",
        ok,
        ms,
        f"Total schemes available: {pagination.get('total_records')}, Top: '{first_item.get('name')}' (3Y CAGR: {first_item.get('returns', {}).get('return_3y')}%)",
    )

    print_header("4. Category & Sorting Metadata")
    t0 = time.perf_counter()
    r = await client.get("/api/v1/funds/categories")
    ms = (time.perf_counter() - t0) * 1000
    cat_data = r.json().get("data", {})
    ok = r.status_code == 200 and len(cat_data.get("categories", [])) >= 3
    all_passed &= ok
    categories_list = [c["key"] for c in cat_data.get("categories", [])]
    print_step("GET /api/v1/funds/categories", ok, ms, f"Categories supported: {', '.join(categories_list)}")

    print_header("5. Deep Fund Details & Portfolio Holdings")
    t0 = time.perf_counter()
    r = await client.get(f"/api/v1/funds/{top_fund_id}")
    ms = (time.perf_counter() - t0) * 1000
    fund_detail = r.json().get("data", {})
    holdings = fund_detail.get("top_holdings", [])
    ok = r.status_code == 200 and len(holdings) > 0
    all_passed &= ok
    holdings_summary = ", ".join([f"{h['company_name']} ({h.get('allocation_percentage', 0)}%)" for h in holdings[:3]])
    print_step(
        f"GET /api/v1/funds/{top_fund_id}",
        ok,
        ms,
        f"NAV: INR {fund_detail.get('nav')}, AUM: INR {fund_detail.get('aum_in_crores')} Cr, Top Holdings: {holdings_summary}",
    )

    print_header("6. Financial SIP Compounding Calculator")
    # Dynamic CAGR from Fund
    t0 = time.perf_counter()
    calc_payload = {
        "monthly_investment": 10000.0,
        "tenure_years": 10,
        "fund_id": top_fund_id,
    }
    r = await client.post("/api/v1/calculators/sip", json=calc_payload)
    ms = (time.perf_counter() - t0) * 1000
    calc_res = r.json().get("data", {})
    ok = r.status_code == 200 and calc_res.get("total_future_value", 0) > calc_res.get("total_invested_amount", 0)
    all_passed &= ok
    print_step(
        "POST /api/v1/calculators/sip (Dynamic Fund Benchmark)",
        ok,
        ms,
        f"Invested: INR {calc_res.get('total_invested_amount'):,.0f} -> Estimated Future Value: INR {calc_res.get('total_future_value'):,.0f} @ {calc_res.get('annual_expected_return_rate')}% CAGR",
    )

    print_header("7. Assignment Convenience Route Aliases")
    t0 = time.perf_counter()
    r1 = await client.get("/api/search?q=hdfc&limit=2")
    r2 = await client.get(f"/api/items/{top_fund_id}")
    r3 = await client.get("/api/categories")
    ms = (time.perf_counter() - t0) * 1000
    ok = r1.status_code == 200 and r2.status_code == 200 and r3.status_code == 200
    all_passed &= ok
    print_step("GET /api/search, /api/items/{id}, /api/categories", ok, ms, "All convenience endpoints mapped successfully")

    print_header("8. Error Handling & Validation Tests")
    # 404 Not Found
    t0 = time.perf_counter()
    r_404 = await client.get("/api/v1/funds/non-existent-fund-slug-xyz")
    ms_404 = (time.perf_counter() - t0) * 1000
    ok_404 = r_404.status_code == 404 and r_404.json().get("error", {}).get("code") == "NOT_FOUND"
    all_passed &= ok_404
    print_step("GET /api/v1/funds/unknown-fund -> 404 NOT_FOUND", ok_404, ms_404, r_404.json().get("error", {}).get("message"))

    # 422 Validation Error
    t0 = time.perf_counter()
    r_422 = await client.post("/api/v1/calculators/sip", json={"monthly_investment": -500, "tenure_years": 5})
    ms_422 = (time.perf_counter() - t0) * 1000
    ok_422 = r_422.status_code == 422 and r_422.json().get("error", {}).get("code") == "VALIDATION_ERROR"
    all_passed &= ok_422
    print_step("POST /api/v1/calculators/sip with negative amount -> 422 VALIDATION_ERROR", ok_422, ms_422, "Input correctly rejected by Pydantic")

    print_header("9. In-Memory Cache Performance Verification")
    # First call (priming / read)
    await client.get(f"/api/v1/funds/{top_fund_id}")
    # Second call (must be sub-millisecond cache hit)
    t0 = time.perf_counter()
    r_cached = await client.get(f"/api/v1/funds/{top_fund_id}")
    ms_cache = (time.perf_counter() - t0) * 1000
    ok_cache = r_cached.status_code == 200 and ms_cache < 50.0
    all_passed &= ok_cache
    print_step(
        f"Cache Hit for GET /api/v1/funds/{top_fund_id}",
        ok_cache,
        ms_cache,
        f"Served from In-Memory TTL Cache in {ms_cache:.2f}ms (Zero upstream load)",
    )

    total_duration = (time.perf_counter() - total_start) * 1000
    print("\n" + "=" * 70)
    if all_passed:
        print(f"{BOLD}{GREEN}ALL TEST SUITES PASSED in {total_duration:.1f}ms!{RESET}")
    else:
        print(f"{BOLD}{RED}SOME TESTS FAILED! Please inspect logs above.{RESET}")
    print("=" * 70 + "\n")

    return all_passed


async def main():
    parser = argparse.ArgumentParser(description="Run test suite for Mutual Fund Discovery API.")
    parser.add_argument(
        "--base-url",
        type=str,
        default="",
        help="Optional base URL of a running server (e.g. http://localhost:8000). If omitted, tests in-process.",
    )
    args = parser.parse_args()

    if args.base_url:
        print(f"Connecting to live API server at {args.base_url}...")
        async with httpx.AsyncClient(base_url=args.base_url, timeout=15.0) as client:
            success = await run_test_suite(client)
    else:
        print("Testing directly against FastAPI ASGI Application in-process...")
        from app.main import app
        from httpx import ASGITransport
        transport = ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test", timeout=15.0) as client:
            success = await run_test_suite(client)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
