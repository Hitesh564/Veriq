import json
from datetime import datetime
from sqlmodel import Session, select
from app.subscriptions.models import Subscription, Payment, UserUsage, Plan

def handle_stripe_event(event_type: str, data_object: dict, db: Session):
    """
    Handles Stripe Webhook events and updates subscription tables accordingly.
    Supports idempotency (ignoring duplicate event triggers).
    """
    print(f"[WEBHOOK] Processing event type: {event_type}")
    
    if event_type == "checkout.session.completed":
        metadata = data_object.get("metadata", {})
        user_id = metadata.get("user_id")
        plan_id = metadata.get("plan_id", "pro")
        customer_id = data_object.get("customer")
        subscription_id = data_object.get("subscription")
        
        if user_id and subscription_id:
            _activate_subscription(
                user_id=user_id,
                plan_id=plan_id,
                customer_id=customer_id,
                subscription_id=subscription_id,
                db=db
            )
            
    elif event_type in ["customer.subscription.updated", "customer.subscription.deleted"]:
        subscription_id = data_object.get("id")
        status = data_object.get("status")
        customer_id = data_object.get("customer")
        
        sub = db.exec(select(Subscription).where(Subscription.subscription_id == subscription_id)).first()
        if sub:
            sub.status = status
            sub.current_period_start = datetime.utcfromtimestamp(data_object.get("current_period_start", datetime.utcnow().timestamp()))
            sub.current_period_end = datetime.utcfromtimestamp(data_object.get("current_period_end", datetime.utcnow().timestamp()))
            sub.updated_at = datetime.utcnow()
            
            if status in ["canceled", "incomplete_expired", "unpaid", "deleted"]:
                usage = db.exec(select(UserUsage).where(UserUsage.user_id == sub.user_id)).first()
                if usage:
                    usage.interviews_remaining = max(0, 3 - usage.interviews_completed)
                    db.add(usage)
                    
            db.add(sub)
            db.commit()
            print(f"[WEBHOOK] Updated subscription {subscription_id} to status: {status}")
            
    elif event_type == "invoice.payment_succeeded":
        subscription_id = data_object.get("subscription")
        charge_id = data_object.get("charge", "mock_charge_id")
        amount = data_object.get("amount_paid", 1999) / 100.0
        currency = data_object.get("currency", "usd")
        invoice_url = data_object.get("hosted_invoice_url")
        
        exists = db.exec(select(Payment).where(Payment.transaction_id == charge_id)).first()
        if not exists and subscription_id:
            sub = db.exec(select(Subscription).where(Subscription.subscription_id == subscription_id)).first()
            user_id = sub.user_id if sub else "unknown"
            
            payment = Payment(
                user_id=user_id,
                subscription_id=sub.id if sub else None,
                provider="stripe",
                transaction_id=charge_id,
                amount=amount,
                currency=currency,
                payment_status="succeeded",
                invoice_url=invoice_url
            )
            db.add(payment)
            db.commit()
            print(f"[WEBHOOK] Logged successful invoice payment of {amount} {currency} for subscription {subscription_id}")

def _activate_subscription(user_id: str, plan_id: str, customer_id: str, subscription_id: str, db: Session):
    sub = db.exec(select(Subscription).where(Subscription.subscription_id == subscription_id)).first()
    if not sub:
        sub = Subscription(
            user_id=user_id,
            provider="stripe",
            customer_id=customer_id,
            subscription_id=subscription_id,
            plan_id=plan_id,
            status="active"
        )
    else:
        sub.status = "active"
        
    db.add(sub)
    
    usage = db.exec(select(UserUsage).where(UserUsage.user_id == user_id)).first()
    if not usage:
        usage = UserUsage(user_id=user_id, interviews_completed=0)
        
    plan = db.get(Plan, plan_id)
    limit = plan.interview_limit if plan else -1
    
    if limit == -1:
        usage.interviews_remaining = 9999
    else:
        usage.interviews_remaining = max(0, limit - usage.interviews_completed)
        
    usage.updated_at = datetime.utcnow()
    db.add(usage)
    db.commit()
    print(f"[WEBHOOK] Activated {plan_id} plan for user {user_id}. Remaining interviews: {usage.interviews_remaining}")
