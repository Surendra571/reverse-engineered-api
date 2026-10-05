"""Domain entities for Mutual Fund Discovery and Analysis."""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class FundSearchResult(BaseModel):
    """Clean model for search autocomplete result."""
    id: str = Field(..., description="Unique scheme slug identifier")
    scheme_code: Optional[str] = Field(None, description="AMFI numeric scheme code")
    name: str = Field(..., description="Official scheme title")
    entity_type: str = Field("Scheme", description="Type of asset")


class FundReturns(BaseModel):
    """Historical annualized returns across standard horizons."""
    return_1d: Optional[float] = Field(None, description="1-day return %")
    return_1y: Optional[float] = Field(None, description="1-year return %")
    return_3y: Optional[float] = Field(None, description="3-year return %")
    return_5y: Optional[float] = Field(None, description="5-year return %")


class FundSummary(BaseModel):
    """Summary representation for catalog browsing/screening."""
    id: str
    scheme_code: Optional[str] = None
    name: str
    fund_house: Optional[str] = None
    category: Optional[str] = None
    sub_category: Optional[str] = None
    risk_rating: Optional[str] = None
    nav: Optional[float] = None
    aum_in_crores: Optional[float] = None
    expense_ratio: Optional[float] = None
    returns: FundReturns
    min_sip_investment: Optional[float] = None


class FundHolding(BaseModel):
    """Individual stock/security asset allocation within the fund portfolio."""
    company_name: str
    sector: Optional[str] = None
    allocation_percentage: Optional[float] = None
    instrument_name: Optional[str] = None


class FundManager(BaseModel):
    """Fund manager profile."""
    name: str
    experience: Optional[str] = None
    description: Optional[str] = None


class FundDetail(BaseModel):
    """Complete fund profile with portfolio holdings and manager details."""
    id: str
    scheme_code: Optional[str] = None
    name: str
    fund_house: Optional[str] = None
    category: Optional[str] = None
    sub_category: Optional[str] = None
    risk_level: Optional[str] = None
    benchmark_name: Optional[str] = None
    nav: Optional[float] = None
    nav_date: Optional[str] = None
    aum_in_crores: Optional[float] = None
    expense_ratio: Optional[float] = None
    exit_load: Optional[str] = None
    stamp_duty: Optional[str] = None
    lock_in_period: Optional[str] = None
    min_sip_investment: Optional[float] = None
    min_lumpsum_investment: Optional[float] = None
    returns: FundReturns
    fund_managers: List[FundManager] = Field(default_factory=list)
    top_holdings: List[FundHolding] = Field(default_factory=list)


class SIPProjectionResult(BaseModel):
    """Result of compounding wealth calculation."""
    monthly_investment: float
    tenure_years: int
    annual_expected_return_rate: float
    total_invested_amount: float
    estimated_returns: float
    total_future_value: float
    benchmark_fund_id: Optional[str] = None
    benchmark_fund_name: Optional[str] = None


class CategoryOption(BaseModel):
    key: str
    display_name: str


class CategoriesMetadata(BaseModel):
    """Supported filter dimensions and categories."""
    categories: List[CategoryOption]
    sub_categories: List[CategoryOption]
    sort_options: List[CategoryOption]
