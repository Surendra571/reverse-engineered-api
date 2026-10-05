"""Calculator Service for financial computations and wealth projections."""

from typing import Optional
from app.models.domain import SIPProjectionResult


class CalculatorService:
    """Provides pure financial math and compounding projections."""

    @staticmethod
    def calculate_sip(
        monthly_investment: float,
        tenure_years: int,
        annual_return_rate: float,
        benchmark_fund_id: Optional[str] = None,
        benchmark_fund_name: Optional[str] = None,
    ) -> SIPProjectionResult:
        """
        Calculates SIP Future Value using the standard financial annuity formula:
        FV = P * [((1 + i)^n - 1) / i] * (1 + i)
        Where:
            P = Monthly investment
            i = Monthly periodic interest rate = (annual_rate / 12) / 100
            n = Total number of months = tenure_years * 12
        """
        n = tenure_years * 12
        total_invested = round(monthly_investment * n, 2)

        if annual_return_rate <= 0:
            total_future_value = total_invested
            estimated_returns = 0.0
        else:
            i = (annual_return_rate / 100.0) / 12.0
            # Formula for annuity due (payments at start of month)
            compound_factor = ((1.0 + i) ** n - 1.0) / i
            total_future_value = round(monthly_investment * compound_factor * (1.0 + i), 2)
            estimated_returns = round(total_future_value - total_invested, 2)

        return SIPProjectionResult(
            monthly_investment=round(monthly_investment, 2),
            tenure_years=tenure_years,
            annual_expected_return_rate=round(annual_return_rate, 2),
            total_invested_amount=total_invested,
            estimated_returns=estimated_returns,
            total_future_value=total_future_value,
            benchmark_fund_id=benchmark_fund_id,
            benchmark_fund_name=benchmark_fund_name,
        )
