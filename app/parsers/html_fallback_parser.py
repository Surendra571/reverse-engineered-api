"""HTML Fallback Parser for extracting Next.js hydration payload using BeautifulSoup."""

import json
from typing import Optional, Dict, Any
from bs4 import BeautifulSoup
from app.core.exceptions import MalformedUpstreamDataError
from app.core.logging import logger


class HTMLFallbackParser:
    """Parses Next.js server-rendered HTML pages for embedded application state."""

    @staticmethod
    def extract_next_data(html_content: str) -> Dict[str, Any]:
        """Extracts JSON payload from <script id="__NEXT_DATA__"> element."""
        try:
            soup = BeautifulSoup(html_content, "html.parser")
            script_tag = soup.find("script", id="__NEXT_DATA__")
            if not script_tag or not script_tag.string:
                raise MalformedUpstreamDataError("No __NEXT_DATA__ script found in HTML response")

            data = json.loads(script_tag.string)
            return data
        except Exception as exc:
            logger.error("Failed to extract NEXT_DATA from HTML: %s", str(exc))
            raise MalformedUpstreamDataError("Failed to extract data from HTML fallback", details={"error": str(exc)}) from exc

    @staticmethod
    def extract_page_props(html_content: str) -> Dict[str, Any]:
        """Convenience method returning pageProps dictionary."""
        data = HTMLFallbackParser.extract_next_data(html_content)
        return data.get("props", {}).get("pageProps", {})
