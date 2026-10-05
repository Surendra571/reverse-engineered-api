"""Integration tests for FastAPI routes covering all 15 required categories with mocked upstream responses."""

import pytest
import respx
import httpx
from app.core.config import settings


# 1. Health check
@pytest.mark.asyncio
async def test_health_check(async_client: httpx.AsyncClient):
    with respx.mock(base_url=settings.UPSTREAM_BASE_URL) as respx_mock:
        respx_mock.get("/v1/api/search/v1/entity").mock(
            return_value=httpx.Response(200, json={"content": []})
        )
        response = await async_client.get("/health")
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "ok"
        assert body["upstream_status"] == "healthy"


# 2. Successful search
@pytest.mark.asyncio
async def test_successful_search(async_client: httpx.AsyncClient, mock_search_response):
    with respx.mock(base_url=settings.UPSTREAM_BASE_URL) as respx_mock:
        respx_mock.get("/v1/api/search/v1/entity").mock(
            return_value=httpx.Response(200, json=mock_search_response)
        )
        response = await async_client.get("/api/v1/funds/search?q=parag+parikh&limit=5")
        assert response.status_code == 200
        body = response.json()
        assert body["success"] is True
        assert len(body["data"]) > 0
        assert body["data"][0]["name"] == "Parag Parikh Flexi Cap Fund"


# 3. Empty search
@pytest.mark.asyncio
async def test_empty_search(async_client: httpx.AsyncClient):
    with respx.mock(base_url=settings.UPSTREAM_BASE_URL) as respx_mock:
        respx_mock.get("/v1/api/search/v1/entity").mock(
            return_value=httpx.Response(200, json={"content": []})
        )
        response = await async_client.get("/api/v1/funds/search?q=nonexistentfundquery999")
        assert response.status_code == 200
        body = response.json()
        assert body["success"] is True
        assert body["data"] == []


# 4. Invalid search parameters
@pytest.mark.asyncio
async def test_invalid_search_parameters(async_client: httpx.AsyncClient):
    # Query length < 2 characters must return 422
    response = await async_client.get("/api/v1/funds/search?q=a")
    assert response.status_code == 422
    body = response.json()
    assert body["success"] is False
    assert body["error"]["code"] == "VALIDATION_ERROR"


# 5. Valid item lookup
@pytest.mark.asyncio
async def test_valid_item_lookup(async_client: httpx.AsyncClient, mock_detail_response):
    with respx.mock(base_url=settings.UPSTREAM_BASE_URL) as respx_mock:
        respx_mock.get("/v1/api/data/mf/web/v4/scheme/search/parag-parikh-long-term-value-fund-direct-growth").mock(
            return_value=httpx.Response(200, json=mock_detail_response, headers={"content-type": "application/json"})
        )
        response = await async_client.get("/api/v1/funds/parag-parikh-long-term-value-fund-direct-growth")
        assert response.status_code == 200
        body = response.json()
        assert body["success"] is True
        assert body["data"]["id"] == "parag-parikh-long-term-value-fund-direct-growth"
        assert body["data"]["name"] == "Parag Parikh Flexi Cap Fund"
        assert body["data"]["nav"] == 86.42
        assert len(body["data"]["top_holdings"]) == 2


# 6. Invalid item ID
@pytest.mark.asyncio
async def test_invalid_item_id(async_client: httpx.AsyncClient):
    # Special characters outside ^[a-z0-9\-]+$ must return 422
    response = await async_client.get("/api/v1/funds/invalid!id@with$chars")
    assert response.status_code == 422
    body = response.json()
    assert body["success"] is False
    assert body["error"]["code"] == "VALIDATION_ERROR"


# 7. Missing item
@pytest.mark.asyncio
async def test_missing_item(async_client: httpx.AsyncClient):
    with respx.mock(base_url=settings.UPSTREAM_BASE_URL) as respx_mock:
        respx_mock.get("/v1/api/data/mf/web/v4/scheme/search/non-existent-fund-slug-xyz").mock(
            return_value=httpx.Response(404, text="Not Found")
        )
        response = await async_client.get("/api/v1/funds/non-existent-fund-slug-xyz")
        assert response.status_code == 404
        body = response.json()
        assert body["success"] is False
        assert body["error"]["code"] == "NOT_FOUND"


# 8. Categories endpoint
@pytest.mark.asyncio
async def test_categories_endpoint(async_client: httpx.AsyncClient):
    response = await async_client.get("/api/v1/funds/categories")
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert "categories" in body["data"]
    assert "sub_categories" in body["data"]
    assert "sort_options" in body["data"]
    assert len(body["data"]["categories"]) >= 3


# 9. Upstream website failure
@pytest.mark.asyncio
async def test_upstream_website_failure(async_client: httpx.AsyncClient):
    with respx.mock(base_url=settings.UPSTREAM_BASE_URL) as respx_mock:
        respx_mock.get("/v1/api/search/v1/entity").mock(
            return_value=httpx.Response(500, text="Internal Server Error")
        )
        response = await async_client.get("/api/v1/funds/search?q=test")
        assert response.status_code == 503
        body = response.json()
        assert body["success"] is False
        assert body["error"]["code"] == "UPSTREAM_UNAVAILABLE"
        assert response.headers.get("retry-after") == "30"


# 10. Timeout handling
@pytest.mark.asyncio
async def test_timeout_handling(async_client: httpx.AsyncClient):
    with respx.mock(base_url=settings.UPSTREAM_BASE_URL) as respx_mock:
        respx_mock.get("/v1/api/search/v1/entity").mock(
            side_effect=httpx.ReadTimeout("Upstream read timed out")
        )
        response = await async_client.get("/api/v1/funds/search?q=test")
        assert response.status_code == 503
        body = response.json()
        assert body["success"] is False
        assert body["error"]["code"] == "UPSTREAM_UNAVAILABLE"


# 11. Malformed upstream response
@pytest.mark.asyncio
async def test_malformed_upstream_response(async_client: httpx.AsyncClient):
    with respx.mock(base_url=settings.UPSTREAM_BASE_URL) as respx_mock:
        respx_mock.get("/v1/api/data/mf/web/v4/scheme/search/test-scheme").mock(
            return_value=httpx.Response(200, text="invalid-json-content{{{", headers={"content-type": "application/json"})
        )
        response = await async_client.get("/api/v1/funds/test-scheme")
        assert response.status_code == 502
        body = response.json()
        assert body["success"] is False
        assert body["error"]["code"] == "BAD_GATEWAY"


# 12. API response schema
@pytest.mark.asyncio
async def test_api_response_schema(async_client: httpx.AsyncClient, mock_search_response):
    with respx.mock(base_url=settings.UPSTREAM_BASE_URL) as respx_mock:
        respx_mock.get("/v1/api/search/v1/entity").mock(
            return_value=httpx.Response(200, json=mock_search_response)
        )
        response = await async_client.get("/api/v1/funds/search?q=parag")
        assert response.status_code == 200
        body = response.json()
        # Verify envelope structure
        assert "success" in body and isinstance(body["success"], bool)
        assert "data" in body
        assert "error" in body
        # Verify data item schema
        item = body["data"][0]
        assert "id" in item
        assert "name" in item
        assert "entity_type" in item


# 13. HTTP status codes
@pytest.mark.asyncio
async def test_http_status_codes(async_client: httpx.AsyncClient, mock_search_response):
    with respx.mock(base_url=settings.UPSTREAM_BASE_URL) as respx_mock:
        # 200 OK
        respx_mock.get("/v1/api/search/v1/entity").mock(return_value=httpx.Response(200, json=mock_search_response))
        r200 = await async_client.get("/api/v1/funds/search?q=parag")
        assert r200.status_code == 200

        # 404 Not Found
        respx_mock.get("/v1/api/data/mf/web/v4/scheme/search/missing-scheme").mock(return_value=httpx.Response(404, text="Not Found"))
        r404 = await async_client.get("/api/v1/funds/missing-scheme")
        assert r404.status_code == 404

        # 422 Unprocessable Entity
        r422 = await async_client.get("/api/v1/funds/search?q=x")
        assert r422.status_code == 422

        # 503 Service Unavailable
        respx_mock.get("/v1/api/data/mf/web/v4/scheme/search/error-scheme").mock(
            return_value=httpx.Response(503, text="Service Unavailable"))
        r503 = await async_client.get("/api/v1/funds/error-scheme")
        assert r503.status_code == 503


# 14. Edge cases
@pytest.mark.asyncio
async def test_edge_cases(async_client: httpx.AsyncClient):
    # Edge case 1: 0% return rate on SIP
    r_zero = await async_client.post("/api/v1/calculators/sip", json={"monthly_investment": 1000.0, "tenure_years": 1, "expected_return_rate": 0.0})
    assert r_zero.status_code == 422  # expected_return_rate ge=0.1

    # Edge case 2: Min allowed return rate 0.1%
    r_min_rate = await async_client.post("/api/v1/calculators/sip", json={"monthly_investment": 1000.0, "tenure_years": 1, "expected_return_rate": 0.1})
    assert r_min_rate.status_code == 200
    assert r_min_rate.json()["data"]["total_future_value"] >= 12000.0

    # Edge case 3: Max boundary monthly investment
    r_max = await async_client.post("/api/v1/calculators/sip", json={"monthly_investment": 10_000_000.0, "tenure_years": 50, "expected_return_rate": 15.0})
    assert r_max.status_code == 200
    assert r_max.json()["data"]["total_future_value"] > 0


# 15. Basic end-to-end workflow
@pytest.mark.asyncio
async def test_basic_end_to_end_workflow(async_client: httpx.AsyncClient, mock_search_response, mock_detail_response):
    with respx.mock(base_url=settings.UPSTREAM_BASE_URL) as respx_mock:
        # Step A: Search for fund
        respx_mock.get("/v1/api/search/v1/entity").mock(return_value=httpx.Response(200, json=mock_search_response))
        search_res = await async_client.get("/api/v1/funds/search?q=parag+parikh")
        assert search_res.status_code == 200
        funds = search_res.json()["data"]
        assert len(funds) > 0
        selected_fund_id = funds[0]["id"]

        # Step B: Fetch details for chosen fund
        respx_mock.get(f"/v1/api/data/mf/web/v4/scheme/search/{selected_fund_id}").mock(
            return_value=httpx.Response(200, json=mock_detail_response, headers={"content-type": "application/json"})
        )
        detail_res = await async_client.get(f"/api/v1/funds/{selected_fund_id}")
        assert detail_res.status_code == 200
        detail = detail_res.json()["data"]
        assert detail["nav"] == 86.42

        # Step C: Use fund in compounding calculation
        calc_res = await async_client.post(
            "/api/v1/calculators/sip",
            json={"monthly_investment": 5000.0, "tenure_years": 5, "fund_id": selected_fund_id},
        )
        assert calc_res.status_code == 200
        calc_data = calc_res.json()["data"]
        assert calc_data["benchmark_fund_id"] == selected_fund_id
        assert calc_data["annual_expected_return_rate"] == 19.4
        assert calc_data["total_future_value"] > calc_data["total_invested_amount"]

