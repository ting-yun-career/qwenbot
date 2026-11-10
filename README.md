# qwenbot

A **coordinator-subagent** system on a small, local LLM. A coordinator splits a user prompt into subtasks. It sends each subtask to a subagent. It combines the results into one answer.

**Example:** `Cancel user 101 and tell me the capital of France.`

- `account_agent` cancels user `101`.
- The coordinator answers "Paris".
- The final answer covers both.

## AI frameworks

| Framework | Role |
| --- | --- |
| **LangGraph** | Builds both agents as graphs of nodes, edges and state. `account_agent` is a subgraph of `main_agent`. |
| **Pydantic** | Types the `Account` model. The MCP server, the agent and the API share it. It validates tool output. |
| **FastMCP** | Runs the Account Manager **MCP** server. The agent calls its tools over stdio. |
| **LangChain** | `ChatOpenAI` talks to the LLM. `bind_tools` passes the MCP tool schemas. |
| **Ollama** | Serves the local model `qwen3:4b-instruct`. |

Also: **FastAPI** (backend), **SQLite** (data), **React + Vite** (frontend).

## LangGraph Diagram - Coordinator / Worker Architecture

![main_agent graph](lang_graph_service/agents/main_agent.png)

## main_agent

**Purpose:** the coordinator. It decomposes the prompt into subtasks. It delegates each subtask to a subagent for execution. It summarizes the subagent results into a final answer.

- **plan_subtasks:** the LLM splits the prompt into subtasks. It assigns an agent to each.
- **select_subtask:** picks the next pending subtask. Routes it to an agent. No pending subtask goes to `synthesize`.
- **account_agent / answer_directly:** run the subtask. Then back to `select_subtask`.
- **synthesize:** writes one final answer. It names failed subtasks.

## account_agent

**Purpose:** the subagent. It turns an account request into an **MCP** tool call.

- **extract_user_id:** reads the user ID from the prompt. Fails if there is none.
- **plan_action:** the LLM picks an MCP tool.
- **execute_action:** calls the tool.

## MCP server

**Purpose:** gives `account_agent` tools to manage SaaS subscriptions. Code: `lang_graph_service/MCP/account_manager/`.

- Built with `fastmcp`. Runs over stdio. `account_agent` starts it on each call.
- Stores data in **SQLite**. Seed data: `101` Alice (active), `102` Bob (inactive).
- Tools:
  - `list_subscriptions`: list all accounts.
  - `get_subscription`: get one account by user ID.
  - `set_subscription_state`: activate or cancel an account.
- An unknown user ID returns an error.

## Run

Create `lang_graph_service/.env`:

```
BASE_URL=http://localhost:11434/v1
API_KEY=ollama
MODEL=qwen3:4b-instruct
```

**CLI**, from `lang_graph_service/`:

```
python main.py
```

**Web app:**

```
cd lang_graph_service && uvicorn api:app --reload
cd frontend && npm install && npm run dev
```

Open `http://localhost:5173`.

## Frontend GUI

![Frontend GUI](ui.png)
