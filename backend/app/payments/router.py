import os
import json
from fastapi import APIRouter, Depends, HTTPException, Request, Header
from sqlmodel import Session, select
import stripe

from app.database import get_session
from app.services.auth_service import auth_service
from app.subscriptions.models import Plan, Subscription, Payment, UserUsage
from app.payments.service import get_payment_service
from app.payments.webhook import handle_stripe_event

router = APIRouter(prefix="/api/v1/payments", tags=["payments"])

stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "sk_test_mock")
stripe_webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET", "whsec_mock")

@router.get("/plans")
def list_plans(db: Session = Depends(get_session)):
    plans = db.exec(select(Plan).where(Plan.active == True)).all()
    result = []
    for p in plans:
        try:
            features = json.loads(p.features_json)
        except:
            features = []
        result.append({
            "id": p.id,
            "name": p.name,
            "monthly_price": p.monthly_price,
            "interview_limit": p.interview_limit,
            "features": features
        })
    return result

@router.get("/subscription")
def get_subscription_status(user_id: str = Depends(auth_service.require_auth), db: Session = Depends(get_session)):
    usage = db.exec(select(UserUsage).where(UserUsage.user_id == user_id)).first()
    if not usage:
        usage = UserUsage(user_id=user_id, interviews_completed=0, interviews_remaining=3)
        db.add(usage)
        db.commit()
        db.refresh(usage)
        
    sub = db.exec(
        select(Subscription).where(
            Subscription.user_id == user_id,
            Subscription.status.in_(["active", "trialing", "trialing_expired"])
        )
    ).first()
    
    plan_name = "Free Plan"
    plan_id = "free"
    renewal_date = None
    is_subscribed = False
    billing_status = "active"
    subscription_id = None
    
    if sub:
        plan = db.get(Plan, sub.plan_id)
        plan_name = plan.name if plan else "Pro Plan"
        plan_id = sub.plan_id
        renewal_date = sub.current_period_end.isoformat()
        is_subscribed = True
        billing_status = sub.status
        subscription_id = sub.subscription_id
        
    return {
        "user_id": user_id,
        "is_subscribed": is_subscribed,
        "plan_id": plan_id,
        "plan_name": plan_name,
        "interviews_completed": usage.interviews_completed,
        "interviews_remaining": usage.interviews_remaining,
        "billing_status": billing_status,
        "renewal_date": renewal_date,
        "subscription_id": subscription_id
    }

@router.post("/create-checkout-session")
def create_checkout_session(plan_id: str = "pro", user_id: str = Depends(auth_service.require_auth), db: Session = Depends(get_session)):
    try:
        service = get_payment_service()
        checkout_url = service.create_checkout_session(user_id, plan_id, db)
        return {"url": checkout_url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/customer-portal")
def customer_portal(user_id: str = Depends(auth_service.require_auth), db: Session = Depends(get_session)):
    try:
        service = get_payment_service()
        portal_url = service.create_customer_portal(user_id, db)
        return {"url": portal_url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/cancel")
def cancel_subscription(subscription_id: str, user_id: str = Depends(auth_service.require_auth), db: Session = Depends(get_session)):
    sub = db.exec(
        select(Subscription).where(
            Subscription.user_id == user_id,
            Subscription.subscription_id == subscription_id
        )
    ).first()
    
    if not sub:
        raise HTTPException(status_code=404, detail="Subscription record not found.")
        
    try:
        service = get_payment_service()
        success = service.cancel_subscription(subscription_id, db)
        if success:
            return {"status": "success", "message": "Subscription set to cancel at period end."}
        else:
            raise HTTPException(status_code=400, detail="Failed to cancel subscription.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/history")
def payment_history(user_id: str = Depends(auth_service.require_auth), db: Session = Depends(get_session)):
    payments = db.exec(select(Payment).where(Payment.user_id == user_id).order_by(Payment.created_at.desc())).all()
    return payments

@router.post("/webhook")
async def stripe_webhook(request: Request, stripe_signature: str = Header(None), db: Session = Depends(get_session)):
    payload = await request.body()
    
    if stripe.api_key == "sk_test_mock" or not stripe_signature:
        try:
            event_data = json.loads(payload.decode("utf-8"))
            event_type = event_data.get("type")
            data_object = event_data.get("data", {}).get("object", {})
            handle_stripe_event(event_type, data_object, db)
            return {"status": "success", "detail": "Mock webhook processed."}
        except Exception as err:
            raise HTTPException(status_code=400, detail=f"Mock webhook parse error: {str(err)}")
            
    try:
        event = stripe.Webhook.construct_event(
            payload, stripe_signature, stripe_webhook_secret
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Webhook signature verification failed: {str(e)}")
        
    handle_stripe_event(event['type'], event['data']['object'], db)
    return {"status": "success"}
