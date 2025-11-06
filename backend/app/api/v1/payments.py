from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.services.payment import PaymentService, PaddleCheckoutRequest
from app.services.auth import get_current_user
from app.models import User

router = APIRouter()


class CheckoutURLRequest(BaseModel):
    product_id: int = Field(
        ..., example=1, description="The internal ID of the product to purchase."
    )


class CheckoutURLResponse(BaseModel):
    checkout_url: str = Field(
        ...,
        example="https://sandbox-vendors.paddle.com/checkout/user/123/hash?redirect_url=...",
        description="The generated Paddle checkout URL.",
    )


@router.post(
    "/checkout-url",
    response_model=CheckoutURLResponse,
    summary="Generate a Payment Checkout URL",
    description="Creates a unique Paddle checkout URL for a specific product and the currently authenticated user.",
)
async def create_checkout_url(
    request: CheckoutURLRequest, current_user: User = Depends(get_current_user)
):
    """
    Generates a Paddle checkout URL for the authenticated user to purchase a product.

    - **product_id**: The ID of the product (subscription or credit pack) to buy.
    """
    payment_service = PaymentService()
    checkout_request = PaddleCheckoutRequest(
        product_id=request.product_id, customer_email=current_user.email
    )

    checkout_url = payment_service.generate_checkout_url(checkout_request)
    return CheckoutURLResponse(checkout_url=checkout_url)
