from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.services.payment import PaymentService, PaddleCheckoutRequest
from app.services.auth import get_current_user
from app.models import User

router = APIRouter()

class CheckoutURLRequest(BaseModel):
    product_id: int

class CheckoutURLResponse(BaseModel):
    checkout_url: str

@router.post("/checkout-url", response_model=CheckoutURLResponse)
async def create_checkout_url(
    request: CheckoutURLRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Generates a Paddle checkout URL for the authenticated user.
    """
    payment_service = PaymentService()
    checkout_request = PaddleCheckoutRequest(
        product_id=request.product_id,
        customer_email=current_user.email
    )
    
    checkout_url = payment_service.generate_checkout_url(checkout_request)
    return CheckoutURLResponse(checkout_url=checkout_url)