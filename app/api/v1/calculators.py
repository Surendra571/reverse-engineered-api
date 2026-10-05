"""Financial Calculator Endpoints."""

from fastapi import APIRouter, Depends, status
from app.services.fund_service import FundService
from app.api.deps import get_fund_service
from app.models.domain import SIPProjectionResult
from app.models.request import SIPCalculatorRequest
from app.models.response import ApiResponse

router = APIRouter(prefix="/calculators", tags=["Calculators"])


@router.post(
    "/sip",
    response_model=ApiResponse[SIPProjectionResult],
    status_code=status.HTTP_200_OK,
    summary="Calculate SIP Compounding & Projections",
    description=(
        "Projects accumulated wealth using annuity compounding. If a fund_id is provided, "
        "the calculator automatically bases expected returns on that fund's actual historical CAGR."
    ),
)
async def calculate_sip_projection(
    payload: SIPCalculatorRequest,
    service: FundService = Depends(get_fund_service),
) -> ApiResponse[SIPProjectionResult]:
    result = await service.project_sip(req=payload)
    return ApiResponse(data=result)
