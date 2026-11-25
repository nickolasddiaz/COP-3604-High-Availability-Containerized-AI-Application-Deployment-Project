from PyPDF2 import PdfReader 
from pdfplumber import pdf
from langchain_text_splitters import RecursiveCharacterTextSplitter
# from sentence_transformers import SentenceTransformer, util
import time
from gpt4all import GPT4All  

from numba import jit, cuda
import numpy as np

import hashlib
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pgvector.psycopg import register_vector
from pypdf import PdfReader
import psycopg

"""
    Build image with "docker build -t rag-db-image ."
    
    Run image with "docker run -e POSTGRES_USER=user \
    -e POSTGRES_PASSWORD=password \
    -e POSTGRES_DB=rag-db \
    -p 5432:5432 rag-db-image"
    
    Build image and run container with "docker build -t rag-db-image . && \
    docker run -e POSTGRES_USER=user \
    -e POSTGRES_PASSWORD=password \
    -e POSTGRES_DB=rag-db \
    -p 5432:5432 rag-db-image"
    
    Open contianer with "docker compose up"
    Close container with "docker compose down"

    If these are not the imports that you use
    then please update the Dockerfile to have
    the correct imports in requirements.txt
    
    Also, if you use sentence_transformers
    then add it to requirements.txt
"""


# Ensure project root is on sys.path so `from app.ai_provider import ...` works
# whether run from repo root or inside the container.
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.ai_provider import get_embedding_provider  # noqa: E402


def build_db_dsn() -> str:
    """Build PostgreSQL connection string from .env variables used in compose.yaml."""
    return (
        f"host={os.getenv('DB_HOST', 'database')} "
        f"port={os.getenv('DB_PORT', '5432')} "
        f"dbname={os.environ['DB_NAME']} "
        f"user={os.environ['DB_USER']} "
        f"password={os.environ['DB_PASSWORD']}"
    )


def compute_chunk_hash(source_file: str, page_number: int, chunk_index: int, content: str) -> str:
    payload = f"{source_file}|{page_number}|{chunk_index}|{content}".encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def load_and_split_pdfs(pdf_dir: Path, chunk_size: int = 800, chunk_overlap: int = 150) -> list[dict]:
    """Read all PDFs in pdf_dir and split into overlapping chunks with citation metadata."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""],
    )

    chunks: list[dict] = []
    pdf_files = sorted(pdf_dir.glob("*.pdf"))
    if not pdf_files:
        print(f"[ingest] No PDF files found in {pdf_dir}")
        return chunks

    for pdf_path in pdf_files:
        reader = PdfReader(str(pdf_path))
        for page_idx, page in enumerate(reader.pages, start=1):
            raw_text = (page.extract_text() or "").strip()
            if not raw_text:
                continue

            split_texts = splitter.split_text(raw_text)
            for chunk_idx, text in enumerate(split_texts):
                cleaned = text.strip()
                if not cleaned:
                    continue
                chunks.append(
                    {
                        "chunk_hash": compute_chunk_hash(pdf_path.name, page_idx, chunk_idx, cleaned),
                        "source_file": pdf_path.name,
                        "page_number": page_idx,
                        "chunk_index": chunk_idx,
                        "content": cleaned,
                    }
                )

    return chunks


def ingest(batch_size: int = 32) -> None:
    load_dotenv()

    pdf_dir = Path(os.getenv("PDF_DIR", str(ROOT_DIR / "pdfs")))
    all_chunks = load_and_split_pdfs(pdf_dir)
    if not all_chunks:
        return

    provider = get_embedding_provider(dict(os.environ))
    active_model = provider.model_name
    dsn = build_db_dsn()

    with psycopg.connect(dsn) as conn:
        register_vector(conn)

        # Fetch existing hashes and which embedding model generated them
        with conn.cursor() as cur:
            cur.execute("SELECT chunk_hash, embedding_model FROM document_chunks;")
            existing = dict(cur.fetchall())

        # Skip chunks that already exist AND were embedded with the current model.
        # If you flip from OpenRouter -> Ollama, mismatched-model chunks are automatically re-embedded.
        to_process = [
            c for c in all_chunks
            if existing.get(c["chunk_hash"]) != active_model
        ]

        if not to_process:
            print(
                f"[ingest] Up to date: {len(all_chunks)} chunks already embedded "
                f"with '{active_model}'. Skipping."
            )
            return

        print(
            f"[ingest] Embedding {len(to_process)} chunks with '{active_model}' "
            f"(skipping {len(all_chunks) - len(to_process)} unchanged chunks)..."
        )

        inserted_or_updated = 0
        for start in range(0, len(to_process), batch_size):
            batch = to_process[start : start + batch_size]
            vectors = provider.embed_documents([c["content"] for c in batch])

            rows = [
                (
                    c["chunk_hash"],
                    c["source_file"],
                    c["page_number"],
                    c["chunk_index"],
                    c["content"],
                    active_model,
                    vec,
                )
                for c, vec in zip(batch, vectors)
            ]

            with conn.cursor() as cur:
                cur.executemany(
                    """
                    INSERT INTO document_chunks (
                        chunk_hash, source_file, page_number, chunk_index,
                        content, embedding_model, embedding
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (chunk_hash) DO UPDATE
                    SET embedding_model = EXCLUDED.embedding_model,
                        embedding       = EXCLUDED.embedding,
                        updated_at      = NOW()
                    WHERE document_chunks.embedding_model IS DISTINCT FROM EXCLUDED.embedding_model;
                    """,
                    rows,
                )
            conn.commit()
            inserted_or_updated += len(rows)
            print(f"[ingest] Committed {inserted_or_updated}/{len(to_process)} chunks.")

        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM document_chunks;")
            total = cur.fetchone()[0]
        print(f"[ingest] Done. Total chunks in database: {total}")


if __name__ == "__main__":
    ingest()