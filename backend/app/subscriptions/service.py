from datetime import datetime
from sqlmodel import Session, select
from app.subscriptions.models import Plan, Subscription, UserUsage

def get_or_create_user_usage(user_id: str, db: Session) -> UserUsage:
    usage = db.exec(select(UserUsage).where(UserUsage.user_id == user_id)).first()
    if not usage:
        usage = UserUsage(
            user_id=user_id,
            interviews_completed=0,
            interviews_remaining=3
        )
        db.add(usage)
        db.commit()
        db.refresh(usage)
    return usage

def can_user_start_interview(user_id: str, db: Session) -> bool:
    # 1. Load active subscription
    sub = db.exec(
        select(Subscription).where(
            Subscription.user_id == user_id,
            Subscription.status.in_(["active", "trialing"])
        )
    ).first()
    
    if sub:
        # User is subscribed, load plan limit
        plan = db.get(Plan, sub.plan_id)
        if plan and plan.active:
            if plan.interview_limit == -1:
                return True
                
    # 2. Check free trial usage
    usage = get_or_create_user_usage(user_id, db)
    free_plan = db.get(Plan, "free")
    free_limit = free_plan.interview_limit if free_plan else 3
    
    return usage.interviews_completed < free_limit

def increment_interview_usage(user_id: str, db: Session) -> None:
    usage = get_or_create_user_usage(user_id, db)
    
    sub = db.exec(
        select(Subscription).where(
            Subscription.user_id == user_id,
            Subscription.status.in_(["active", "trialing"])
        )
    ).first()
    
    limit = 3
    if sub:
        plan = db.get(Plan, sub.plan_id)
        if plan:
            limit = plan.interview_limit
            
    usage.interviews_completed += 1
    if limit == -1:
        usage.interviews_remaining = 9999
    else:
        usage.interviews_remaining = max(0, limit - usage.interviews_completed)
        
    usage.updated_at = datetime.utcnow()
    db.add(usage)
    db.commit()
