import asyncio
from agent import Orchestrator_Agent, thread ,test_agent
from semantic_kernel.functions import KernelArguments

async def main() -> None:
    print("Welcome to the chat bot!\nType 'exit' to exit.\n")

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
            "max_debug_retries": 3,
        }

        response = await Orchestrator_Agent.get_response(
            messages=user_input, thread=thread, arguments=KernelArguments(**arguments)
        )
        
        print(f"Agent> {response}")


if __name__ == "__main__":
    asyncio.run(main())