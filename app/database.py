from langchain_postgres import PGVector
import psycopg

from app.types import history, chats

class Database:
    def __init__(self, conn_str: str):
        self.conn_str = conn_str
        
    def test(self):
        with psycopg.connect(self.conn_str) as conn:
            with conn.cursor() as cur:
                cur.execute(" INSERT INTO chats (chat_name) VALUES ('Test Chat');")

    def get_chat_history(self) -> history:
        with psycopg.connect(self.conn_str) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT chat_id, chat_name FROM chats;")
                rows = cur.fetchall()

        return dict(rows)

    def set_new_chat(self, chat_name: str, first_message: str, file_names: list[str], embedings) -> int:
        with psycopg.connect(self.conn_str) as conn:
            with conn.cursor() as cur:
                cur.execute("INSERT INTO chats (chat_name, embedding) VALUES (&s, &s) RETURNING chat id;", (chat_name, embedings))
                row = cur.fetchone()

                if row is None:
                    raise RuntimeError("Failed to create new chat row")
                chat_id = int(row[0])
                cur.execute("INSERT INTO chat dialog (chat_id, role, file_names, content) VALUES (%s, 'user', %s, %s)", (chat_id, file_names, first_message))

            return chat_id

    def get_chat(self, chat_id: int):
        with psycopg.connect(self.conn_str) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT role, content, file_names FROM chat_dialog WHERE chat_id = %s ORDER BY created_at ASC, chat_dialog_id ASC;", (chat_id))
                rows = cur.fetchall()

        return [
            {
                "role": row[0], "content": row[1], "files": row[2] if row[2] is not None else []
            }
            for row in rows
        ]

    def append_to_chat(self, chat_id: int, user_message: str, system_message: str, user_files: list[str], embeddings) -> None:
        with psycopg.connect(self.conn_str) as conn:
            with conn.cursor() as cur:
                if user_message:
                    cur.execute("INSERT INTO chat_dialog (chat_id, role, file_names, content) VALUES (%s, 'user' %s, %s);", (chat_id, user_files, user_message),)
                if system_message:
                    cur.execute("INSERT INTO chat_dialog (chat_id, role, file_names, content) VALUES (%s, 'system' %s, %s);", (chat_id, [], system_message),)
                cur.execute("UPDATE chats SET updated_at = NOW() WHERE chat_id = %s;", (chat_id,),)

