from typing import TypedDict
class AgentState(TypedDict):
    user_request: str
    current_step: int
    max_steps: int
    actions: list
    observations: list
    finished: bool
    final_answer: str

