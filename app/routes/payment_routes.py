from fastapi import APIRouter, HTTPException, status, Depends, Query
from app.core.auth import get_current_user
from app.db.connection import get_database
from app.services.payment_service import payment_service
from app.utils.helpers import success_response
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

router = APIRouter(prefix="/payment", tags=["Payment"])


class PaymentInitiateRequest(BaseModel):
    amount: float
    currency: str = "INR"
    purpose: str = "wallet_recharge"
    gateway: str = "razorpay"
    payment_method: str = "card"
    metadata: Optional[dict] = None


class PaymentVerifyRequest(BaseModel):
    payment_id: str
    order_id: str
    signature: Optional[str] = None
    gateway_data: Optional[Dict[str, Any]] = None


class RefundRequest(BaseModel):
    amount: Optional[float] = None
    reason: str = "customer_request"


@router.post("/initiate", response_model=dict)
async def initiate_payment(
    request: PaymentInitiateRequest,
    current_user: dict = Depends(get_current_user)
):
    """Initiate a payment transaction with multiple gateway support"""
    
    if request.amount <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Amount must be greater than 0"
        )
    
    try:
        result = await payment_service.initiate_payment(
            user_id=current_user["user_id"],
            amount=request.amount,
            currency=request.currency,
            purpose=request.purpose,
            gateway=request.gateway,
            payment_method=request.payment_method,
            metadata=request.metadata
        )
        
        return success_response(
            data=result,
            message="Payment initiated successfully"
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/verify", response_model=dict)
async def verify_payment(
    request: PaymentVerifyRequest,
    current_user: dict = Depends(get_current_user)
):
    """Verify a payment transaction with enhanced validation"""
    
    result = await payment_service.verify_payment(
        payment_id=request.payment_id,
        order_id=request.order_id,
        signature=request.signature,
        gateway_data=request.gateway_data
    )
    
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["message"]
        )
    
    return success_response(
        data=result,
        message="Payment verified successfully"
    )


@router.post("/refund/{payment_id}", response_model=dict)
async def refund_payment(
    payment_id: str,
    request: RefundRequest,
    current_user: dict = Depends(get_current_user)
):
    """Process a refund for a payment with reason tracking"""
    
    result = await payment_service.process_refund(
        payment_id=payment_id,
        amount=request.amount,
        reason=request.reason
    )
    
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["message"]
        )
    
    return success_response(
        data=result,
        message="Refund processed successfully"
    )


@router.get("/wallet", response_model=dict)
async def get_wallet_balance(
    current_user: dict = Depends(get_current_user)
):
    """Get current wallet balance"""
    db = get_database()
    
    from bson import ObjectId
    user = await db.users.find_one({"_id": ObjectId(current_user["user_id"])})
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return success_response(
        data={
            "user_id": current_user["user_id"],
            "wallet_balance": user.get("wallet_balance", 0.0)
        },
        message="Wallet balance retrieved successfully"
    )


@router.get("/history", response_model=dict)
async def get_payment_history(
    status: Optional[str] = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(get_current_user)
):
    """Get payment history for current user"""
    
    payments = await payment_service.get_payment_history(
        user_id=current_user["user_id"],
        limit=limit,
        offset=offset,
        status=status
    )
    
    # Convert ObjectId to string for JSON serialization
    for payment in payments:
        payment["id"] = str(payment.pop("_id"))
    
    return success_response(
        data={
            "payments": payments,
            "limit": limit,
            "offset": offset,
            "total": len(payments)
        },
        message="Payment history retrieved successfully"
    )


@router.get("/transactions", response_model=dict)
async def get_transaction_history(
    transaction_type: Optional[str] = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(get_current_user)
):
    """Get transaction history for current user"""
    
    transactions = await payment_service.get_transaction_history(
        user_id=current_user["user_id"],
        limit=limit,
        offset=offset,
        transaction_type=transaction_type
    )
    
    # Convert ObjectId to string for JSON serialization
    for txn in transactions:
        txn["id"] = str(txn.pop("_id"))
    
    return success_response(
        data={
            "transactions": transactions,
            "limit": limit,
            "offset": offset,
            "total": len(transactions)
        },
        message="Transaction history retrieved successfully"
    )


@router.post("/webhook/{gateway}", response_model=dict)
async def handle_payment_webhook(
    gateway: str,
    payload: Dict[str, Any],
    signature: Optional[str] = None
):
    """Handle webhook notifications from payment gateways"""
    
    result = await payment_service.handle_webhook(
        gateway=gateway,
        payload=payload,
        signature=signature
    )
    
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["message"]
        )
    
    return success_response(
        data=result,
        message="Webhook processed successfully"
    )


@router.get("/gateways", response_model=dict)
async def get_supported_gateways():
    """Get list of supported payment gateways and their configurations"""
    
    return success_response(
        data={
            "gateways": payment_service.supported_gateways,
            "currencies": payment_service.supported_currencies,
            "payment_methods": payment_service.supported_payment_methods,
            "default_gateway": payment_service.default_gateway
        },
        message="Supported gateways retrieved successfully"
    )
