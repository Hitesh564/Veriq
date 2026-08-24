from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.routers.interview import router as interview_router
from app.routers.voice import router as voice_router
from app.database import get_session
from sqlmodel import Session
from fastapi import Depends
from app.payments.router import (
    router as payments_router,
    CreateOrderRequest,
    VerifyPaymentRequest,
    create_order_endpoint,
    verify_payment_endpoint
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield

app = FastAPI(
    title="Veriq AI API",
    description="Backend API and LangGraph Agent services for Veriq AI",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(interview_router) 
app.include_router(voice_router)
app.include_router(payments_router)

# Direct root endpoints for Razorpay Standard Checkout
@app.post("/api/create-order", tags=["payments"])
def create_order_root(req: CreateOrderRequest):
    return create_order_endpoint(req)

@app.post("/api/verify-payment", tags=["payments"])
def verify_payment_root(req: VerifyPaymentRequest, db: Session = Depends(get_session)):
    return verify_payment_endpoint(req, db=db)

@app.get("/api/health")
def health_check():
    return {"status": "healthy", "service": "Veriq AI Backend"}
