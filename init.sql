SELECT 'CREATE DATABASE mydatabase'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'mydatabase')
\gexec
\connect mydatabase

CREATE EXTENSION IF NOT EXISTS vector;

-- BIGSERIAL is autoincrementing
CREATE TABLE IF NOT EXISTS chats (
    chat_id BIGSERIAL PRIMARY KEY,
    chat_name TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS chat_dialog (
    chat_dialog_id BIGSERIAL PRIMARY KEY,
    chat_id BIGINT NOT NULL REFERENCES chats(chat_id) ON DELETE CASCADE, -- deletes the rows in chat_dialog matching the deleted chat_id
    role TEXT NOT NULL CHECK (role IN ('system', 'user')),
    file_names TEXT[] NOT NULL DEFAULT '{}',
    message TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- RAG document chunks populated by rag-database/ingest.py
CREATE TABLE IF NOT EXISTS document_chunks (
    chunk_id        BIGSERIAL PRIMARY KEY,
    chat_dialog_id  BIGINT REFERENCES chat_dialog(chat_dialog_id) ON DELETE CASCADE,
    source_file     TEXT NOT NULL,              -- Cited in RAG answers
    chunk_index     INTEGER NOT NULL,
    content         TEXT NOT NULL,
    embedding       vector(768) NOT NULL        -- Match EMBEDDING_DIM (768 for nomic-embed-text)
);

-- index for the text embeddings
CREATE INDEX IF NOT EXISTS idx_document_chunks_embedding_hnsw
    ON document_chunks USING hnsw (embedding vector_cosine_ops);

-- index for the chat dialog/chat it
CREATE INDEX IF NOT EXISTS idx_chat_dialog_chat_id
    ON chat_dialog (chat_id, created_at);
