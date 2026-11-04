from langgraph.graph import (
    StateGraph,
    START,
    END
)

from agent.planner import planner


from agent.state import AgentState

def create_planner_node(tools):

    def planner_node(state: AgentState):

        action = planner(
            state,
            tools
        )

        print("\nPlanner Selected:")
        print(action)

        return {
            "actions": state["actions"],
            "observations": state["observations"],
            "current_step": state["current_step"],
            "finished": action == "FINISH",
            "final_answer": state["final_answer"]
        }

    return planner_node



def build_graph(tools):

    builder = StateGraph(AgentState)

    planner_node = create_planner_node(tools)

    builder.add_node(
        "planner",
        planner_node
    )

    builder.add_edge(
        START,
        "planner"
    )

    builder.add_edge(
        "planner",
        END
    )

    return builder.compile()

