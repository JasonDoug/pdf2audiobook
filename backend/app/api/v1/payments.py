from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.schemas import Product
from app.services.payment import PaymentService

router = APIRouter()

@router.get("/products", response_model=List[Product])
async def get_products(
    db: Session = Depends(get_db)
):
    payment_service = PaymentService()
    return payment_service.get_active_products(db)

@router.post("/checkout-url")
async def get_checkout_url(
    product_id: int,
    user_email: str,
    db: Session = Depends(get_db)
):
    payment_service = PaymentService()
    checkout_url = payment_service.create_checkout_url(product_id, user_email)
    
    if not checkout_url:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    return {"checkout_url": checkout_url}