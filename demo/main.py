import asyncio
from pathlib import Path

from agents.main_agent import main_agent

GRAPH_IMAGE = Path(__file__).parent / "agents/main_agent.png"

if __name__ == "__main__":
    GRAPH_IMAGE.write_bytes(main_agent.get_graph(xray=True).draw_mermaid_png())
    print(f"Graph saved to {GRAPH_IMAGE}")

    final = asyncio.run(main_agent.ainvoke({"prompt": input("Enter a prompt: ")}))
    print("---")
    for subtask in final["subtasks"]:
        print(subtask)
    print("---")
    print(final["answer"])
