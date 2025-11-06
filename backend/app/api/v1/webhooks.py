from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
import json
import logging

from app.core.database import get_db
from app.core.config import settings
from app.services.payment import PaymentService
from app.services.user import UserService

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post(
    "/paddle",
    summary="Handle Paddle Webhooks",
    description="This single endpoint receives all webhook notifications from Paddle for events like successful payments, new subscriptions, cancellations, etc. It verifies the webhook signature and processes the event to update user data accordingly.",
)
async def paddle_webhook(request: Request, db: Session = Depends(get_db)):
    """
    Handles all incoming webhooks from Paddle.

    This endpoint should not be called directly by users. It is designed to be registered in the Paddle dashboard.

    The endpoint performs the following steps:
    1.  Verifies the `Paddle-Signature` header to ensure the request is authentic.
    2.  Parses the webhook data from the request body.
    3.  Inspects the `alert_name` or `event_type` to determine what happened.
    4.  Calls the appropriate service method to update user subscriptions, credits, etc.
    """
    try:
        # Get the raw body and signature
        raw_body = await request.body()
        signature = request.headers.get(
            "Paddle-Signature"
        )  # Correct header for Paddle Billing
        if not signature:
            signature = request.headers.get(
                "x-paddle-signature"
            )  # Fallback for Paddle Classic

        # Verify webhook signature
        payment_service = PaymentService()
        # Note: Paddle Classic verification is complex. This is a simplified check.
        if not payment_service.verify_webhook_signature(raw_body, signature):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid webhook signature",
            )

        # Parse webhook data
        webhook_data = json.loads(raw_body.decode())
        event_type = webhook_data.get("alert_name")

        user_service = UserService(db)

        if event_type == "subscription_created":
            # Handle new subscription
            user_service.handle_subscription_created(webhook_data)

        elif event_type == "subscription_payment_succeeded":
            # Handle successful subscription payment
            user_service.handle_subscription_payment(webhook_data)

        elif event_type == "subscription_cancelled":
            # Handle subscription cancellation
            user_service.handle_subscription_cancelled(webhook_data)

        elif event_type == "payment_succeeded":
            # Handle one-time payment (credit packs)
            user_service.handle_payment_succeeded(webhook_data)

        return {"status": "success"}

    except Exception as e:
        logger.error(f"Webhook processing failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Webhook processing failed: {str(e)}",
        )
