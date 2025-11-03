import hashlib
import hmac
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.config import settings
from app.models import Product
from app.schemas import Product as ProductSchema

class PaymentService:
    def __init__(self):
        self.vendor_id = settings.PADDLE_VENDOR_ID
        self.vendor_auth_code = settings.PADDLE_VENDOR_AUTH_CODE
        self.public_key = settings.PADDLE_PUBLIC_KEY
        self.environment = settings.PADDLE_ENVIRONMENT
    
    def verify_webhook_signature(self, body: bytes, signature: str) -> bool:
        """Verify Paddle webhook signature"""
        try:
            # Paddle uses HMAC-SHA256 for webhook signatures
            expected_signature = hmac.new(
                self.public_key.encode(),
                body,
                hashlib.sha256
            ).hexdigest()
            
            return hmac.compare_digest(expected_signature, signature)
        except Exception:
            return False
    
    def get_active_products(self, db: Session) -> List[ProductSchema]:
        """Get all active products"""
        products = db.query(Product).filter(Product.is_active == True).all()
        return [ProductSchema.from_orm(product) for product in products]
    
    def create_checkout_url(self, product_id: int, user_email: str) -> Optional[str]:
        """Create a Paddle checkout URL for a product"""
        try:
            # This is a simplified version - in production you'd use Paddle's API
            # to generate proper checkout links with proper parameters
            
            base_url = "https://checkout.paddle.com/checkout/custom/"
            
            if self.environment == "sandbox":
                base_url = "https://sandbox-checkout.paddle.com/checkout/custom/"
            
            # In a real implementation, you would:
            # 1. Call Paddle's API to generate a checkout link
            # 2. Include product IDs, customer info, etc.
            # 3. Handle success/cancel URLs
            
            checkout_params = {
                "product_ids": str(product_id),
                "customer_email": user_email,
                "passthrough": f"user_email={user_email}"
            }
            
            # For now, return a placeholder URL
            return f"{base_url}?product_ids={product_id}&customer_email={user_email}"
            
        except Exception as e:
            print(f"Error creating checkout URL: {str(e)}")
            return None
    
    def get_subscription_plans(self) -> List[dict]:
        """Get available subscription plans"""
        return [
            {
                "id": "pro_monthly",
                "name": "Pro Monthly",
                "price": 29.99,
                "currency": "USD",
                "interval": "month",
                "features": [
                    "50 PDF conversions per month",
                    "Premium voices",
                    "Faster processing",
                    "Priority support"
                ]
            },
            {
                "id": "pro_yearly",
                "name": "Pro Yearly",
                "price": 299.99,
                "currency": "USD",
                "interval": "year",
                "features": [
                    "600 PDF conversions per year",
                    "Premium voices",
                    "Fastest processing",
                    "Priority support",
                    "2 months free"
                ]
            },
            {
                "id": "enterprise",
                "name": "Enterprise",
                "price": 99.99,
                "currency": "USD",
                "interval": "month",
                "features": [
                    "Unlimited PDF conversions",
                    "All premium voices",
                    "Fastest processing",
                    "Dedicated support",
                    "Custom integrations",
                    "API access"
                ]
            }
        ]
    
    def get_credit_packs(self) -> List[dict]:
        """Get available credit packs"""
        return [
            {
                "id": "credits_10",
                "name": "10 Credits",
                "price": 9.99,
                "currency": "USD",
                "credits": 10,
                "description": "Perfect for trying out our service"
            },
            {
                "id": "credits_50",
                "name": "50 Credits",
                "price": 39.99,
                "currency": "USD",
                "credits": 50,
                "description": "Great for occasional use",
                "popular": True
            },
            {
                "id": "credits_200",
                "name": "200 Credits",
                "price": 149.99,
                "currency": "USD",
                "credits": 200,
                "description": "Best value for regular users"
            }
        ]