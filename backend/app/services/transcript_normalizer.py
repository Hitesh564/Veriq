import re
import os
from langchain_google_genai import ChatGoogleGenerativeAI
from app.config import GEMINI_API_KEY

# Dictionary of common technical interview term misrecognitions
CORRECTIONS_DICT = {
    "lang graph": "LangGraph",
    "land graph": "LangGraph",
    "lang chain": "LangChain",
    "quadrant": "Qdrant",
    "face": "FAISS",
    "rag": "RAG",
    "fast api": "FastAPI",
    "sql model": "SQLModel",
    "pi torch": "PyTorch",
    "py torch": "PyTorch",
    "redis": "Redis",
    "docker": "Docker",
    "kubernetes": "Kubernetes",
    "koobernetes": "Kubernetes",
    "coobernetes": "Kubernetes"
}

def normalize_with_dict(text: str) -> str:
    """
    Applies case-insensitive dictionary replacements for technical terminology.
    """
    corrected = text
    for wrong, right in CORRECTIONS_DICT.items():
        # Match whole word/phrase case-insensitively with word boundaries
        pattern = re.compile(rf"\b{re.escape(wrong)}\b", re.IGNORECASE)
        corrected = pattern.sub(right, corrected)
    return corrected

async def normalize_with_llm(text: str) -> str:
    """
    Calls Gemini 2.5 Flash to perform technical terminology correction.
    """
    api_key = GEMINI_API_KEY or os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("[WARNING] GEMINI_API_KEY is not configured for normalizer. Skipping LLM pass.")
        return text
        
    try:
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            temperature=0.0,
            google_api_key=api_key,
            max_retries=1
        )
        
        prompt = (
            "You are a technical transcription corrector. Correct technical terminology only. "
            "Do not change the sentence structure or general meaning.\n"
            "Only fix misspelled framework names, libraries, concepts, and acronyms to their standard casing/spelling "
            "(e.g., land graph/lang graph -> LangGraph, rag -> RAG, quadrant -> Qdrant, face -> FAISS, pi torch -> PyTorch, fast api -> FastAPI).\n\n"
            f"Input: \"{text}\"\n"
            "Output:"
        )
        
        response = await llm.ainvoke(prompt)
        corrected = response.content.strip()
        
        # Clean any surrounding quotes that the LLM might have returned
        if corrected.startswith('"') and corrected.endswith('"'):
            corrected = corrected[1:-1]
            
        if corrected:
            return corrected
    except Exception as e:
        print(f"[ERROR] LLM terminology correction failed: {e}")
        
    return text

async def normalize_transcript(text: str, run_gemini: bool = True) -> str:
    """
    Full normalization pipeline: applies dictionary corrections first,
    then runs optional Gemini-based normalization pass.
    """
    if not text or not text.strip():
        return text
        
    # 1. Apply dictionary-based corrections
    corrected = normalize_with_dict(text)
    
    # 2. Optionally run Gemini correction pass
    if run_gemini:
        corrected = await normalize_with_llm(corrected)
        # Apply dictionary corrections one more time to catch any casing inconsistencies from LLM
        corrected = normalize_with_dict(corrected)
        
    return corrected
