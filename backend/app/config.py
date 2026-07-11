import os
from dotenv import load_dotenv

# Load variables from .env file
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./dev.db")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY", "")
WHISPER_API_KEY = os.getenv("WHISPER_API_KEY") or os.getenv("GROQ_API_KEY", "")
NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY", "")
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY", "")
TECHNICAL_VOCAB = [
    "LangGraph", "LangChain", "Qdrant", "FastAPI", "RAG", "FAISS", "Gemini", "SQLModel",
    "Redis", "Vector Database", "Embedding", "Transformer", "Fine Tuning", "PyTorch",
    "TensorFlow", "Kafka", "Kubernetes", "Docker", "PostgreSQL", "SQLite", "SQLAlchemy"
]

