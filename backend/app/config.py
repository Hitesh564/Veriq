import os
from dotenv import load_dotenv

# Load variables from .env file
load_dotenv()

raw_db_url = os.getenv("DATABASE_URL", "sqlite:///./dev.db")
if raw_db_url.startswith("postgres://"):
    DATABASE_URL = raw_db_url.replace("postgres://", "postgresql://", 1)
else:
    DATABASE_URL = raw_db_url

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

