import os
from dotenv import load_dotenv
import autogen
from autogen import AssistantAgent, UserProxyAgent, GroupChat, GroupChatManager

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")

# 1. Configure Gemini using Google's Official OpenAI-compatible API endpoint
llm_config = {
    "config_list": [
        {
            "model": "gemini-3.1-flash-lite",
            "api_key": api_key,
            "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
        }
    ],
    "temperature": 0.2,
}

# 2. Define the Four Specialized Assistant Agents
planner = AssistantAgent(
    name="Planner",
    system_message="""You are a Senior Software Architect.
    Analyze the coding task and produce a concise, numbered step-by-step implementation plan.
    Do not write the final Python implementation yourself.
    When your plan is complete, end your response with: 'NEXT: Coder'.""",
    llm_config=llm_config,
)

coder = AssistantAgent(
    name="Coder",
    system_message="""You are an Expert Python Developer.
    Read the plan provided by the Planner and write clean, modular, production-ready Python code.
    Include docstrings, type annotations, and robust error handling.
    When your code is written, end your response with: 'NEXT: Debugger'.""",
    llm_config=llm_config,
)

debugger = AssistantAgent(
    name="Debugger",
    system_message="""You are a QA & Code Review Specialist.
    Review the Coder's implementation for logical bugs, corrupted row handling, and edge cases.
    Suggest specific fixes or verify code robustness.
    When your review is complete, end your response with: 'NEXT: Tester'.""",
    llm_config=llm_config,
)

tester = AssistantAgent(
    name="Tester",
    system_message="""You are a Test Automation Engineer.
    Write unit tests (using unittest or pytest) covering both standard inputs and edge cases (empty file, invalid data, missing columns).
    If the implementation and tests are complete and verified, end your response with: 'TERMINATE'.""",
    llm_config=llm_config,
)

# 3. Define the User Proxy Agent
user_proxy = UserProxyAgent(
    name="UserProxy",
    human_input_mode="NEVER",
    max_consecutive_auto_reply=10,
    is_termination_msg=lambda x: "TERMINATE" in (x.get("content", "") or ""),
    code_execution_config=False,
)

# 4. Assemble the GroupChat with Round-Robin Rotation
groupchat = GroupChat(
    agents=[user_proxy, planner, coder, debugger, tester],
    messages=[],
    max_round=8,
    speaker_selection_method="round_robin",
)

manager = GroupChatManager(groupchat=groupchat, llm_config=llm_config)

if __name__ == "__main__":
    task_prompt = """
    Build a standalone Python utility function `analyze_sales_data(filepath: str) -> dict` that parses a CSV file of sales data 
    (columns: 'date', 'product', 'quantity', 'price') and calculates:
    1. Total revenue
    2. Top 3 products by revenue
    3. Monthly revenue breakdown (formatted as 'YYYY-MM': total_revenue)
    Handle missing files, corrupted rows, and invalid numbers gracefully without crashing.
    """

    print("--- Starting AutoGen Multi-Agent Coding Session ---\n")
    user_proxy.initiate_chat(
        manager,
        message=task_prompt,
    )