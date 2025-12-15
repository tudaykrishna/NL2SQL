from semantic_kernel.agents import Agent, ChatCompletionAgent
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
import os
from dotenv import load_dotenv
from semantic_kernel import Kernel
from semantic_kernel.agents import ChatCompletionAgent, ChatHistoryAgentThread
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion, AzureChatPromptExecutionSettings
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior
import asyncio
from pathlib import Path
import sys

# Ensure project root is on sys.path so sibling packages can be imported when running directly
_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_root))

from Tools.Plugin import SchemaGroundingPlugin
from Prompt.Prompt import (
    QUERY_BUILDER_AGENT_PROMPT,
    EVALUATION_AGENT_PROMPT,
    DEBUG_AGENT_PROMPT,
    EXPLANATION_AGENT_PROMPT,
    ORCHESTRATOR_AGENT_PROMPT,
)

# Load environment variables
load_dotenv()

# Environment variables
key = os.getenv("incubator_key")
model = os.getenv("model")
endpoint = os.getenv("incubator_endpoint")

# Azure chat completion setup
chat_completion_service = AzureChatCompletion(
    deployment_name=model,
    api_key=key,
    endpoint=endpoint,
)

def get_agents() -> list[Agent]:

    Builder_Agent= ChatCompletionAgent(
        name="BuilderAgent",
        description="An agent that builds SQL queries from natural language.",
        instructions=QUERY_BUILDER_AGENT_PROMPT,
        service=chat_completion_service,
        plugins=[SchemaGroundingPlugin()]
    )

    Evaluation_Agent = ChatCompletionAgent(
        description="An agent that evaluates SQL queries for correctness and efficiency.",
        service=chat_completion_service,
        name="EvaluationAgent",
        instructions=EVALUATION_AGENT_PROMPT
    )

    Debug_Agent = ChatCompletionAgent(
        description="An agent that debugs SQL queries and provides explanations.",
        service=chat_completion_service,
        name="DebugAgent",
        instructions=DEBUG_AGENT_PROMPT
    )

    Explanation_Agent = ChatCompletionAgent(
        description="An agent that explains SQL queries in natural language.",
        service=chat_completion_service,
        name="ExplanationAgent",
        instructions=EXPLANATION_AGENT_PROMPT
    )


    return [Builder_Agent,Evaluation_Agent,Debug_Agent,Explanation_Agent]


from semantic_kernel.contents import ChatMessageContent

def agent_response_callback(message: ChatMessageContent) -> None:
    print(f"**{message.name}**\n{message.content}")


from semantic_kernel.agents import GroupChatOrchestration, RoundRobinGroupChatManager

agents = get_agents()
group_chat_orchestration = GroupChatOrchestration(
    members=agents,
    manager=RoundRobinGroupChatManager(max_rounds=5),  # Odd number so writer gets the last word
    agent_response_callback=agent_response_callback,
)

from semantic_kernel.agents.runtime import InProcessRuntime

runtime = InProcessRuntime()

async def main():
    runtime.start()

    orchestration_result = await group_chat_orchestration.invoke(
        task="name all the employees born on 31st august 1992",
        runtime=runtime,
    )

    value = await orchestration_result.get()
    print(f"***** Final Result *****\n{value}")

if __name__ == "__main__":
    asyncio.run(main())