from src.config import Settings
from langchain_openai import ChatOpenAI

from src.config import settings

class LLM:
    """
    Represents a Language Model (LLM) configuration for interacting with OpenAI's API.
    """

    def __init__(self):
        self.model = settings.OPENAI_MODEL
        self.api_key = settings.OPENAI_API_KEY
        self.temperature = 0.7
        self.streaming = True

    def get_model_info(self) -> ChatOpenAI:
        """
        Returns the model information for the LLM.

        Returns:
            BaseChatModel: The configured chat model.
        """
        return ChatOpenAI(
            model=self.model,
            api_key=self.api_key,
            temperature=self.temperature,
            streaming=self.streaming
        )

llm = LLM()