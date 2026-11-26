from langchain_postgres import PGVector
import psycopg

from app.types import embedding_to_pgvector, history, chats, embedding_vector, DocumentChunk, RetrievedChunk

class Database:
    def __init__(self, conn_str: str):
        self.conn_str = conn_str
        with psycopg.connect(self.conn_str, connect_timeout=5) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT version();")
                row = cur.fetchone()
                version = row[0] if row is not None else None

        if version is None:
            raise Exception("Postgress did not work")
        
    def get_chat_history(self) -> history:
        with psycopg.connect(self.conn_str) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT chat_id, chat_name FROM chats;")
                rows = cur.fetchall()

        return dict(rows)

    def create_chat(self, chat_name: str) -> int:
        with psycopg.connect(self.conn_str) as conn:
            with conn.cursor() as cur:
                cur.execute("INSERT INTO chats (chat_name) VALUES (%s) RETURNING chat_id;", (chat_name,))
                row = cur.fetchone()

        if row is None:
            raise RuntimeError("Failed to create new chat row")
        return int(row[0])

    def delete_chat(self, chat_id: int) -> None:
        """Cascades to chat_dialog and document_chunks."""
        with psycopg.connect(self.conn_str) as conn:
            conn.execute("DELETE FROM chats WHERE chat_id = %s;", (chat_id,))


    def get_chat(self, chat_id: int) -> list[chats]:
        with psycopg.connect(self.conn_str) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT role, message, file_names FROM chat_dialog "
                    "WHERE chat_id = %s ORDER BY created_at ASC, chat_dialog_id ASC;",
                    (chat_id,),
                )
                rows = cur.fetchall()

        return [
            {
                "role": row[0], "content": row[1], "files": row[2] if row[2] is not None else []
            }
            for row in rows
        ]


    def add_user_message(
        self,
        chat_id: int,
        message: str,
        file_names: list[str],
        chunks: list[DocumentChunk],
    ) -> int:
        """Store the user's message and the chunks of any files they uploaded, atomically.
        Returns the chat_dialog_id of the new message."""
        with psycopg.connect(self.conn_str) as conn:
            with conn.transaction():
                with conn.cursor() as cur:
                    cur.execute(
                        "INSERT INTO chat_dialog (chat_id, role, file_names, message) "
                        "VALUES (%s, 'user', %s, %s) RETURNING chat_dialog_id;",
                        (chat_id, file_names, message),
                    )
                    row = cur.fetchone()
                    if row is None:
                        raise RuntimeError("Failed to insert user message")
                    chat_dialog_id = int(row[0])

                    if chunks:
                        cur.executemany(
                            "INSERT INTO document_chunks "
                            "(chat_id, chat_dialog_id, source_file, chunk_index, content, embedding) "
                            "VALUES (%s, %s, %s, %s, %s, %s::vector);",
                            [
                                (
                                    chat_id,
                                    chat_dialog_id,
                                    c["source_file"],
                                    c["chunk_index"],
                                    c["content"],
                                    embedding_to_pgvector(c["embedding"]),
                                )
                                for c in chunks
                            ],
                        )
        return chat_dialog_id

    def add_system_message(self, chat_id: int, message: str) -> None:
        with psycopg.connect(self.conn_str) as conn:
            with conn.transaction():
                conn.execute(
                    "INSERT INTO chat_dialog (chat_id, role, message) VALUES (%s, 'system', %s);",
                    (chat_id, message),
                )
                conn.execute("UPDATE chats SET updated_at = NOW() WHERE chat_id = %s;", (chat_id,))

    def delete_dialog_message(self, chat_dialog_id: int) -> None:
        """Used to roll back a user message if answering failed.
        Cascades to the document_chunks uploaded with that message."""
        with psycopg.connect(self.conn_str) as conn:
            conn.execute("DELETE FROM chat_dialog WHERE chat_dialog_id = %s;", (chat_dialog_id,))

    def chat_has_chunks(self, chat_id: int) -> bool:
        """Cheap check so we can skip embedding the query for chats without documents."""
        with psycopg.connect(self.conn_str) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT EXISTS (SELECT 1 FROM document_chunks WHERE chat_id = %s);",
                    (chat_id,),
                )
                row = cur.fetchone()
        return row is not None and bool(row[0])

    def search_chunks(self, chat_id: int, query_embedding: embedding_vector, k: int = 4) -> list[RetrievedChunk]:
        """Return the k chunks in this chat closest to the query (cosine distance)."""
        vector = embedding_to_pgvector(query_embedding)
        with psycopg.connect(self.conn_str) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT source_file, chunk_index, content, embedding <=> %s::vector AS distance "
                    "FROM document_chunks "
                    "WHERE chat_id = %s "
                    "ORDER BY embedding <=> %s::vector "
                    "LIMIT %s;",
                    (vector, chat_id, vector, k),
                )
                rows = cur.fetchall()

        return [
            {
                "source_file": row[0],
                "chunk_index": row[1],
                "content": row[2],
                "distance": float(row[3]),
            }
            for row in rows
        ]

