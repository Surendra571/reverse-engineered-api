"""Request models with validation rules."""

from typing import Optional, Literal
from pydantic import BaseModel, Field


class SIPCalculatorRequest(BaseModel):
    """Payload for SIP calculation."""
    monthly_investment: float = Field(
        ...,
        gt=0,
        le=10_000_000,
        description="Monthly contribution in INR (min: 1, max: 10,000,000)",
        examples=[5000.0],
    )
    tenure_years: int = Field(
        ...,
        ge=1,
        le=50,
        description="Investment duration in years (min: 1, max: 50)",
        examples=[10],
    )
    expected_return_rate: Optional[float] = Field(
        None,
        ge=0.1,
        le=100.0,
        description="Expected annualized return % (CAGR). If omitted, can be derived from fund_id.",
        examples=[12.0],
    )
    fund_id: Optional[str] = Field(
        None,
        min_length=3,
        max_length=150,
        pattern=r"^[a-z0-9\-]+$",
        description="Optional fund scheme slug to dynamically benchmark CAGR against.",
        examples=["parag-parikh-long-term-value-fund-direct-growth"],
    )
