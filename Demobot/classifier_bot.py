import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END
from typing_extensions import TypedDict

load_dotenv()

llm = ChatOpenAI(
    model=os.getenv("MODEL"),
    base_url=os.getenv("BASE_URL"),
    api_key=os.getenv("API_KEY"),
    temperature=0,
)


class ClassifierState(TypedDict):
    prompt: str
    response: str


def read_prompt(state: ClassifierState) -> dict:
    return {"prompt": input("Enter a prompt: ")}


def classifier(state: ClassifierState) -> str:
    response = llm.invoke(
        "Classify the text as exactly one word: question or statement.\n"
        f"Text: {state['prompt']}"
    )
    if "question" in response.content.lower():
        return "query_handler"
    return "account_handler"


def account_handler(state: ClassifierState) -> dict:
    return {"response": f"account handler received: {state['prompt']}"}


def query_handler(state: ClassifierState) -> dict:
    return {"response": f"query handler received: {state['prompt']}"}


graph = StateGraph(ClassifierState)

graph.add_node("read_prompt", read_prompt)
graph.add_node("account_handler", account_handler)
graph.add_node("query_handler", query_handler)

graph.add_edge(START, "read_prompt")
graph.add_conditional_edges("read_prompt", classifier, ["account_handler", "query_handler"])
graph.add_edge("account_handler", END)
graph.add_edge("query_handler", END)

app = graph.compile()

if __name__ == "__main__":
    with open("classifier_bot.png", "wb") as f:
        f.write(app.get_graph().draw_mermaid_png())
    print("Graph saved to classifier_bot.png")

    result = app.invoke({"prompt": "", "response": ""})
    print(f"{result['prompt']!r}")
    print(result["response"])
