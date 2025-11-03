from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.models import User, Subscription, Transaction, Product
from app.schemas import UserCreate, UserUpdate

class UserService:
    def __init__(self, db: Session):
        self.db = db
    
    def get_user_by_id(self, user_id: int) -> Optional[User]:
        return self.db.query(User).filter(User.id == user_id).first()
    
    def get_user_by_auth_id(self, auth_provider_id: str) -> Optional[User]:
        return self.db.query(User).filter(User.auth_provider_id == auth_provider_id).first()
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        return self.db.query(User).filter(User.email == email).first()
    
    def get_or_create_user(self, user_data: dict) -> User:
        # Check if user exists
        user = self.get_user_by_auth_id(user_data["auth_provider_id"])
        
        if user:
            # Update user info if needed
            if user_data.get("first_name") != user.first_name or \
               user_data.get("last_name") != user.last_name:
                user.first_name = user_data.get("first_name")
                user.last_name = user_data.get("last_name")
                self.db.commit()
                self.db.refresh(user)
            return user
        
        # Create new user
        user = User(
            auth_provider_id=user_data["auth_provider_id"],
            email=user_data["email"],
            first_name=user_data.get("first_name"),
            last_name=user_data.get("last_name")
        )
        
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user
    
    def update_user(self, user_id: int, user_update: UserUpdate) -> User:
        user = self.get_user_by_id(user_id)
        if not user:
            raise ValueError("User not found")
        
        for field, value in user_update.dict(exclude_unset=True).items():
            setattr(user, field, value)
        
        self.db.commit()
        self.db.refresh(user)
        return user
    
    def handle_subscription_created(self, webhook_data: dict):
        """Handle subscription creation webhook from Paddle"""
        email = webhook_data.get("email")
        subscription_id = webhook_data.get("subscription_id")
        product_id = webhook_data.get("product_id")
        
        user = self.get_user_by_email(email)
        if not user:
            # Create user if doesn't exist
            user = self.get_or_create_user({
                "auth_provider_id": f"paddle_{subscription_id}",
                "email": email
            })
        
        # Update user subscription info
        product = self.db.query(Product).filter(Product.paddle_product_id == product_id).first()
        if product and product.subscription_tier:
            user.subscription_tier = product.subscription_tier
        
        user.paddle_customer_id = webhook_data.get("customer_id")
        
        # Create subscription record
        subscription = Subscription(
            user_id=user.id,
            product_id=product.id if product else None,
            paddle_subscription_id=subscription_id,
            status="active",
            next_billing_date=datetime.fromisoformat(webhook_data.get("next_payment_date"))
        )
        
        self.db.add(subscription)
        self.db.commit()
    
    def handle_subscription_payment(self, webhook_data: dict):
        """Handle successful subscription payment"""
        subscription_id = webhook_data.get("subscription_id")
        
        subscription = self.db.query(Subscription).filter(
            Subscription.paddle_subscription_id == subscription_id
        ).first()
        
        if subscription:
            subscription.status = "active"
            # Reset monthly credits usage
            user = subscription.user
            user.monthly_credits_used = 0
            
            self.db.commit()
    
    def handle_subscription_cancelled(self, webhook_data: dict):
        """Handle subscription cancellation"""
        subscription_id = webhook_data.get("subscription_id")
        
        subscription = self.db.query(Subscription).filter(
            Subscription.paddle_subscription_id == subscription_id
        ).first()
        
        if subscription:
            subscription.status = "cancelled"
            subscription.cancelled_at = datetime.now()
            
            # Downgrade user to free tier at end of billing period
            user = subscription.user
            user.subscription_tier = "free"
            
            self.db.commit()
    
    def handle_payment_succeeded(self, webhook_data: dict):
        """Handle one-time payment (credit packs)"""
        email = webhook_data.get("email")
        product_id = webhook_data.get("product_id")
        transaction_id = webhook_data.get("checkout_id")
        amount = float(webhook_data.get("sale_gross", 0))
        
        user = self.get_user_by_email(email)
        if not user:
            user = self.get_or_create_user({
                "auth_provider_id": f"paddle_{transaction_id}",
                "email": email
            })
        
        product = self.db.query(Product).filter(Product.paddle_product_id == product_id).first()
        
        # Add credits to user account
        if product and product.credits_included:
            user.one_time_credits += product.credits_included
        
        # Create transaction record
        transaction = Transaction(
            user_id=user.id,
            product_id=product.id if product else None,
            paddle_transaction_id=transaction_id,
            amount=amount,
            credits_added=product.credits_included if product else None
        )
        
        self.db.add(transaction)
        self.db.commit()