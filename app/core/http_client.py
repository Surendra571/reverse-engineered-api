"""HTTP Client manager with connection pooling and timeouts."""

import httpx
from typing import Optional
from app.core.config import settings


class HTTPClientManager:
    """Manages the lifecycle of httpx.AsyncClient."""

    _client: Optional[httpx.AsyncClient] = None

    @classmethod
    def get_client(cls) -> httpx.AsyncClient:
        if cls._client is None or cls._client.is_closed:
            limits = httpx.Limits(
                max_keepalive_connections=20,
                max_connections=50,
                keepalive_expiry=30.0,
            )
            timeouts = httpx.Timeout(
                connect=settings.UPSTREAM_TIMEOUT_CONNECT,
                read=settings.UPSTREAM_TIMEOUT_READ,
                write=settings.UPSTREAM_TIMEOUT_WRITE,
                pool=settings.UPSTREAM_TIMEOUT_POOL,
            )
            cls._client = httpx.AsyncClient(
                limits=limits,
                timeout=timeouts,
                follow_redirects=True,
                headers={
                    "User-Agent": settings.UPSTREAM_USER_AGENT,
                    "Accept": "application/json, text/plain, */*",
                    "Accept-Language": "en-US,en;q=0.9",
                },
            )
        return cls._client

    @classmethod
    async def close_client(cls) -> None:
        if cls._client and not cls._client.is_closed:
            await cls._client.aclose()
            cls._client = None
