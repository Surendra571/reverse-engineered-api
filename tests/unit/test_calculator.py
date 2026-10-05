"""Unit tests for financial compounding and SIP calculator."""

import pytest
from app.services.calculator_service import CalculatorService


def test_sip_calculation_standard():
    """Verify standard SIP compounding against financial annuity benchmark: ₹10,000/mo at 12% over 10 years."""
    result = CalculatorService.calculate_sip(
        monthly_investment=10000.0,
        tenure_years=10,
        annual_return_rate=12.0,
    )

    assert result.monthly_investment == 10000.0
    assert result.tenure_years == 10
    assert result.annual_expected_return_rate == 12.0
    assert result.total_invested_amount == 1200000.0  # 10,000 * 120 months
    # Formula for annuity due FV: ~2,323,390.8
    assert result.total_future_value > 2300000.0
    assert result.total_future_value < 2350000.0
    assert result.estimated_returns == round(result.total_future_value - result.total_invested_amount, 2)


def test_sip_calculation_zero_percent():
    """Verify 0% return edge case results in future value equal to invested capital."""
    result = CalculatorService.calculate_sip(
        monthly_investment=5000.0,
        tenure_years=5,
        annual_return_rate=0.0,
    )

    assert result.total_invested_amount == 300000.0
    assert result.total_future_value == 300000.0
    assert result.estimated_returns == 0.0


def test_sip_calculation_one_year():
    """Verify 1-year tenure computation."""
    result = CalculatorService.calculate_sip(
        monthly_investment=1000.0,
        tenure_years=1,
        annual_return_rate=10.0,
    )

    assert result.total_invested_amount == 12000.0
    assert result.total_future_value > 12000.0
    assert result.estimated_returns > 0.0
