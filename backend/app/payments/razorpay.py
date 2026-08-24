import os
import hmac
import hashlib
from typing import Optional, Dict, Any
from sqlmodel import Session, select
from datetime import datetime, timedelta
from decimal import Decimal
from fastapi import HTTPException
import razorpay
from razorpay.errors import BadRequestError, GatewayError, ServerError, SignatureVerificationError

from app.payments.service import PaymentService
from app.subscriptions.models import Subscription, Payment, UserUsage, Plan

class RazorpayClientManager:
    @staticmethod
    def get_client() -> razorpay.Client:
        key_id = os.getenv("RAZORPAY_KEY_ID", "rzp_test_TTiNj5PVM8xl3r")
        key_secret = os.getenv("RAZORPAY_KEY_SECRET", "TFSbnihCAdeSRBt59diajygr")
        return razorpay.Client(auth=(key_id, key_secret))

    @staticmethod
    def get_key_id() -> str:
        return os.getenv("RAZORPAY_KEY_ID", "rzp_test_TTiNj5PVM8xl3r")

    @staticmethod
    def get_key_secret() -> str:
        return os.getenv("RAZORPAY_KEY_SECRET", "TFSbnihCAdeSRBt59diajygr")


def create_razorpay_order(
    amount: int,
    currency: str = "INR",
    receipt: Optional[str] = None,
    notes: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Creates an order with Razorpay.
    amount: amount in smallest currency subunit (e.g., paise for INR). Minimum is 100 paise.
    """
    if amount is None or amount < 100:
        raise HTTPException(
            status_code=400,
            detail="Invalid amount. Minimum order amount is 100 paise (₹1.00)."
        )

    try:
        client = RazorpayClientManager.get_client()
        order_data: Dict[str, Any] = {
            "amount": int(amount),
            "currency": (currency or "INR").upper(),
            "payment_capture": 1
        }
        if receipt:
            order_data["receipt"] = str(receipt)
        if notes:
            order_data["notes"] = notes

        order = client.order.create(data=order_data)
        return {
            "order_id": order.get("id"),
            "amount": order.get("amount"),
            "currency": order.get("currency"),
            "status": order.get("status"),
            "receipt": order.get("receipt"),
            "key_id": RazorpayClientManager.get_key_id()
        }
    except BadRequestError as err:
        err_msg = str(err)
        if "Authentication failed" in err_msg or "auth" in err_msg.lower() or "unauthorized" in err_msg.lower():
            raise HTTPException(status_code=401, detail=f"Razorpay authentication failed: {err_msg}")
        raise HTTPException(status_code=400, detail=f"Razorpay bad request: {err_msg}")
    except (GatewayError, ServerError) as err:
        raise HTTPException(status_code=500, detail=f"Razorpay gateway error: {str(err)}")
    except HTTPException:
        raise
    except Exception as err:
        err_msg = str(err)
        if "auth" in err_msg.lower() or "unauthorized" in err_msg.lower() or "key" in err_msg.lower() and "invalid" in err_msg.lower():
            raise HTTPException(status_code=401, detail=f"Razorpay authentication error: {err_msg}")
        raise HTTPException(status_code=500, detail=f"Failed to create Razorpay order: {err_msg}")


def verify_razorpay_payment_signature(
    razorpay_order_id: str,
    razorpay_payment_id: str,
    razorpay_signature: str
) -> bool:
    """
    Verifies the HMAC-SHA256 signature of a Razorpay payment response.
    Algorithm: HMAC-SHA256(order_id + "|" + payment_id, KEY_SECRET)
    """
    if not razorpay_order_id or not razorpay_payment_id or not razorpay_signature:
        return False

    key_secret = RazorpayClientManager.get_key_secret()
    payload = f"{razorpay_order_id}|{razorpay_payment_id}".encode("utf-8")
    expected_signature = hmac.new(
        key_secret.encode("utf-8"),
        payload,
        hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(expected_signature, razorpay_signature)


def process_payment_verification(
    razorpay_order_id: str,
    razorpay_payment_id: str,
    razorpay_signature: str,
    user_id: Optional[str] = None,
    plan_id: Optional[str] = "pro",
    db: Optional[Session] = None
) -> Dict[str, Any]:
    """
    Validates fields, verifies signature, and persists subscription/payment if DB and user_id are supplied.
    """
    if not razorpay_order_id or not razorpay_payment_id or not razorpay_signature:
        raise HTTPException(
            status_code=400,
            detail="Missing required fields: razorpay_order_id, razorpay_payment_id, and razorpay_signature are all required."
        )

    is_valid = verify_razorpay_payment_signature(
        razorpay_order_id=razorpay_order_id.strip(),
        razorpay_payment_id=razorpay_payment_id.strip(),
        razorpay_signature=razorpay_signature.strip()
    )

    if not is_valid:
        raise HTTPException(
            status_code=400,
            detail="Payment verification failed: Signature mismatch. Payment has not been marked as paid."
        )

    if db and user_id:
        try:
            record_successful_payment(
                db=db,
                user_id=user_id,
                razorpay_order_id=razorpay_order_id,
                razorpay_payment_id=razorpay_payment_id,
                plan_id=plan_id or "pro"
            )
        except Exception as e:
            db.rollback()
            print(f"[ERROR] Failed to update subscription/payment records: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Payment signature verified, but error occurred updating database records: {str(e)}"
            )

    return {
        "status": "success",
        "message": "Payment verified successfully",
        "order_id": razorpay_order_id,
        "payment_id": razorpay_payment_id
    }


def record_successful_payment(
    db: Session,
    user_id: str,
    razorpay_order_id: str,
    razorpay_payment_id: str,
    amount_in_paise: int = 19900,
    currency: str = "INR",
    plan_id: str = "pro"
) -> None:
    """
    Updates the database with the subscription and payment record for the user.
    """
    amount_in_units = Decimal(amount_in_paise) / Decimal(100)
    now = datetime.utcnow()
    period_end = now + timedelta(days=30)
    
    # Ensure Plan exists in database
    plan = db.get(Plan, plan_id)
    if not plan and plan_id == "pro":
        plan = Plan(
            id="pro",
            name="Pro Plan",
            monthly_price=Decimal("199.00"),
            interview_limit=-1,
            features_json='["Unlimited practice sessions", "Detailed evaluations", "Personalized learning plans"]',
            active=True
        )
        db.add(plan)
        db.flush()
    
    # Update or create subscription
    existing_sub = db.exec(select(Subscription).where(Subscription.user_id == user_id)).first()
    
    if existing_sub:
        existing_sub.provider = "razorpay"
        existing_sub.customer_id = existing_sub.customer_id or f"rzp_cust_{user_id[:8]}"
        existing_sub.subscription_id = razorpay_order_id
        existing_sub.plan_id = plan_id
        existing_sub.status = "active"
        existing_sub.current_period_start = now
        existing_sub.current_period_end = period_end
        existing_sub.updated_at = now
        db.add(existing_sub)
        db.flush()
        subscription_pk_id = existing_sub.id
    else:
        new_sub = Subscription(
            user_id=user_id,
            provider="razorpay",
            customer_id=f"rzp_cust_{user_id[:8]}",
            subscription_id=razorpay_order_id,
            plan_id=plan_id,
            status="active",
            current_period_start=now,
            current_period_end=period_end,
            created_at=now,
            updated_at=now
        )
        db.add(new_sub)
        db.flush()
        subscription_pk_id = new_sub.id

    # Record payment transaction (idempotent check by transaction_id)
    existing_payment = db.exec(select(Payment).where(Payment.transaction_id == razorpay_payment_id)).first()
    if not existing_payment:
        payment_record = Payment(
            user_id=user_id,
            subscription_id=subscription_pk_id,
            provider="razorpay",
            transaction_id=razorpay_payment_id,
            amount=amount_in_units,
            currency=currency.lower(),
            payment_status="succeeded",
            invoice_url=None,
            created_at=now
        )
        db.add(payment_record)

    # Refresh user usage
    usage = db.exec(select(UserUsage).where(UserUsage.user_id == user_id)).first()
    if not usage:
        usage = UserUsage(user_id=user_id, interviews_completed=0, interviews_remaining=9999)
        db.add(usage)
    else:
        usage.interviews_remaining = 9999  # Unlimited for pro
        usage.updated_at = now
        db.add(usage)

    db.commit()


class RazorpayPaymentService(PaymentService):
    """
    Implements PaymentService interface for Razorpay.
    """
    def create_checkout_session(self, user_id: str, plan_id: str, db: Session) -> str:
        frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
        return f"{frontend_url}/pricing?checkout=razorpay&plan={plan_id}"

    def create_customer_portal(self, user_id: str, db: Session) -> str:
        frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
        return f"{frontend_url}/billing"

    def cancel_subscription(self, subscription_id: str, db: Session) -> bool:
        sub = db.exec(select(Subscription).where(Subscription.subscription_id == subscription_id)).first()
        if sub:
            sub.status = "canceled"
            sub.updated_at = datetime.utcnow()
            db.add(sub)
            db.commit()
            return True
        return False
