"""
Document ingestion script for the RAG pipeline.

Loads text files from the data directory, splits them into semantic chunks,
computes vector embeddings using SentenceTransformer, and stores them in PostgreSQL.
"""

import os
import sys
from pathlib import Path
from sentence_transformers import SentenceTransformer

# Ensure the backend directory is in sys.path when running this script directly
BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from rag.chunker import chunk_text
from db.models import Document
from db.connection import get_db

# Path to the data directory containing text documents
DATA_DIR = BACKEND_DIR.parent / "data"

# Load the sentence embedding model (all-MiniLM-L6-v2 produces 384-dimensional embeddings)
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
model = SentenceTransformer(EMBEDDING_MODEL_NAME)


def ingest_documents(data_dir: Path | str = DATA_DIR) -> None:
    """
    Ingest all .txt files from the data folder into the vector database.

    Steps:
      1. Clear existing rows from the documents table (full re-ingest).
      2. Find all .txt files in the target data directory.
      3. Chunk each file's text using chunk_text().
      4. Compute embeddings for each chunk using SentenceTransformer.
      5. Save chunks and their embeddings into the database.
      6. Commit changes and display an ingestion summary.
    """
    data_path = Path(data_dir)
    if not data_path.exists():
        print(f"Data directory '{data_path}' does not exist.")
        return

    # Obtain a database session using get_db()
    db_gen = get_db()
    db = next(db_gen)

    try:
        # Step 1: Clear existing rows from the documents table
        print("Clearing existing documents from the database...")
        deleted_count = db.query(Document).delete()
        db.commit()
        print(f"Cleared {deleted_count} existing document(s).")

        # Step 2: Loop through all .txt files in data folder
        txt_files = sorted(data_path.glob("*.txt"))
        print(f"Found {len(txt_files)} .txt file(s) in {data_path}")

        total_files_processed = 0
        total_chunks_created = 0

        for file_path in txt_files:
            print(f"Processing: {file_path.name}")

            # Step 3: Read text content and chunk it
            with open(file_path, "r", encoding="utf-8") as f:
                text_content = f.read()

            chunks = chunk_text(text_content)
            if not chunks:
                print(f"  No text or chunks extracted from {file_path.name}")
                continue

            print(f"  Split into {len(chunks)} chunk(s). Generating embeddings...")

            # Step 4 & 5: Generate embeddings and save Document rows
            for chunk in chunks:
                embedding = model.encode(chunk).tolist()
                doc = Document(
                    source_file=file_path.name,
                    chunk_text=chunk,
                    embedding=embedding,
                )
                db.add(doc)
                total_chunks_created += 1

            total_files_processed += 1

        # Step 6: Commit all changes to the database
        db.commit()
        print("Database commit successful.")

        # Step 7: Print summary
        print("\n" + "=" * 50)
        print("Ingestion Summary:")
        print(f"  Files processed : {total_files_processed}")
        print(f"  Total chunks    : {total_chunks_created}")
        print("=" * 50)

    except Exception as e:
        db.rollback()
        print(f"Error during document ingestion: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    ingest_documents()
