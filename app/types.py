from typing import Literal, TypedDict


class chats(TypedDict):
    role: Literal['user', 'system']
    content: str
    files: list[str]

# current_chat: list[chats] = [
#         {'role': 'user', 'content': 'Hello how are you.', 'files': ["test1.txt", "test2.txt", "test3.txt"]},
#         {'role': 'system', 'content': 'I am doing great, do you have any questions.', 'files': []},
#         {'role': 'user', 'content': 'pls let me pass on god.', 'files': ["plshelp.pdf"]},
#         {'role': 'system', 'content': 'you are beyond help.', 'files': []},
#     ]

type history = dict[int, str]