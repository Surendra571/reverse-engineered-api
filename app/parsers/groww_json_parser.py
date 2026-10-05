"""Parser and normalizer for Groww JSON API payloads."""

from typing import List, Dict, Any, Optional
from app.models.domain import (
    FundSearchResult,
    FundSummary,
    FundDetail,
    FundHolding,
    FundManager,
    FundReturns,
)
from app.core.exceptions import MalformedUpstreamDataError
from app.core.logging import logger


class GrowwJsonParser:
    """Extracts, validates, and normalizes raw JSON from Groww internal services."""

    @staticmethod
    def parse_search_results(raw_json: Dict[str, Any]) -> List[FundSearchResult]:
        """Parses entity search/autocomplete response."""
        try:
            items = raw_json.get("content", [])
            results: List[FundSearchResult] = []
            for item in items:
                entity_type = item.get("entity_type", "Scheme")
                search_id = item.get("search_id") or item.get("id")
                title = item.get("title")

                if search_id and title:
                    results.append(
                        FundSearchResult(
                            id=search_id,
                            scheme_code=str(item.get("scheme_code")) if item.get("scheme_code") else None,
                            name=title,
                            entity_type=entity_type,
                        )
                    )
            return results
        except Exception as exc:
            logger.error("Failed to parse search results: %s", str(exc))
            raise MalformedUpstreamDataError("Invalid search response format from upstream", details={"raw": str(raw_json)[:300]}) from exc

    @staticmethod
    def parse_explore_results(raw_json: Dict[str, Any]) -> tuple[List[FundSummary], int]:
        """Parses catalog screener / filter response returning (funds, total_count)."""
        try:
            total_results = raw_json.get("total_results", 0)
            items = raw_json.get("content", [])
            funds: List[FundSummary] = []

            for item in items:
                search_id = item.get("search_id") or item.get("id")
                name = item.get("scheme_name") or item.get("fund_name") or item.get("title")
                if not search_id or not name:
                    continue

                returns = FundReturns(
                    return_1d=item.get("return1d"),
                    return_1y=item.get("return1y"),
                    return_3y=item.get("return3y"),
                    return_5y=item.get("return5y"),
                )

                funds.append(
                    FundSummary(
                        id=search_id,
                        scheme_code=str(item.get("scheme_code")) if item.get("scheme_code") else None,
                        name=name,
                        fund_house=item.get("fund_house") or item.get("amc"),
                        category=item.get("category"),
                        sub_category=item.get("sub_category"),
                        risk_rating=str(item.get("risk_rating") or item.get("risk") or ""),
                        nav=item.get("nav"),
                        aum_in_crores=item.get("aum"),
                        expense_ratio=item.get("expense_ratio"),
                        returns=returns,
                        min_sip_investment=item.get("min_sip_investment"),
                    )
                )

            return funds, total_results
        except Exception as exc:
            logger.error("Failed to parse explore results: %s", str(exc))
            raise MalformedUpstreamDataError("Invalid explore response format from upstream", details={"error": str(exc)}) from exc

    @staticmethod
    def parse_fund_detail(raw_json: Dict[str, Any], scheme_id: str) -> FundDetail:
        """Parses comprehensive scheme profile."""
        try:
            if not raw_json or not isinstance(raw_json, dict):
                raise MalformedUpstreamDataError("Empty or non-dictionary scheme detail response")

            name = raw_json.get("scheme_name") or raw_json.get("fund_name")
            if not name:
                raise MalformedUpstreamDataError("Missing scheme_name in detail payload")

            # Extract holdings safely
            raw_holdings = raw_json.get("holdings", [])
            holdings: List[FundHolding] = []
            if isinstance(raw_holdings, list):
                for h in raw_holdings[:20]:  # Top 20 holdings
                    if isinstance(h, dict):
                        c_name = h.get("company_name")
                        if c_name:
                            holdings.append(
                                FundHolding(
                                    company_name=c_name,
                                    sector=h.get("sector_name"),
                                    allocation_percentage=h.get("corpus_per"),
                                    instrument_name=h.get("nature_name"),
                                )
                            )

            # Extract managers safely
            raw_managers = raw_json.get("fund_manager_details", [])
            managers: List[FundManager] = []
            if isinstance(raw_managers, list):
                for m in raw_managers:
                    if isinstance(m, dict):
                        m_name = m.get("fund_manager") or m.get("name")
                        if m_name:
                            managers.append(
                                FundManager(
                                    name=m_name,
                                    experience=m.get("experience"),
                                    description=m.get("description"),
                                )
                            )

            # Extract return stats: can be list or dict
            raw_stats = raw_json.get("return_stats")
            stats_dict: Dict[str, Any] = {}
            if isinstance(raw_stats, list) and len(raw_stats) > 0 and isinstance(raw_stats[0], dict):
                stats_dict = raw_stats[0]
            elif isinstance(raw_stats, dict):
                stats_dict = raw_stats

            returns = FundReturns(
                return_1d=stats_dict.get("return1d") or raw_json.get("return1d"),
                return_1y=stats_dict.get("return1y") or raw_json.get("return1y"),
                return_3y=stats_dict.get("return3y") or raw_json.get("return3y"),
                return_5y=stats_dict.get("return5y") or raw_json.get("return5y"),
            )

            return FundDetail(
                id=scheme_id,
                scheme_code=str(raw_json.get("scheme_code")) if raw_json.get("scheme_code") else None,
                name=name,
                fund_house=raw_json.get("fund_house") or raw_json.get("amc"),
                category=raw_json.get("category"),
                sub_category=raw_json.get("sub_category"),
                risk_level=str(raw_json.get("risk") or raw_json.get("risk_rating") or ""),
                benchmark_name=raw_json.get("benchmark_name") or raw_json.get("benchmark"),
                nav=raw_json.get("nav"),
                nav_date=raw_json.get("nav_date"),
                aum_in_crores=raw_json.get("aum"),
                expense_ratio=raw_json.get("expense_ratio"),
                exit_load=raw_json.get("exit_load"),
                stamp_duty=str(raw_json.get("stamp_duty")) if raw_json.get("stamp_duty") else None,
                lock_in_period=str(raw_json.get("lock_in")) if raw_json.get("lock_in") else None,
                min_sip_investment=raw_json.get("min_sip_investment"),
                min_lumpsum_investment=raw_json.get("min_investment_amount"),
                returns=returns,
                fund_managers=managers,
                top_holdings=holdings,
            )
        except MalformedUpstreamDataError:
            raise
        except Exception as exc:
            logger.error("Failed to parse fund detail: %s", str(exc))
            raise MalformedUpstreamDataError(f"Error parsing scheme detail for '{scheme_id}'", details={"error": str(exc)}) from exc
