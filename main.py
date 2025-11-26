import asyncio
import nest_asyncio
from typing import List
from semantic_kernel.agents import ChatCompletionAgent, ChatHistoryAgentThread
from semantic_kernel.connectors.ai.open_ai import OpenAIChatCompletion
from semantic_kernel.functions import kernel_function

import os
from dotenv import load_dotenv

from Prompt import QUERY_BUILDER_AGENT_PROMPT, EVALUATION_AGENT_PROMPT, DEBUG_AGENT_PROMPT, EXPLANATION_AGENT_PROMPT, ORCHESTRATOR_AGENT_PROMPT

nest_asyncio.apply()

load_dotenv()

key=os.getenv("OPENAI_KEY")

chat_completion_service = OpenAIChatCompletion(
    service_id="chat-gpt",
    ai_model_id="gpt-5-nano",
    api_key=key 
)


Builder_Agent = ChatCompletionAgent(
    service=chat_completion_service,
    name="Builder Agent",
    instructions=QUERY_BUILDER_AGENT_PROMPT
)

Evaluation_Agent = ChatCompletionAgent(
    service=chat_completion_service,
    name="Evaluation Agent",
    instructions=EVALUATION_AGENT_PROMPT
)

Debug_Agent = ChatCompletionAgent(
    service=chat_completion_service,
    name="Debug Agent",
    instructions=DEBUG_AGENT_PROMPT
)

Explanation_Agent = ChatCompletionAgent(
    service=chat_completion_service,
    name="Explanation Agent",
    instructions=EXPLANATION_AGENT_PROMPT
)



Orchestrator_Agent = ChatCompletionAgent(
    service=chat_completion_service,
    name="Orchestrator Agent",
    instructions=ORCHESTRATOR_AGENT_PROMPT,
    plugins=[]
)


thread = ChatHistoryAgentThread()


async def main() -> None:
    print("Welcome to the chat bot!\n  Type 'exit' to exit.\n")
    while True:
        user_input = input("User> ")
        if user_input.lower().strip() == "exit":
            print("\nExiting chat...")
            return
        response = await Orchestrator_Agent.get_response(messages=user_input, thread=thread)
        print(f"Agent> {response}")

asyncio.run(main())
