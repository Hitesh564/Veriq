import uuid
from datetime import datetime
from typing import Optional
from sqlmodel import Field, SQLModel

class Plan(SQLModel, table=True):
    __tablename__ = "plans"
    
    id: str = Field(primary_key=True)
    name: str = Field(nullable=False)
    monthly_price: float = Field(nullable=False)
    interview_limit: int = Field(nullable=False)  # -1 for unlimited, 3 for Free
    features_json: str = Field(default="[]")
    active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Subscription(SQLModel, table=True):
    __tablename__ = "subscriptions"
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    user_id: str = Field(unique=True, index=True, nullable=False)
    provider: str = Field(default="stripe")
    customer_id: str = Field(nullable=False)
    subscription_id: str = Field(nullable=False)
    plan_id: str = Field(foreign_key="plans.id", nullable=False)
    status: str = Field(default="active")
    current_period_start: datetime = Field(default_factory=datetime.utcnow)
    current_period_end: datetime = Field(default_factory=datetime.utcnow)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class Payment(SQLModel, table=True):
    __tablename__ = "payments"
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    user_id: str = Field(index=True, nullable=False)
    subscription_id: Optional[str] = Field(default=None, foreign_key="subscriptions.id", nullable=True)
    provider: str = Field(default="stripe")
    transaction_id: str = Field(unique=True, index=True, nullable=False)
    amount: float = Field(nullable=False)
    currency: str = Field(default="usd")
    payment_status: str = Field(default="succeeded")
    invoice_url: Optional[str] = Field(default=None, nullable=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)

class UserUsage(SQLModel, table=True):
    __tablename__ = "user_usage"
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    user_id: str = Field(unique=True, index=True, nullable=False)
    interviews_completed: int = Field(default=0)
    interviews_remaining: int = Field(default=3)  # default for Free plan
    updated_at: datetime = Field(default_factory=datetime.utcnow)
