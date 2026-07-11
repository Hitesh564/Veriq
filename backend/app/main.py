from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.database import init_db
from app.routers.interview import router as interview_router
from app.routers.voice import router as voice_router
from app.payments.router import router as payments_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize SQLite Database tables on startup
    init_db()
    yield

app = FastAPI(
    title="Veriq AI API",
    description="Backend API and LangGraph Agent services for Veriq AI",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS to allow Next.js local frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify the actual frontend domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(interview_router)
app.include_router(voice_router)
app.include_router(payments_router)

@app.get("/api/health")
def health_check():
    return {"status": "healthy", "service": "Veriq AI Backend"}
