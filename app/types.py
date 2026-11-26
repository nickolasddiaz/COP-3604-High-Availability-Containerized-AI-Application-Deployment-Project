from typing import Literal, TypedDict

type history = dict[int, str]
type embedding_list = list[list[float]]

class chats(TypedDict):
    role: Literal['user', 'system']
    content: str
    files: list[str]

class chats_with_embeddings(chats):
    embeddings: embedding_list

def embedings_into_string(embeddings: embedding_list|None) -> str|None:
    if embeddings == None:
        return None

    return "[" + ",".join(map(str, embeddings[0])) + "]"