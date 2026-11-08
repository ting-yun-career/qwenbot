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
    label: str


def read_prompt(state: ClassifierState) -> dict:
    return {"prompt": input("Enter a prompt: ")}


def classify(state: ClassifierState) -> dict:
    response = llm.invoke(
        "Classify the text as exactly one word: question or statement.\n"
        f"Text: {state['prompt']}"
    )
    label = "question" if "question" in response.content.lower() else "statement"
    return {"label": label}


graph = StateGraph(ClassifierState)
graph.add_node("read_prompt", read_prompt)
graph.add_node("classify", classify)
graph.add_edge(START, "read_prompt")
graph.add_edge("read_prompt", "classify")
graph.add_edge("classify", END)

app = graph.compile()

if __name__ == "__main__":
    with open("classifier_bot.png", "wb") as f:
        f.write(app.get_graph().draw_mermaid_png())
    print("Graph saved to classifier_bot.png")

    result = app.invoke({"prompt": "", "label": ""})
    print(f"{result['prompt']!r} -> {result['label']}")
