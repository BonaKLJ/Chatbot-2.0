"""
Document retrieval module for the RAG pipeline.

Uses SentenceTransformer to compute query embeddings and pgvector cosine distance
to fetch the most relevant document chunks from PostgreSQL.
"""

import sys
from pathlib import Path
from sentence_transformers import SentenceTransformer

# Ensure the backend directory is in sys.path when running this script directly
BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from db.models import Document
from db.connection import SessionLocal

# Load the sentence embedding model (same model as ingest.py: 384 dimensions)
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
model = SentenceTransformer(EMBEDDING_MODEL_NAME)


def retrieve_relevant_chunks(query: str, top_k: int = 3) -> list[str]:
    """
    Retrieve the top_k most relevant text chunks for a given query using vector similarity.

    Args:
        query: The user's search query or question.
        top_k: Number of most similar document chunks to return (default: 3).

    Returns:
        A list of matching chunk_text strings, ordered from most to least relevant.
    """
    # 1. Generate embedding for the input query
    query_embedding = model.encode(query).tolist()

    # 2. Open a database session
    db = SessionLocal()

    try:
        # 3. Query documents ordered by cosine distance to query embedding
        # pgvector's cosine_distance operator corresponds to <=> in SQL
        results = (
            db.query(Document)
            .order_by(Document.embedding.cosine_distance(query_embedding))
            .limit(top_k)
            .all()
        )

        # 4. Extract and return matching chunk_text strings
        return [doc.chunk_text for doc in results]

    finally:
        # 5. Ensure database session is always closed
        db.close()


if __name__ == "__main__":
    sample_query = "What programming languages does this person know?"
    print(f"Sample Query: '{sample_query}'\n")

    chunks = retrieve_relevant_chunks(sample_query, top_k=3)
    print(f"Retrieved {len(chunks)} relevant chunk(s):\n")

    for i, chunk in enumerate(chunks, start=1):
        print(f"--- Chunk {i} ---")
        print(chunk.strip())
        print()
