import asyncio

from langgraph.graph import StateGraph, START, END
from typing_extensions import TypedDict

from agents.rag_agent.helper.vector_store import embed_query, get_collection

TOP_K = 5


class RagState(TypedDict):
    prompt: str
    chunks: list[str] | None
    answer: str | None
    error: str | None


def search_chunks(prompt: str) -> list[str]:
    result = get_collection().query(
        query_embeddings=[embed_query(prompt)], n_results=TOP_K
    )
    return result["documents"][0]


async def retrieve(state: RagState) -> dict:
    chunks = await asyncio.to_thread(search_chunks, state["prompt"])
    if not chunks:
        return {"chunks": [], "error": "No matching text found in the protocol"}
    return {"chunks": chunks}


def has_chunks(state: RagState) -> str:
    return "answer" if state.get("chunks") else END


def create_rag_agent(llm):
    async def answer(state: RagState) -> dict:
        excerpts = "\n\n---\n\n".join(state["chunks"])
        response = await llm.ainvoke(
            "Answer the question with the excerpts only. "
            "Name the section number, such as (8), for each fact. "
            "If the excerpts do not answer the question, say so.\n\n"
            f"Excerpts:\n{excerpts}\n\nQuestion: {state['prompt']}"
        )
        return {"answer": response.content}

    graph = StateGraph(RagState)

    graph.add_node("retrieve", retrieve)
    graph.add_node("answer", answer)

    graph.add_edge(START, "retrieve")
    graph.add_conditional_edges("retrieve", has_chunks, ["answer", END])
    graph.add_edge("answer", END)

    return graph.compile()
