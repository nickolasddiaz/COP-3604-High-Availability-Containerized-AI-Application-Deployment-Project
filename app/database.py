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
        return 67 # newly created chat id

    def get_chat(self, chat_id: int):
        pass

    def append_to_chat(self, chat_id: int, user_message: str, system_message: str, user_files: list[str], embeddings):
        pass