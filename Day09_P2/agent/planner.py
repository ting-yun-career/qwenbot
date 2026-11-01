from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()

client = OpenAI(
    base_url=os.getenv("BASE_URL"),
    api_key=os.getenv("API_KEY")
)


def build_tool_descriptions(tools):

    descriptions = ""

    for tool in tools:

        descriptions += f"""
Tool:
{tool.name}

Description:
{tool.description}

----------------------------
"""

    return descriptions

def planner(state, tools):

    tool_descriptions = build_tool_descriptions(tools)

    prompt = f"""
You are an AI Planner.

Your job is to decide ONLY the next action.

User Request:
{state["user_request"]}

Completed Actions:
{state["actions"]}

Previous Observations:
{state["observations"]}

Available Tools:
{tool_descriptions}

Rules:

- Choose only ONE next action.
- Never repeat an action that has already been completed.
- Use the observations to decide what is still required.
- If the user's request has been completely satisfied, return FINISH.
- Return ONLY the tool name or FINISH.
- Do not explain your answer.
"""
    # print('==========================')
    # print("planner prompt: " + prompt)
    # print('==========================')
    response = client.chat.completions.create(
        model=os.getenv("MODEL"),
        messages=[
            {
                "role": "system",
                "content": "You are an AI planner."
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    return response.choices[0].message.content.strip()

