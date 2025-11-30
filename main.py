import asyncio
import nest_asyncio
from typing import List
from semantic_kernel.agents import ChatCompletionAgent, ChatHistoryAgentThread
from semantic_kernel.connectors.ai.open_ai import OpenAIChatCompletion
from semantic_kernel.functions import kernel_function
from Plugins.SchemaGroundingPlugin import SchemaGroundingPlugin
import os
from dotenv import load_dotenv

from semantic_kernel.prompt_template.kernel_prompt_template import KernelPromptTemplate
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior
from semantic_kernel.functions import KernelArguments

from semantic_kernel.connectors.ai.open_ai import OpenAIChatPromptExecutionSettings
from semantic_kernel import Kernel


from Prompt import QUERY_BUILDER_AGENT_PROMPT, EVALUATION_AGENT_PROMPT, DEBUG_AGENT_PROMPT, EXPLANATION_AGENT_PROMPT, ORCHESTRATOR_AGENT_PROMPT

nest_asyncio.apply()

load_dotenv()

key=os.getenv("OPENAI_KEY")

chat_completion_service = OpenAIChatCompletion(
    service_id="chat-gpt",
    ai_model_id="gpt-5-nano",
    api_key=key 
)

kernel = Kernel()

kernel.add_service(chat_completion_service)

kernel.add_plugin(
    SchemaGroundingPlugin(),
    plugin_name="SchemaGroundingPlugin",
)


Builder_Agent = ChatCompletionAgent(
    kernel=kernel,
    name="BuilderAgent",
    instructions=QUERY_BUILDER_AGENT_PROMPT
)

Evaluation_Agent = ChatCompletionAgent(
    kernel=kernel,
    name="EvaluationAgent",
    instructions=EVALUATION_AGENT_PROMPT
)

Debug_Agent = ChatCompletionAgent(
    kernel=kernel,
    name="DebugAgent",
    instructions=DEBUG_AGENT_PROMPT
)

Explanation_Agent = ChatCompletionAgent(
    kernel=kernel,
    name="ExplanationAgent",
    instructions=EXPLANATION_AGENT_PROMPT
)



Orchestrator_Agent = ChatCompletionAgent(
    kernel=kernel,
    name="OrchestratorAgent",
    instructions=ORCHESTRATOR_AGENT_PROMPT,
    plugins=[Explanation_Agent,Debug_Agent,Evaluation_Agent,Builder_Agent,SchemaGroundingPlugin()]
)

test_agent = ChatCompletionAgent(
    kernel=kernel,
    name="testAgent",
    instructions="Return from the pligin",
    plugins=[SchemaGroundingPlugin()]
)

execution_settings = OpenAIChatPromptExecutionSettings()
execution_settings.function_choice_behavior = FunctionChoiceBehavior.Auto()

thread = ChatHistoryAgentThread()


async def main() -> None:
    print("Welcome to the chat bot!\n  Type 'exit' to exit.\n")
    while True:
        user_input = input("User> ")
        if user_input.lower().strip() == "exit":
            print("\nExiting chat...")
            return
        

        arguments = {
            "user_message": user_input,
            "last_query": "",            
            "last_sql": "",                
            "last_result_summary": "",      
            "db_dialect": "sqlite",        
            "max_rows": 1000,            
            "max_eval_retries": 3,        
            "max_debug_retries": 3         
        }

        response = await Orchestrator_Agent.get_response(messages=user_input, thread=thread)
        print(f"Agent> {response}")

asyncio.run(main())
