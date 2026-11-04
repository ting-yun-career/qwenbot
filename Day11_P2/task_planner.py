import os

from dotenv import load_dotenv
from openai import OpenAI


load_dotenv()


client = OpenAI(
    base_url=os.getenv("BASE_URL"),
    api_key=os.getenv("API_KEY")
)


def decompose_task(user_request):

    prompt = f"""
You are an AI task planner.

Break the user's request into smaller tasks.

Rules:

1. Create only necessary tasks.
2. Put tasks in execution order.
3. Each task should be a short action.
4. Return one task per line.
5. Do not number the tasks.
6. Do not explain anything.

CRITICAL RULE:

Return NO tasks (or "NONE") ONLY IF the ENTIRE user request belongs to the following categories and no part of it needs a tool:
   1. Greetings or casual conversation (e.g., "hi", "hello", "how are you?")
   2. Introductions or personal details (e.g., "my name is Pankaj", "I live in Delhi")
   3. Memory questions about past interactions (e.g., "what is my name?", "what did we discuss earlier?")
   4. General knowledge/Q&A questions that can be answered directly without tools (e.g., "what is Machine Learning?", "explain gravity")

Always create a task for any part of the request that needs a tool:
   - current date or time
   - rolling a dice
   - generating a password
If a request mixes an introduction or memory question with a tool request
(e.g., "my name is Tim, what time is it?" or "hi, I am Tim, tell me the current time"), ignore the introduction
and return a task for the tool part only (e.g., "Get the current time.").
Never create a task for a memory question such as "what is my name".
Example: "tell me the time and my name" -> return only: Get the current time.


User Request:

{user_request}
"""

    response = client.chat.completions.create(
        model=os.getenv("MODEL"),
        messages=[
            {
                "role": "system",
                "content": "You are an AI task planner."
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    result = response.choices[0].message.content.strip()

    tasks = []

    for line in result.splitlines():

        line = line.strip()

        if line and line.upper().strip(".") != "NONE":
            tasks.append(line)

    return tasks