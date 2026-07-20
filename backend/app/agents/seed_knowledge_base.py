import os
import uuid

try:
    # pyrefly: ignore [missing-import]
    from qdrant_client import QdrantClient
    # pyrefly: ignore [missing-import]
    from qdrant_client.http import models as q_models
except ImportError:
    QdrantClient = None
    q_models = None

# Curated, fine-grained concept knowledge base
KNOWLEDGE_DATA = [
    # Transformers concepts
    {
        "topic": "Transformers",
        "concept": "Self-Attention",
        "difficulty_level": "intermediate",
        "content": "Self-attention computes dynamic weights between token representations. It involves multiplying the input vectors with learned Query, Key, and Value matrices to output a weighted sum of values. This allows the model to contextually link different words in a sequence regardless of their distance.",
        "estimated_completion_time": "30 minutes",
        "resource_type": "article",
        "source_quality": 4.9,
        "resources": [
            {"title": "The Illustrated Transformer (Jay Alammar)", "url": "https://jalammar.github.io/illustrated-transformer/"}
        ],
        "practice_questions": [
            "What is the mathematical formula for scaled dot-product attention?",
            "Explain the role of Query, Key, and Value vectors in self-attention."
        ]
    },
    {
        "topic": "Transformers",
        "concept": "Multi-Head Attention",
        "difficulty_level": "advanced",
        "content": "Multi-head attention runs multiple self-attention mechanisms (heads) in parallel. Each head learns a different set of Q, K, V projection matrices, allowing the model to jointly attend to information from different representation subspaces at different positions.",
        "estimated_completion_time": "45 minutes",
        "resource_type": "article",
        "source_quality": 4.8,
        "resources": [
            {"title": "Attention Is All You Need Paper", "url": "https://arxiv.org/abs/1706.03762"}
        ],
        "practice_questions": [
            "Why is multi-head attention preferred over single-head attention?",
            "How are outputs from individual attention heads combined before projection?"
        ]
    },
    {
        "topic": "Transformers",
        "concept": "Positional Encoding",
        "difficulty_level": "beginner",
        "content": "Since Transformer architectures process all tokens simultaneously without recurrence or convolution, they have no inherent sense of word order. Positional encodings add positional vectors (often based on sine and cosine functions of varying frequencies) to input embeddings to preserve sequence structure.",
        "estimated_completion_time": "20 minutes",
        "resource_type": "documentation",
        "source_quality": 4.7,
        "resources": [
            {"title": "Understanding Positional Encoding (Kazemnejad)", "url": "https://kazemnejad.com/blog/transformer_architecture_positional_encoding/"}
        ],
        "practice_questions": [
            "Why do Transformers require positional encodings?",
            "What is the advantage of using sinusoidal positional encodings over learned embeddings?"
        ]
    },
    {
        "topic": "Transformers",
        "concept": "Encoder-Decoder Architecture",
        "difficulty_level": "intermediate",
        "content": "The original Transformer uses a dual architecture: the encoder processes the source sequence into continuous representations, while the decoder autoregressively generates the target sequence, utilizing cross-attention over the encoder's outputs.",
        "estimated_completion_time": "40 minutes",
        "resource_type": "article",
        "source_quality": 4.8,
        "resources": [
            {"title": "Transformer Architecture Explained (Machine Learning Mastery)", "url": "https://machinelearningmastery.com/the-transformer-model/"}
        ],
        "practice_questions": [
            "How does cross-attention differ from self-attention in the decoder?",
            "Describe the masking applied in decoder self-attention and explain why it is necessary."
        ]
    },
    {
        "topic": "Transformers",
        "concept": "Training Concepts",
        "difficulty_level": "advanced",
        "content": "Training Transformers involves optimization techniques such as learning rate warmup, the AdamW optimizer (with weight decay), label smoothing to prevent overconfidence, and gradient clipping to avoid exploding gradients.",
        "estimated_completion_time": "50 minutes",
        "resource_type": "interactive_exercise",
        "source_quality": 4.6,
        "resources": [
            {"title": "Hugging Face Training Guides", "url": "https://huggingface.co/docs/transformers/training"}
        ],
        "practice_questions": [
            "What is learning rate warmup and why is it critical for Transformer training?",
            "How does AdamW differ from standard Adam optimization?"
        ]
    },
    # RAG concepts
    {
        "topic": "RAG",
        "concept": "Chunking",
        "difficulty_level": "beginner",
        "content": "Chunking splits large documents into smaller segments to fit within LLM context windows and ensure focused retrieval. Techniques include fixed-size sliding window, paragraph/sentence splitting, and semantic layout-aware chunking.",
        "estimated_completion_time": "25 minutes",
        "resource_type": "article",
        "source_quality": 4.7,
        "resources": [
            {"title": "Pinecone Guide to Chunking", "url": "https://www.pinecone.io/learn/chunking-strategies/"}
        ],
        "practice_questions": [
            "What are the trade-offs of using large chunk sizes vs small chunk sizes?",
            "Why is overlap between chunks important during document ingestion?"
        ]
    },
    {
        "topic": "RAG",
        "concept": "Embeddings",
        "difficulty_level": "beginner",
        "content": "Embeddings convert text chunks into dense, high-dimensional vector representations that capture semantic meaning. Common models include OpenAI embeddings, Cohere embeddings, or open-source models like BGE or E5.",
        "estimated_completion_time": "20 minutes",
        "resource_type": "documentation",
        "source_quality": 4.8,
        "resources": [
            {"title": "OpenAI Embeddings API Reference", "url": "https://platform.openai.com/docs/guides/embeddings"}
        ],
        "practice_questions": [
            "How does cosine similarity measure semantic closeness between two embedding vectors?",
            "What is the impact of embedding model dimensionality on search efficiency and accuracy?"
        ]
    },
    {
        "topic": "RAG",
        "concept": "Retrieval",
        "difficulty_level": "intermediate",
        "content": "Retrieval searches the vector database to retrieve the top-K chunks most relevant to a query. Methods include standard vector search (KNN/ANN), keyword search (BM25), and hybrid search combining dense and sparse indices.",
        "estimated_completion_time": "35 minutes",
        "resource_type": "article",
        "source_quality": 4.9,
        "resources": [
            {"title": "LlamaIndex Retrieval Documentation", "url": "https://docs.llamaindex.ai/en/stable/module_guides/querying/retriever/"}
        ],
        "practice_questions": [
            "Explain hybrid retrieval and how dense and sparse scores are fused (e.g. via RRF).",
            "What is retrieval latency and how can it be optimized?"
        ]
    },
    {
        "topic": "RAG",
        "concept": "Re-ranking",
        "difficulty_level": "advanced",
        "content": "Re-ranking utilizes a secondary cross-encoder model to re-evaluate the relevance of the retrieved top-K chunks. Cross-encoders examine query and document interactions directly, yielding highly accurate relevance scores at higher computational cost.",
        "estimated_completion_time": "40 minutes",
        "resource_type": "article",
        "source_quality": 4.8,
        "resources": [
            {"title": "Cohere Rerank Introduction", "url": "https://txt.cohere.com/rerank/"}
        ],
        "practice_questions": [
            "Why is a two-stage retrieval (dense search + re-ranking) system used in production?",
            "Compare bi-encoders vs cross-encoders in terms of performance and computational complexity."
        ]
    },
    {
        "topic": "RAG",
        "concept": "Vector Databases",
        "difficulty_level": "intermediate",
        "content": "Vector databases index and store dense vector representations to allow fast approximate nearest neighbor (ANN) search. Examples include Qdrant, Pinecone, Milvus, and pgvector. They support metadata filtering, indexing structures like HNSW, and clustering.",
        "estimated_completion_time": "30 minutes",
        "resource_type": "documentation",
        "source_quality": 4.8,
        "resources": [
            {"title": "Qdrant Architecture Overview", "url": "https://qdrant.tech/documentation/concepts/"}
        ],
        "practice_questions": [
            "What is HNSW and how does it speed up vector similarity search?",
            "How does metadata filtering work in vector databases during the search process?"
        ]
    },
    # Deep Learning concepts
    {
        "topic": "Deep Learning",
        "concept": "Neural Networks & Activation Functions",
        "difficulty_level": "beginner",
        "content": "Neural networks are layers of nodes that learn abstract representations. Activation functions introduce non-linearity, allowing the network to learn complex boundaries. Standard activations include ReLU, GeLU, Sigmoid, and Tanh.",
        "estimated_completion_time": "25 minutes",
        "resource_type": "video",
        "source_quality": 4.9,
        "resources": [
            {"title": "3Blue1Brown Deep Learning Series", "url": "https://www.3blue1brown.com/topics/neural-networks"}
        ],
        "practice_questions": [
            "Why is non-linearity necessary in a neural network?",
            "What are the benefits of GELU over standard ReLU in modern architectures like BERT or GPT?"
        ]
    },
    {
        "topic": "Deep Learning",
        "concept": "Backpropagation & Optimizers",
        "difficulty_level": "intermediate",
        "content": "Backpropagation computes the gradient of the loss function with respect to weights using the chain rule. Optimizers use these gradients to update weights to minimize loss. Common optimizers: SGD, Momentum, RMSprop, and Adam.",
        "estimated_completion_time": "45 minutes",
        "resource_type": "article",
        "source_quality": 4.8,
        "resources": [
            {"title": "Calculus of Backpropagation (Colah)", "url": "https://colah.github.io/posts/2015-08-Backprop/"}
        ],
        "practice_questions": [
            "Walk through the mathematical formulation of backpropagation for a single layer.",
            "Explain how the Adam optimizer combines ideas from momentum and RMSprop."
        ]
    },
    {
        "topic": "Deep Learning",
        "concept": "Loss Functions",
        "difficulty_level": "beginner",
        "content": "Loss functions measure the discrepancy between prediction and true target. Choice of loss depends on task: Cross-Entropy for classification, MSE/MAE for regression, and contrastive loss for embedding systems.",
        "estimated_completion_time": "20 minutes",
        "resource_type": "documentation",
        "source_quality": 4.7,
        "resources": [
            {"title": "PyTorch Loss Functions Reference", "url": "https://pytorch.org/docs/stable/nn.html#loss-functions"}
        ],
        "practice_questions": [
            "Why is Cross-Entropy loss preferred over MSE for multi-class classification?",
            "What is Huber loss and in what scenario is it preferred over MSE or MAE?"
        ]
    },
    {
        "topic": "Deep Learning",
        "concept": "Regularization (Dropout)",
        "difficulty_level": "intermediate",
        "content": "Dropout is a powerful regularization technique where randomly selected neurons are ignored ('dropped out') during training. This prevents co-adaptation of features and forces the network to learn robust representation ensembles.",
        "estimated_completion_time": "25 minutes",
        "resource_type": "article",
        "source_quality": 4.8,
        "resources": [
            {"title": "Dropout Paper (Srivastava et al.)", "url": "https://jmlr.org/papers/v15/srivastava14a.html"}
        ],
        "practice_questions": [
            "How does dropout behavior differ between training and evaluation phases?",
            "Explain the scaling factor applied to activations when using dropout."
        ]
    }
]

def seed_qdrant_kb():
    """
    Seeds the local Qdrant Vector database with detailed concept resource cards.
    If GEMINI_API_KEY is not set or valid, disables vector ingestion and logs a warning.
    """
    if QdrantClient is None or q_models is None:
        print("[WARNING] qdrant_client is not installed in the active environment. Skipping vector database ingestion.")
        return False

    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key or api_key == "placeholder_api_key" or api_key == "your_gemini_api_key_here":
        print("[WARNING] GEMINI_API_KEY is not configured. Skipping vector database ingestion; local keyword lookup is enabled.")
        return False
        
    db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "qdrant_db")
    client = QdrantClient(path=db_path)
    
    collection_name = "global_knowledge_base"
    
    try:
        # Recreate collection to ensure clean structure matching 768 dimensions
        client.recreate_collection(
            collection_name=collection_name,
            vectors_config=q_models.VectorParams(
                size=768,
                distance=q_models.Distance.COSINE
            )
        )
        print(f"Collection '{collection_name}' initialized successfully.")
        
        # Load and call langchain-google-genai embeddings inside function
        from langchain_google_genai import GoogleGenerativeAIEmbeddings
        embeddings_model = GoogleGenerativeAIEmbeddings(
            model="models/text-embedding-004",
            google_api_key=api_key
        )
        
        print("Embedding knowledge base records using Gemini API...")
        points = []
        for idx, item in enumerate(KNOWLEDGE_DATA):
            # Formulate query text for embedding
            text_to_embed = f"{item['topic']} {item['concept']} {item['content']}"
            vector = embeddings_model.embed_query(text_to_embed)
            
            payload = {
                "topic": item["topic"],
                "concept": item["concept"],
                "difficulty_level": item["difficulty_level"],
                "content": item["content"],
                "estimated_completion_time": item["estimated_completion_time"],
                "resource_type": item["resource_type"],
                "source_quality": item["source_quality"],
                "resources": item["resources"],
                "practice_questions": item["practice_questions"]
            }
            
            points.append(
                q_models.PointStruct(
                    id=str(uuid.uuid4()),
                    vector=vector,
                    payload=payload
                )
            )
            
        client.upsert(
            collection_name=collection_name,
            points=points
        )
        print(f"[SUCCESS] Successfully seeded {len(points)} points into Qdrant collection '{collection_name}'.")
        return True
        
    except Exception as e:
        print(f"[ERROR] Failed to seed Qdrant database: {e}. Falling back to local keyword lookup.")
        return False

if __name__ == "__main__":
    seed_qdrant_kb()
