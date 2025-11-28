import asyncio
import nest_asyncio
from typing import List
from semantic_kernel.agents import ChatCompletionAgent, ChatHistoryAgentThread
from semantic_kernel.connectors.ai.open_ai import OpenAIChatCompletion
from semantic_kernel.functions import kernel_function
from Plugins.SchemaGroundingPlugin import SchemaGroundingPlugin
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
    name="BuilderAgent",
    instructions=QUERY_BUILDER_AGENT_PROMPT
)

Evaluation_Agent = ChatCompletionAgent(
    service=chat_completion_service,
    name="EvaluationAgent",
    instructions=EVALUATION_AGENT_PROMPT
)

Debug_Agent = ChatCompletionAgent(
    service=chat_completion_service,
    name="DebugAgent",
    instructions=DEBUG_AGENT_PROMPT
)

Explanation_Agent = ChatCompletionAgent(
    service=chat_completion_service,
    name="ExplanationAgent",
    instructions=EXPLANATION_AGENT_PROMPT
)



Orchestrator_Agent = ChatCompletionAgent(
    service=chat_completion_service,
    name="OrchestratorAgent",
    instructions=ORCHESTRATOR_AGENT_PROMPT,
    plugins=[Explanation_Agent,Debug_Agent,Evaluation_Agent,Builder_Agent,SchemaGroundingPlugin()]
)

test_agent = ChatCompletionAgent(
    service=chat_completion_service,
    name="testAgent",
    instructions="Return from the pligin",
    plugins=[SchemaGroundingPlugin()]
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
