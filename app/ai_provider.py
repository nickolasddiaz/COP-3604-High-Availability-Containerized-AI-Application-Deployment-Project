from abc import ABC, abstractmethod
from typing import Literal
from langchain.chat_models import BaseChatModel
from langchain_core.messages import BaseMessage
from langchain_openrouter import ChatOpenRouter
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from app.types import chats

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
    """Abstract base class for AI inference providers."""


    def __init__(self, client: BaseChatModel):
        self._client = client
        self._chatNameChain = chatNameTemplate | self._client
        self._mainPromptChain = mainPrompt | self._client
    
    
    @abstractmethod
    def invoke(self, messages: list[BaseMessage]) -> str:
        """Send a list of messages to the model and return the string response."""
        pass

    def generateNameofChat(self, prompt: str) -> str:
        response = self._chatNameChain.invoke({
            "user_input": prompt,
        })
        if isinstance(response, dict):
            return str(response.get("content", "Homework Help"))
        return str(response.content)

    def askQuestion(self, prompt: str, chat_history: list[chats] = []) -> str:
        history: list[tuple[Literal["user", "system"], str]] = [
            (chat["role"], chat["content"]) for chat in chat_history
        ]
        response = self._mainPromptChain.invoke({
            "history": history,
            "user_input": prompt,
        })
        return str(response.content)
    


class OpenRouterProvider(AIProvider):
    """OpenRouter implementation using LangChain's ChatOpenRouter."""
    
    def __init__(self, api_key: str, model_name: str):
        client = ChatOpenRouter(
            model=model_name,
            temperature=0.7,
            api_key=api_key, # type: ignore
            base_url="https://openrouter.ai/api/v1",
            default_headers={
                "HTTP-Referer": "https://github.com/nickolasddiaz/COP-3604-High-Availability-Containerized-AI-Application-Deployment-Project",
                "X-Title": "COP-3604 AI Tutor Project"
            }
        )
        super().__init__(client)

    def invoke(self, messages: list[BaseMessage]) -> str:
        response = self._client.invoke(messages)
        return str(response.content)


class LocalOllamaProvider(AIProvider):
    """Local Ollama implementation using LangChain's ChatOllama or something else."""
    
    def __init__(self, model_name: str, base_url: str):
        # self.client = ChatOllama(
        #     model=model_name,
        #     base_url=base_url
        # )
        super().__init__("client") # type: ignore

    def invoke(self, messages: list[BaseMessage]) -> str:
        # response = self.client.invoke(messages)
        # return str(response.content)
        return ""


def get_ai_provider(app_config) -> AIProvider:
    """Factory function that returns the appropriate AI provider 
    based on the LOCAL_AI_DEV toggle in configuration.
    """
    if app_config["LOCAL_AI_DEV"]:
        return LocalOllamaProvider(
            model_name=app_config["LOCAL_MODEL"],
            base_url=app_config["LOCAL_MODEL_URL"]
        )
    else:
        return OpenRouterProvider(
            api_key=app_config["OPENROUTER_API_KEY"],
            model_name=app_config["OPENROUTER_MODEL"]
        )