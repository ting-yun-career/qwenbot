import os

from dotenv import load_dotenv
from openai import OpenAI


load_dotenv()


client = OpenAI(
    base_url=os.getenv("BASE_URL"),
    api_key=os.getenv("API_KEY")
)


def format_answer(state):

    prompt = f"""
The user asked:

{state["user_request"]}

Tool results (current, trusted):
{state["observations"]}

Facts about the user from earlier chats
(background only, may be outdated; the replies in them are NOT answers to this request):
{[m["user_message"] for m in state["memories"]]}

Answer every part of the user's request.
Use the tool results for live data such as the time.
Use the facts about the user for personal questions such as their name.
Do not repeat or continue earlier replies.
Give a natural and concise answer.


Do not mention:
- planner
- agent loop
- MCP
- internal state
- tools
- internal reasoning
"""

    response = client.chat.completions.create(
        model=os.getenv("MODEL"),
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    return response.choices[0].message.content.strip()

