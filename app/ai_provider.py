from abc import ABC
import tempfile
from pathlib import Path
from typing import Literal, Mapping
from langchain.chat_models import BaseChatModel
from langchain_openrouter import ChatOpenRouter
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.embeddings import Embeddings
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_ollama import ChatOllama, OllamaEmbeddings
from werkzeug.datastructures import FileStorage
from app.types import embedding_list, chats_with_embeddings
from langchain_community.document_loaders import PyPDFLoader


default_headers: Mapping[str, str] = {
    "HTTP-Referer": "https://github.com/nickolasddiaz/COP-3604-High-Availability-Containerized-AI-Application-Deployment-Project",
    "X-Title": "COP-3604 AI Tutor Project",
}

base_url="https://openrouter.ai/api/v1"

chatNameTemplate = ChatPromptTemplate(
    [
    ("system", 
    '''
    You are a AI tutor chatbot. Your task is to generate a name for the chat.
    Keep it short no more that 8 words. Make the best guess.
    If there too little information return "Homework Help".

    Example human: "I need help studing for my chemistry test, I have been struggling on this problem Phosphoric acid, 
    H3PO4, is a triprooc acid. What is the total number of moles of H+ available for reaction in 3.50 L of 0.400 M H3PO4?"

    Example system: "Determining number of moles for a reaction."
    '''),
    ("human", "{user_input}"),
    ]
)

mainPrompt = ChatPromptTemplate([
    ("system", '''
    You are a AI tutor chatbot. You help students understand their material.
    If a student comes in with a direct question: give them some hints to try to help them solve that problem.
    When a student solution comes in, give a correction and the thought-process of the solution if they are wrong,
    If a student comes in with a set of materials/content, generate an appropriate set of questions to test their knowledge without giving out the answers at first
    If there is no content, or questions, ask the student to supply them to you.
    Make the best effort to accommodate the student on their quest.
    The app does not support Markdown yet, answer in normal text.

    Example human 1: "Hello I am struggling with my Calculus homework, I am not sure where to start"
    Example system 1: "I would love to help, but I need more information from you, perhaps could you give me a sample of the homework questions or the textbook"

    Example human 2: "I need help studing for my chemistry test, I have been struggling on this problem Phosphoric acid, 
            H3PO4, is a triprooc acid. What is the total number of moles of H+ available for reaction in 3.50 L of 0.400 M H3PO4?"

    Example system 2: "Hint: Multiply the volume of the solution by its molarity to get the moles. 
            Triprotic acid, each mole of acid can donate 3 moles of H+ ions during a complete reaction.
            Should be a more in depth explaination"

    Example human 3: "[answered the question based on the hints but got it wrong]"
    Example system 3: "[Correct the solution and tell him step by step where the student got wrong]"

    Example human 4: "[answered the question based on the hints and got it correct]"
    Example system 4: "[Congratulate the student on their success]"
    '''),
    MessagesPlaceholder("history"),
    ("human", "{user_input}"),
])

class AIProvider(ABC):
    """Abstract base class for AI inference providers.
       Using both ChatModel and Embedding models
    """

    def __init__(self, LLMclient: BaseChatModel, embed_client: Embeddings, embed_model_name: str):
        self._client = LLMclient
        self._chatNameChain = chatNameTemplate | self._client
        self._mainPromptChain = mainPrompt | self._client

        self._embed_client = embed_client
        self.embed_model_name = embed_model_name

    def generateNameofChat(self, prompt: str) -> str:
        response = self._chatNameChain.invoke({
            "user_input": prompt,
        })
        if isinstance(response, dict):
            return str(response.get("content", "Homework Help"))
        return str(response.content)

    def askQuestion(self, prompt: str, current_embedings: embedding_list | None, chat_history: list[chats_with_embeddings]) -> str:
        history: list[tuple[Literal["user", "system"], str]] = [
            (chat["role"], chat["content"]) for chat in chat_history
        ]
        embedding_context = {
            "current_embeddings": current_embedings,
            "chat_history_embeddings": [chat["embeddings"] for chat in chat_history],
        }
        response = self._mainPromptChain.invoke({
            "history": history,
            "user_input": prompt,
        })
        return str(response.content)

    @staticmethod
    def _load_txt_md_from_upload(file_storage: FileStorage) -> list[Document]:
        filename = Path(file_storage.filename or "upload.txt").name

        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / filename
            file_storage.save(str(path))
            text = path.read_text(encoding="utf-8")
        return [Document(page_content=text, metadata={"source": filename})]

    @staticmethod
    def _load_pdf_from_upload(file_storage: FileStorage) -> list[Document]:
        filename = Path(file_storage.filename or "upload.pdf").name

        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / filename
            file_storage.save(str(path))
            loader = PyPDFLoader(str(path))
            return loader.load()

    def embed_documents(self, files: list[FileStorage]) -> embedding_list:
        documents: list[Document] = []
        for file_storage in files:
            suffix = Path(file_storage.filename or "").suffix.lower()
            if suffix == ".pdf":
                documents.extend(self._load_pdf_from_upload(file_storage))
            elif suffix in {".txt", ".md"}:
                documents.extend(self._load_txt_md_from_upload(file_storage))
            else:
                raise ValueError("Only .pdf, .txt, and .md files are supported")

        if not documents:
            return []
        return self._embed_client.embed_documents(
            [document.page_content for document in documents]
        )

    

class OpenRouterProvider(AIProvider):
    """OpenRouter implementation using LangChain's ChatOpenRouter/OpenAIEmbeddings"""
    
    def __init__(self, api_key: str, model_name: str, embed_model_name: str, dimensions: int):
        client = ChatOpenRouter(
            model=model_name,
            temperature=0.7,
            api_key=api_key, # type: ignore
            base_url=base_url,
            default_headers=default_headers
        )
        embed_client = OpenAIEmbeddings(
            model=embed_model_name,
            api_key=api_key,  # type: ignore
            base_url=base_url,
            dimensions=dimensions,
            check_embedding_ctx_length=False,
            default_headers=default_headers,
        )
        super().__init__(client, embed_client, embed_model_name)


class LocalOllamaProvider(AIProvider):
    """Local Ollama implementation using LangChain's ChatOllama/OllamaEmbeddings"""
    
    def __init__(self, model_name: str, base_url: str, embed_model_name: str, embed_base_url: str, dimensions: int):
        client = ChatOllama(
            model=model_name,
            base_url=base_url
        )
        embed_client = OllamaEmbeddings(
            model=embed_model_name,
            base_url=embed_base_url,
            dimensions=dimensions
        )
        super().__init__(client, embed_client, embed_model_name)


def get_ai_provider(app_config) -> AIProvider:
    """Factory function that returns the appropriate AI provider 
    based on the LOCAL_AI_DEV toggle in the .env.
    """

    if app_config["LOCAL_AI_DEV"]:
        return LocalOllamaProvider(
            model_name=app_config["LOCAL_MODEL"],
            base_url=app_config["LOCAL_MODEL_URL"],
            embed_model_name=app_config["LOCAL_EMBED_MODEL"],
            embed_base_url=app_config["LOCAL_EMBED_MODEL_URL"],
            dimensions=app_config["EMBEDDING_DIM"],
        )
    else:
        return OpenRouterProvider(
            api_key=app_config["OPENROUTER_API_KEY"],
            model_name=app_config["OPENROUTER_MODEL"],
            embed_model_name=app_config["OPENROUTER_EMBED_MODEL"],
            dimensions=app_config["EMBEDDING_DIM"],
        )
