from langchain_postgres import PGVector
import psycopg

from app.types import embedings_into_string, history, chats, embedding_list, chats_with_embeddings

class Database:
    def __init__(self, conn_str: str):
        self.conn_str = conn_str
        with psycopg.connect(self.conn_str) as conn:
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


    def set_new_chat(self, chat_name: str, user_message: str, system_message: str, file_names: list[str], current_embeddings: embedding_list|None) -> int:
        with psycopg.connect(self.conn_str) as conn:
            with conn.transaction():
                with conn.cursor() as cur:
                    cur.execute("INSERT INTO chats (chat_name) VALUES (%s) RETURNING chat_id;", (chat_name,))
                    row = cur.fetchone()

                if row is None:
                    raise RuntimeError("Failed to create new chat row")
                chat_id = int(row[0])
                user_embedding = embedings_into_string(current_embeddings)
                conn.execute(
                    "INSERT INTO chat_dialog (chat_id, role, file_names, embedding, message)"
                    "VALUES (%s, 'user', %s, %s::vector, %s)",
                    (chat_id, file_names, user_embedding, user_message),
                )
                conn.execute("INSERT INTO chat_dialog (chat_id, role, message) VALUES (%s, 'system', %s)", (chat_id, system_message))

            return chat_id

    def get_chat(self, chat_id: int) -> list[chats]:
        with psycopg.connect(self.conn_str) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT role, message, file_names FROM chat_dialog WHERE chat_id = %s ORDER BY created_at ASC, chat_dialog_id ASC;", (chat_id,))
                rows = cur.fetchall()

        return [
            {
                "role": row[0], "content": row[1], "files": row[2] if row[2] is not None else []
            }
            for row in rows
        ]

    def get_chat_with_embeddings(self, chat_id: int) -> list[chats_with_embeddings]:
            with psycopg.connect(self.conn_str) as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT role, message, file_names, embedding FROM chat_dialog WHERE chat_id = %s ORDER BY created_at ASC, chat_dialog_id ASC;", (chat_id,))
                    rows = cur.fetchall()
    
            return [
                {
                    "role": row[0],
                    "content": row[1],
                    "files": row[2] if row[2] is not None else [],
                    "embeddings": row[3] if row[3] is not None else []
                }
                for row in rows
            ]

    def append_to_chat(self, chat_id: int, user_message: str, system_message: str, user_files: list[str], current_embeddings: embedding_list|None) -> None:
        with psycopg.connect(self.conn_str) as conn:
            with conn.transaction():
                user_embedding = embedings_into_string(current_embeddings)
                conn.execute("INSERT INTO chat_dialog (chat_id, role, file_names, embedding, message) VALUES (%s, 'user', %s, %s::vector,  %s);", (chat_id, user_files, user_embedding, user_message))
                conn.execute("INSERT INTO chat_dialog (chat_id, role, message) VALUES (%s, 'system', %s);", (chat_id, system_message))
                conn.execute("UPDATE chats SET updated_at = NOW() WHERE chat_id = %s;", (chat_id,),)

