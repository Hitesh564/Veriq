import os
from abc import ABC, abstractmethod
from sqlmodel import Session

class PaymentService(ABC):
    @abstractmethod
    def create_checkout_session(self, user_id: str, plan_id: str, db: Session) -> str:
        """
        Creates a payment provider checkout session and returns the redirect URL.
        """
        pass
        
    @abstractmethod
    def create_customer_portal(self, user_id: str, db: Session) -> str:
        """
        Creates a customer billing portal session and returns the redirect URL.
        """
        pass
        
    @abstractmethod
    def cancel_subscription(self, subscription_id: str, db: Session) -> bool:
        """
        Cancels an active subscription immediately or at period end.
        """
        pass

def get_payment_service() -> PaymentService:
    provider = os.getenv("PAYMENT_PROVIDER", "stripe").lower()
    
    if provider == "stripe":
        from app.payments.stripe import StripePaymentService
        return StripePaymentService()
    elif provider == "razorpay":
        raise NotImplementedError("RazorpayPaymentService is not yet implemented.")
    else:
        raise ValueError(f"Unknown payment provider: {provider}")
