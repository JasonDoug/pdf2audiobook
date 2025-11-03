from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
import json

from app.core.database import get_db
from app.core.config import settings
from app.services.payment import PaymentService
from app.services.user import UserService

router = APIRouter()

@router.post("/paddle")
async def paddle_webhook(
    request: Request,
    db: Session = Depends(get_db)
):
    try:
        # Get the raw body and signature
        body = await request.body()
        signature = request.headers.get("x-paddle-signature")
        
        # Verify webhook signature
        payment_service = PaymentService()
        if not payment_service.verify_webhook_signature(body, signature):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid webhook signature"
            )
        
        # Parse webhook data
        webhook_data = json.loads(body.decode())
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
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Webhook processing failed: {str(e)}"
        )