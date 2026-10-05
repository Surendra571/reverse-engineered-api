"""Unit tests for Groww JSON and HTML parsers."""

import pytest
from app.parsers.groww_json_parser import GrowwJsonParser
from app.parsers.html_fallback_parser import HTMLFallbackParser
from app.core.exceptions import MalformedUpstreamDataError


def test_parse_search_results_valid(mock_search_response):
    results = GrowwJsonParser.parse_search_results(mock_search_response)
    assert len(results) == 3
    assert results[0].id == "parag-parikh-long-term-value-fund-direct-growth"
    assert results[0].name == "Parag Parikh Flexi Cap Fund"
    assert results[0].scheme_code == "122639"
    assert results[0].entity_type == "Scheme"


def test_parse_search_results_empty():
    results = GrowwJsonParser.parse_search_results({"content": []})
    assert results == []


def test_parse_explore_results_valid(mock_explore_response):
    funds, total = GrowwJsonParser.parse_explore_results(mock_explore_response)
    assert total == 2
    assert len(funds) == 2
    assert funds[0].id == "bandhan-small-cap-fund-direct-growth"
    assert funds[0].name == "Bandhan Small Cap Fund Direct Growth"
    assert funds[0].returns.return_3y == 23.15
    assert funds[0].aum_in_crores == 6245.8


def test_parse_fund_detail_valid(mock_detail_response):
    detail = GrowwJsonParser.parse_fund_detail(mock_detail_response, "parag-parikh-long-term-value-fund-direct-growth")
    assert detail.id == "parag-parikh-long-term-value-fund-direct-growth"
    assert detail.name == "Parag Parikh Flexi Cap Fund"
    assert detail.scheme_code == "122639"
    assert detail.nav == 86.42
    assert len(detail.top_holdings) == 2
    assert detail.top_holdings[0].company_name == "HDFC Bank Ltd."
    assert detail.top_holdings[0].allocation_percentage == 7.82
    assert len(detail.fund_managers) == 1
    assert detail.fund_managers[0].name == "Rajeev Thakkar"
    assert detail.returns.return_3y == 19.4


def test_parse_fund_detail_malformed():
    with pytest.raises(MalformedUpstreamDataError):
        GrowwJsonParser.parse_fund_detail({}, "invalid-fund")


def test_html_fallback_parser():
    sample_html = """
    <!DOCTYPE html>
    <html>
      <head><title>Test</title></head>
      <body>
        <script id="__NEXT_DATA__" type="application/json">
          {"props": {"pageProps": {"schemeData": {"scheme_name": "Test Fund", "search_id": "test-fund"}}}}
        </script>
      </body>
    </html>
    """
    props = HTMLFallbackParser.extract_page_props(sample_html)
    assert "schemeData" in props
    assert props["schemeData"]["scheme_name"] == "Test Fund"


def test_html_fallback_parser_missing_tag():
    with pytest.raises(MalformedUpstreamDataError):
        HTMLFallbackParser.extract_next_data("<html><body>No next data</body></html>")
