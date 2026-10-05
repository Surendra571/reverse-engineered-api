# Mutual Fund Intelligence API Facade

A production-grade, reverse-engineered API facade providing structured mutual fund discovery, portfolio analytics, and financial compounding calculators.

Built for the **Razorpay Forward-Deployed Engineer (Agent Studio) Technical Assignment**.

---

## 1. Project Context & Objectives

The assignment requires selecting a website without a public API, reverse-engineering its public functionality into an enterprise-grade API, submitting a working test script, and detailing the solution's limitations alongside an appropriate long-term fix.

* **Target Website**: [Groww India](https://groww.in)
* **Scope**: Public Indian Mutual Funds Catalog, Search, Portfolio Holdings, and Compounding Analytics.
* **Compliance & Boundaries**:
  - Uses **only publicly accessible information**.
  - **Zero bypass** of authentication, paywalls, or CAPTCHA.
  - **Zero access** to private user data, accounts, orders, or portfolios.
  - Operates strictly with read-only public endpoints backed by an in-memory TTL caching tier to minimize upstream load.

---

## 2. Architecture & Design Principles

The application is structured using the **Hexagonal / Ports-and-Adapters** architectural pattern:

```text
reverse-engineered-api/
├── app/
│   ├── main.py                     # Application factory, lifespan, CORS, middleware
│   ├── api/
│   │   ├── deps.py                 # Dependency injection providers (Ports & Adapters)
│   │   └── v1/
│   │       ├── router.py           # v1 aggregation router
│   │       ├── funds.py            # Search, explore, categories, and fund detail routes
│   │       └── calculators.py      # Financial compounding & SIP projection routes
│   ├── services/
│   │   ├── fund_service.py         # Business domain orchestration & caching
│   │   └── calculator_service.py   # Pure financial mathematics (annuity compounding)
│   ├── adapters/
│   │   ├── base.py                 # Abstract Base Class: FundDataProvider (Port)
│   │   └── groww_adapter.py        # Concrete implementation targeting Groww (Adapter)
│   ├── parsers/
│   │   ├── groww_json_parser.py    # Resilient JSON normalizer (handles nested schemas)
│   │   └── html_fallback_parser.py # BeautifulSoup parser for Next.js SSR hydration fallback
│   ├── models/
│   │   ├── domain.py               # Pure domain models (FundDetail, Holding, Returns)
│   │   ├── request.py              # Pydantic input validation models
│   │   └── response.py             # Standardized response envelopes (ApiResponse, PaginatedResponse)
│   └── core/
│       ├── config.py               # Pydantic settings with APP_ env prefix
│       ├── exceptions.py           # Domain exception hierarchy
│       ├── handlers.py             # Global exception handlers (mapping to 404, 422, 502, 503)
│       ├── logging.py              # Structured JSON logging
│       ├── cache.py                # Thread-safe in-memory LRU cache with TTL
│       └── http_client.py          # Managed httpx.AsyncClient with connection pooling
│
├── tests/
│   ├── conftest.py                 # Fixtures, test client, and upstream mocks
│   ├── unit/
│   │   ├── test_calculator.py      # Compounding formulas & boundary conditions
│   │   ├── test_parsers.py         # JSON and HTML fallback parsers
│   │   └── test_validation.py      # Pydantic input validators
│   └── integration/
│       └── test_api_routes.py      # Mocked end-to-end API integration tests (respx)
│
├── scripts/
│   └── test_api.py                 # Comprehensive CLI test script (dual in-process / live)
├── Dockerfile                      # Multi-stage lightweight Docker build
├── requirements.txt                # Pinned dependencies
├── pytest.ini                      # Pytest asyncio configuration
└── README.md
```

### Key Highlights:
1. **Isolated Upstream Coupling**: Website-specific paths, headers, and parsing are isolated inside `adapters/groww_adapter.py` and `parsers/groww_json_parser.py`.
2. **Swappable Implementation**: If an official AMFI or partner API is provided, only a new adapter implementing `FundDataProvider` needs to be created. Domain services, controllers, and tests remain untouched.
3. **In-Memory TTL Caching**: Since Mutual Fund NAVs update only once per business day post 9:00 PM IST, search (15m), explore (30m), and fund profiles (2h) are cached locally, delivering sub-2ms response times and shielding the upstream host.
4. **Resilient Network Policies**: Built on `httpx.AsyncClient` with connection pooling, exponential backoff (2 retries on 5xx/network errors), and strict non-retrying on 4xx client errors.

---

## 3. API Specification

### Core Endpoints

| HTTP Method | Route | Description |
| :--- | :--- | :--- |
| `GET` | `/health` | Service health status and upstream reachability check |
| `GET` | `/api/v1/funds/search?q={query}&limit={10}` | Autocomplete search across mutual fund schemes |
| `GET` | `/api/v1/funds/explore?category={Equity}&sort_by={returns_3y}` | Screen and paginate catalog by asset class and return horizons |
| `GET` | `/api/v1/funds/categories` | Metadata listing supported categories, subcategories, and sort keys |
| `GET` | `/api/v1/funds/{fund_id}` | Complete fund profile: NAV, AUM, managers, and top 20 portfolio holdings |
| `POST`| `/api/v1/calculators/sip` | SIP future value compounding (supports dynamic scheme CAGR benchmarking) |

### Convenience Route Aliases (Assignment Compatibility)
* `GET /api/search?q=<query>` $\rightarrow$ Maps to `/api/v1/funds/search`
* `GET /api/items/{id}` $\rightarrow$ Maps to `/api/v1/funds/{fund_id}`
* `GET /api/categories` $\rightarrow$ Maps to `/api/v1/funds/categories`

---

## 4. Quickstart & Local Setup

### Prerequisites
- Python 3.12+
- `pip`

### Installation
```bash
# 1. Clone repository and navigate to folder
cd reverse-engineered-api

# 2. Install dependencies
pip install -r requirements.txt

# 3. (Optional) Configure environment variables
cp .env.example .env
```

### Running the API Server
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
Interactive API Documentation will be available at:
* Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)
* ReDoc: [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

## 5. Verification & Testing

### A. Run Complete Pytest Suite (Unit & Integration)
```bash
pytest -v
```
*Executes all 27 tests covering unit math, schema parsing, validation rules, and mocked API routes.*

### B. Run Standalone Reviewer CLI Script
The test script runs in **dual mode**:
```bash
# Mode 1: Directly in-process against ASGI app (no running server needed!)
python scripts/test_api.py

# Mode 2: Against a running server instance
python scripts/test_api.py --base-url http://localhost:8000
```

---

## 6. Docker Deployment

```bash
# Build Docker image
docker build -t mutual-fund-api:latest .

# Run container
docker run -d --name mutual-fund-api -p 8000:8000 mutual-fund-api:latest

# Check health
curl http://localhost:8000/health
```

---

## 7. Solution Limitations & Long-Term Production Fix

### Current Solution Limitations

1. **Unannounced Upstream Schema Changes**:
   * *Limitation*: Because Groww’s internal microservices are designed for their own web frontend, fields or endpoint paths (e.g., `/v4/scheme/...` migrating to `/v5/`) can shift without deprecation notices.
   * *Current Mitigation*: The parser implements defensive type-checking (e.g., accommodating both list and dict structures for `return_stats`) and raises sanitized `502 Bad Gateway` errors rather than leaking tracebacks.
2. **Cloudflare WAF / IP Rate Limits**:
   * *Limitation*: High-concurrency automated bursts from a single IP could trigger Cloudflare anti-bot verification or temporary 403/429 status codes.
   * *Current Mitigation*: Aggressive in-memory TTL caching prevents redundant requests, and backoff handlers respect `Retry-After` headers.
3. **No Real-Time Intraday NAVs**:
   * *Limitation*: Mutual fund NAVs in India are computed by AMCs only at the close of every trading day. This API is an end-of-day intelligence feed, not a tick-by-tick market feed.

### Appropriate Long-Term Production Fix

For an enterprise deployment at Razorpay scale, the long-term production solution involves transitioning from reverse-engineered facades to institutional financial rails:

```text
               ┌─────────────────────────────────────┐
               │    FundService (Business Logic)     │
               └──────────────────┬──────────────────┘
                                  │ Calls abstract interface:
                                  ▼
                 «interface» FundDataProvider (adapters/base.py)
                                  ▲
        ┌─────────────────────────┴─────────────────────────┐
        │                                                   │
  (Current Prototype)                                 (Long-Term Production)
┌───────────────────────┐                           ┌───────────────────────────┐
│   GrowwWebAdapter     │                           │   OfficialAmfiAdapter     │
│ (Reverse-Engineered)  │                           │   (AMFI Daily Data Feeds) │
└───────────────────────┘                           └─────────────┬─────────────┘
                                                                  │
                                                    ┌─────────────┴─────────────┐
                                                    │  BSE StAR MF / NSE NMF II │
                                                    │  Morningstar Institutional│
                                                    └───────────────────────────┘
```

1. **Direct AMFI Ingestion Pipeline**:
   * AMFI publishes authoritative end-of-day NAV feeds at `amfiindia.com/spages/NAVAll.txt`.
   * A scheduled batch service (cron/worker) can ingest this feed daily at 9:30 PM IST, parse NAV values, and persist them into a managed PostgreSQL or TimescaleDB instance.
2. **Institutional Data Vendor Partnership**:
   * Integrate with providers like **Morningstar**, **Refinitiv**, or **Value Research** for deep portfolio disclosures (sector weightings, Sharpe/Sortino ratios, risk grades) via enterprise SLAs.
3. **Execution Rail Integration (BSE StAR MF / NSE NMF II)**:
   * When moving beyond data discovery to financial execution (e.g., automated SIP investments via Razorpay mandates), integrate directly with BSE StAR MF or NSE NMF II B2B transaction APIs.
4. **Zero-Downtime Transition**:
   * Because of this codebase’s Ports-and-Adapters design, switching to the official feed requires only implementing an `OfficialAmfiAdapter` in `app/adapters/` and updating the dependency injection in `app/api/deps.py`.
