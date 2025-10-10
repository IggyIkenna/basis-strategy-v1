"""
Capital management routes for deposit and withdrawal operations.
"""

from datetime import datetime
from typing import Dict, Any

from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, Field

from basis_strategy_v1.api.models import ApiResponse
from basis_strategy_v1.api.routes.auth import verify_token

router = APIRouter()


class DepositRequest(BaseModel):
    amount: float = Field(..., gt=0, description="Amount to deposit")
    currency: str = Field(default="USDT", description="Currency for deposit")
    share_class: str = Field(default="usdt", description="Share class for deposit")
    source: str = Field(default="manual", description="Source of deposit")


class WithdrawRequest(BaseModel):
    amount: float = Field(..., gt=0, description="Amount to withdraw")
    currency: str = Field(default="USDT", description="Currency for withdrawal")
    share_class: str = Field(default="usdt", description="Share class for withdrawal")
    withdrawal_type: str = Field(default="fast", description="Withdrawal type: fast or slow")


class CapitalResponse(BaseModel):
    id: str
    amount: float
    currency: str
    share_class: str
    status: str
    new_total_equity: float
    timestamp: str


@router.post("/deposit", response_model=ApiResponse[CapitalResponse])
async def deposit_capital(
    request: DepositRequest,
    token_payload: Dict[str, Any] = Depends(verify_token)
):
    """
    Queue a capital deposit request.
    
    - **amount**: Amount to deposit (must be > 0)
    - **currency**: Currency for deposit (default: USDT)
    - **share_class**: Share class for deposit (default: usdt)
    - **source**: Source of deposit (default: manual)
    
    Returns confirmation of queued deposit request.
    """
    # Validate amount
    if request.amount <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Deposit amount must be greater than 0"
        )
    
    # Validate share class
    if request.share_class not in ["usdt", "eth"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Share class must be either 'usdt' or 'eth'"
        )
    
    # Generate request ID
    request_id = f"deposit_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{int(request.amount)}"
    
    # TODO: In a real implementation, this would:
    # 1. Queue the deposit request for next timestep processing
    # 2. Trigger rebalancing after deposit
    # 3. Update total equity tracking
    # 4. Log the transaction
    
    # For MVP, simulate the response
    new_total_equity = 100000.0 + request.amount  # Mock current equity + deposit
    
    return ApiResponse(
        success=True,
        data=CapitalResponse(
            id=request_id,
            amount=request.amount,
            currency=request.currency,
            share_class=request.share_class,
            status="queued",
            new_total_equity=new_total_equity,
            timestamp=datetime.now().isoformat()
        ),
        message=f"Deposit of {request.amount} {request.currency} queued successfully"
    )


@router.post("/withdraw", response_model=ApiResponse[CapitalResponse])
async def withdraw_capital(
    request: WithdrawRequest,
    token_payload: Dict[str, Any] = Depends(verify_token)
):
    """
    Queue a capital withdrawal request.
    
    - **amount**: Amount to withdraw (must be > 0)
    - **currency**: Currency for withdrawal (default: USDT)
    - **share_class**: Share class for withdrawal (default: usdt)
    - **withdrawal_type**: Withdrawal type - 'fast' (from reserves) or 'slow' (unwind positions)
    
    Returns confirmation of queued withdrawal request.
    """
    # Validate amount
    if request.amount <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Withdrawal amount must be greater than 0"
        )
    
    # Validate share class
    if request.share_class not in ["usdt", "eth"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Share class must be either 'usdt' or 'eth'"
        )
    
    # Validate withdrawal type
    if request.withdrawal_type not in ["fast", "slow"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Withdrawal type must be either 'fast' or 'slow'"
        )
    
    # Generate request ID
    request_id = f"withdraw_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{int(request.amount)}"
    
    # TODO: In a real implementation, this would:
    # 1. Check available balance for withdrawal
    # 2. Queue the withdrawal request for next timestep processing
    # 3. For 'fast' withdrawals: withdraw from available reserves
    # 4. For 'slow' withdrawals: unwind positions to free up capital
    # 5. Trigger rebalancing after withdrawal
    # 6. Update total equity tracking
    # 7. Log the transaction
    
    # For MVP, simulate the response
    new_total_equity = 100000.0 - request.amount  # Mock current equity - withdrawal
    
    return ApiResponse(
        success=True,
        data=CapitalResponse(
            id=request_id,
            amount=request.amount,
            currency=request.currency,
            share_class=request.share_class,
            status="queued",
            new_total_equity=new_total_equity,
            timestamp=datetime.now().isoformat()
        ),
        message=f"Withdrawal of {request.amount} {request.currency} queued successfully"
    )

