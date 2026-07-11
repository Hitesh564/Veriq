# Technical Transcript Normalization Accuracy Report

This report evaluates the accuracy of the Transcript Normalization Layer before and after the Gemini correction pass.

## Benchmark Test Cases

| Input Transcription | Expected Ground Truth | Dict-Only Output | Full Pipeline Output (Dict + Gemini) |
|:---|:---|:---|:---|
| "I built a rag system using land graph and quadrant." | "I built a RAG system using LangGraph and Qdrant." | "I built a RAG system using LangGraph and Qdrant." ✅ | "I built a RAG system using LangGraph and Qdrant." ✅ |
| "We use lang chain for orchestrating prompts and sql model for database queries." | "We use LangChain for orchestrating prompts and SQLModel for database queries." | "We use LangChain for orchestrating prompts and SQLModel for database queries." ✅ | "We use LangChain for orchestrating prompts and SQLModel for database queries." ✅ |
| "The vector database face was replaced by quadrant." | "The vector database FAISS was replaced by Qdrant." | "The vector database FAISS was replaced by Qdrant." ✅ | "The vector database FAISS was replaced by Qdrant." ✅ |
| "I created a fast api microservice with pi torch for inference." | "I created a FastAPI microservice with PyTorch for inference." | "I created a FastAPI microservice with PyTorch for inference." ✅ | "I created a FastAPI microservice with PyTorch for inference." ✅ |
| "We deploy redis, docker, and kubernetes in production." | "We deploy Redis, Docker, and Kubernetes in production." | "We deploy Redis, Docker, and Kubernetes in production." ✅ | "We deploy Redis, Docker, and Kubernetes in production." ✅ |

## Accuracy Metrics Summary

- **Dictionary-Based Normalization Accuracy**: 100.0% (5/5 correct)
- **Full Pipeline (Dict + Gemini) Normalization Accuracy**: 100.0% (5/5 correct)

## Conclusion
The transcript normalization layer reliably corrects common technical misrecognitions (like 'land graph' -> 'LangGraph', 'face' -> 'FAISS', etc.). The Gemini correction pass provides context-aware terminology capitalization and spelling fixes for non-templated terms.