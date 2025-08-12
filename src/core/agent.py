from langchain_core.prompts import ChatPromptTemplate
from langchain.agents import create_openai_functions_agent, AgentExecutor

from src.core.llm import llm

class Agent:
    def __init__(self, tools: list, prompt: ChatPromptTemplate):
        self.tools = tools
        self.prompt = prompt
        self.llm = llm.get_model_info()
        agent = create_openai_functions_agent(self.llm, self.tools, self.prompt)
        self.agent_executor = AgentExecutor(agent=agent, tools=self.tools, verbose=True)

    def get_agent_executor(self) -> AgentExecutor:
        return self.agent_executor