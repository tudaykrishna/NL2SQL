import os
from dotenv import load_dotenv
from semantic_kernel import Kernel
from semantic_kernel.agents import ChatCompletionAgent, ChatHistoryAgentThread
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion, AzureChatPromptExecutionSettings
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior

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

# Kernel setup
kernel = Kernel()
kernel.add_service(chat_completion_service)

# Add plugin
kernel.add_plugin(SchemaGroundingPlugin(), plugin_name="SchemaGroundingPlugin")

# Optional execution settings (currently unused)
execution_settings = AzureChatPromptExecutionSettings()
execution_settings.function_choice_behavior = FunctionChoiceBehavior.Auto()

# Agent definitions
Builder_Agent = ChatCompletionAgent(
    kernel=kernel,
    name="BuilderAgent",
    instructions=QUERY_BUILDER_AGENT_PROMPT,
)

Evaluation_Agent = ChatCompletionAgent(
    kernel=kernel,
    name="EvaluationAgent",
    instructions=EVALUATION_AGENT_PROMPT,
)

Debug_Agent = ChatCompletionAgent(
    kernel=kernel,
    name="DebugAgent",
    instructions=DEBUG_AGENT_PROMPT,
)

Explanation_Agent = ChatCompletionAgent(
    kernel=kernel,
    name="ExplanationAgent",
    instructions=EXPLANATION_AGENT_PROMPT,
)

Orchestrator_Agent = ChatCompletionAgent(
    kernel=kernel,
    name="OrchestratorAgent",
    instructions=ORCHESTRATOR_AGENT_PROMPT,
)

test_agent = ChatCompletionAgent(
    kernel=kernel,
    name="testAgent",
    instructions="You are an agent taking inputs from the user. Use the plugin SchemaGroundingPlugin to answer questions about the database schema.",
)


