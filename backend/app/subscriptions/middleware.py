from fastapi import Depends, HTTPException
from sqlmodel import Session
from app.database import get_session
from app.services.auth_service import auth_service
from app.subscriptions.service import can_user_start_interview

def check_subscription(
    user_id: str = Depends(auth_service.require_auth),
    db: Session = Depends(get_session)
) -> str:
    """
    Middleware dependency to enforce subscription limit before starting/resuming interviews.
    """
    if not can_user_start_interview(user_id, db):
        raise HTTPException(
            status_code=403,
            detail={
                "error": "FREE_LIMIT_REACHED",
                "message": "You have used all free interviews.",
                "upgrade_required": True
            }
        )
    return user_id
