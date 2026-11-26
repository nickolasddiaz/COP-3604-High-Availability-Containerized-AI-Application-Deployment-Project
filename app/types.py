from typing import Literal, TypedDict

type history = dict[int, str]
type embedding_vector = list[float]


class chats(TypedDict):
    role: Literal['user', 'system']
    content: str
    files: list[str]


class DocumentChunk(TypedDict):
    """A chunk of an uploaded file, ready to be stored in document_chunks."""
    source_file: str
    chunk_index: int
    content: str
    embedding: embedding_vector


class RetrievedChunk(TypedDict):
    """A chunk returned by the similarity search (no embedding needed anymore)."""
    source_file: str
    chunk_index: int
    content: str
    distance: float  # cosine distance: 0 = identical, 2 = opposite


def embedding_to_pgvector(embedding: embedding_vector) -> str:
    """Serialize an embedding into pgvector's text format, e.g. '[0.1,0.2,0.3]'.
    Use together with a `%s::vector` cast in SQL."""
    return "[" + ",".join(map(str, embedding)) + "]"