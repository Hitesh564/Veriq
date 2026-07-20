import os
from sqlmodel import Session, select
import stripe
from app.payments.service import PaymentService
from app.subscriptions.models import Subscription

stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "sk_test_mock")

class StripePaymentService(PaymentService):
    def create_checkout_session(self, user_id: str, plan_id: str, db: Session) -> str:
        frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
        
        price_id = os.getenv(f"STRIPE_{plan_id.upper()}_PRICE_ID")
        if not price_id:
            price_id = "price_mock_pro" if plan_id == "pro" else "price_mock_free"
            
        if stripe.api_key == "sk_test_mock" or stripe.api_key.startswith("sk_test_mock"):
            return f"{frontend_url}/payment-success?session_id=mock_checkout_session_{user_id}&plan_id={plan_id}"
            
        try:
            existing_sub = db.exec(select(Subscription).where(Subscription.user_id == user_id)).first()
            customer_id = existing_sub.customer_id if existing_sub else None
            
            session_kwargs = {
                "payment_method_types": ["card"],
                "line_items": [{
                    "price": price_id,
                    "quantity": 1,
                }],
                "mode": "subscription",
                "metadata": {
                    "user_id": user_id,
                    "plan_id": plan_id
                },
                "success_url": f"{frontend_url}/payment-success?session_id={{CHECKOUT_SESSION_ID}}",
                "cancel_url": f"{frontend_url}/pricing",
            }
            
            if customer_id:
                session_kwargs["customer"] = customer_id
            
            session = stripe.checkout.Session.create(**session_kwargs)
            return session.url
        except Exception as e:
            print(f"[ERROR] Failed to create Stripe checkout session: {e}")
            raise RuntimeError(f"Stripe session generation failed: {str(e)}")
            
    def create_customer_portal(self, user_id: str, db: Session) -> str:
        frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
        
        if stripe.api_key == "sk_test_mock" or stripe.api_key.startswith("sk_test_mock"):
            return f"{frontend_url}/billing"
            
        sub = db.exec(select(Subscription).where(Subscription.user_id == user_id)).first()
        if not sub or not sub.customer_id:
            raise ValueError("No active Stripe customer profile found for this account.")
            
        try:
            portal_session = stripe.billing_portal.Session.create(
                customer=sub.customer_id,
                return_url=f"{frontend_url}/billing"
            )
            return portal_session.url
        except Exception as e:
            print(f"[ERROR] Failed to create Stripe billing portal: {e}")
            raise RuntimeError(f"Stripe billing portal generation failed: {str(e)}")
            
    def cancel_subscription(self, subscription_id: str, db: Session) -> bool:
        if stripe.api_key == "sk_test_mock" or stripe.api_key.startswith("sk_test_mock"):
            sub = db.exec(select(Subscription).where(Subscription.subscription_id == subscription_id)).first()
            if sub:
                sub.status = "canceled"
                db.add(sub)
                db.commit()
            return True
            
        try:
            stripe.Subscription.modify(
                subscription_id,
                cancel_at_period_end=True
            )
            return True
        except Exception as e:
            print(f"[ERROR] Failed to cancel Stripe subscription: {e}")
            return False
