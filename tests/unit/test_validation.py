"""Unit tests for Pydantic request models and input validation."""

import pytest
from pydantic import ValidationError
from app.models.request import SIPCalculatorRequest


def test_valid_sip_request():
    req = SIPCalculatorRequest(
        monthly_investment=5000.0,
        tenure_years=10,
        expected_return_rate=12.5,
    )
    assert req.monthly_investment == 5000.0
    assert req.tenure_years == 10
    assert req.expected_return_rate == 12.5


def test_invalid_negative_monthly_investment():
    with pytest.raises(ValidationError):
        SIPCalculatorRequest(
            monthly_investment=-100.0,
            tenure_years=10,
        )


def test_invalid_zero_tenure():
    with pytest.raises(ValidationError):
        SIPCalculatorRequest(
            monthly_investment=5000.0,
            tenure_years=0,
        )


def test_invalid_excessive_tenure():
    with pytest.raises(ValidationError):
        SIPCalculatorRequest(
            monthly_investment=5000.0,
            tenure_years=100,
        )


def test_invalid_fund_id_pattern():
    with pytest.raises(ValidationError):
        SIPCalculatorRequest(
            monthly_investment=5000.0,
            tenure_years=10,
            fund_id="Invalid Fund Name! with special chars",
        )
