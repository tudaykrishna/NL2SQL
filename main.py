import asyncio
import nest_asyncio
from typing import List
from semantic_kernel.agents import ChatCompletionAgent, ChatHistoryAgentThread
from semantic_kernel.connectors.ai.open_ai import OpenAIChatCompletion ,AzureChatCompletion
from semantic_kernel.functions import kernel_function

from Prompt import QUERY_BUILDER_AGENT_PROMPT, EVALUATION_AGENT_PROMPT, DEBUG_AGENT_PROMPT, EXPLANATION_AGENT_PROMPT, ORCHESTRATOR_AGENT_PROMPT

from semantic_kernel.connectors.ai.open_ai import OpenAIChatPromptExecutionSettings

from semantic_kernel.prompt_template.kernel_prompt_template import KernelPromptTemplate
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior
from semantic_kernel.functions import KernelArguments

from semantic_kernel import Kernel
from dotenv import load_dotenv
import os

from Plugin import SchemaGroundingPlugin


load_dotenv()

key=os.getenv("incubator_key")
model= os.getenv("model")
endpoint=os.getenv("incubator_endpoint")

chat_completion_service = AzureChatCompletion(
    deployment_name=model,  
    api_key=key,
    endpoint=endpoint,
)

kernel = Kernel()

kernel.add_service(chat_completion_service)

kernel.add_plugin(
    SchemaGroundingPlugin(),
    plugin_name="SchemaGroundingPlugin",
)





Builder_Agent = ChatCompletionAgent(
    # service=chat_completion_service,
    kernel = kernel,
    name="BuilderAgent",
    instructions=QUERY_BUILDER_AGENT_PROMPT
)

Evaluation_Agent = ChatCompletionAgent(
    # service=chat_completion_service,
    kernel = kernel,
    name="EvaluationAgent",
    instructions=EVALUATION_AGENT_PROMPT
)

Debug_Agent = ChatCompletionAgent(
    # service=chat_completion_service,
    kernel = kernel,
    name="DebugAgent",
    instructions=DEBUG_AGENT_PROMPT
)

Explanation_Agent = ChatCompletionAgent(
    # service=chat_completion_service,
    kernel = kernel,
    name="ExplanationAgent",
    instructions=EXPLANATION_AGENT_PROMPT
)



Orchestrator_Agent = ChatCompletionAgent(
    # service=chat_completion_service,
    kernel = kernel,
    name="OrchestratorAgent",
    instructions=ORCHESTRATOR_AGENT_PROMPT,
    # plugins=[Explanation_Agent,Debug_Agent,Evaluation_Agent,Builder_Agent,SchemaGroundingPlugin()]
)

test_agent = ChatCompletionAgent(
    # service=chat_completion_service,
    kernel = kernel,
    name="testAgent",
    instructions="your an agent taking inputs for user use the plugin SchemaGroundingPlugin to answer questions about the database schema",
    # plugins=[SchemaGroundingPlugin()]
)


thread = ChatHistoryAgentThread()

execution_settings = OpenAIChatPromptExecutionSettings()
execution_settings.function_choice_behavior = FunctionChoiceBehavior.Auto()


async def main() -> None:
    print("Welcome to the chat bot!\n  Type 'exit' to exit.\n")
    while True:
        user_input = input("User> ")
        if user_input.lower().strip() == "exit":
            print("\nExiting chat...")
            return

        arguments = {
            "user_message": user_input,
            "last_query": "",               # or track previous query
            "last_sql": "",                 # or track previous SQL
            "last_result_summary": "",      # or track previous summary
            "db_dialect": "sqlite",         # default dialect
            "max_rows": 1000,               # default row limit
            "max_eval_retries": 3,          # default retries
            "max_debug_retries": 3          # default retries
        }
        response = await Orchestrator_Agent.get_response(messages=user_input, thread=thread)
        print(f"Agent> {response}")


if __name__ == "__main__":
    asyncio.run(main())