# qwenbot

A **coordinator-subagent** system on a small, local LLM. A coordinator splits a user prompt into subtasks. It sends each subtask to a subagent. It combines the results into one answer.

**Example:** `Cancel user 101 and tell me the capital of France.`

- `account_agent` cancels user `101`.
- The coordinator answers "Paris".
- The final answer covers both.

## AI frameworks

| Framework | Role |
| --- | --- |
| **LangGraph** | Builds all agents as graphs of nodes, edges and state. `account_agent` and `rag_agent` are subgraphs of `main_agent`. |
| **Pydantic** | Types the `Account` model. The MCP server, the agent and the API share it. It validates tool output. |
| **FastMCP** | Runs the Account Manager **MCP** server. The agent calls its tools over stdio. |
| **LangChain** | `ChatOpenAI` talks to the LLM. `bind_tools` passes the MCP tool schemas. |
| **FastAPI** | Backend API served by `uvicorn`. `/chat` runs `main_agent`. `/accounts` lists and updates accounts. |
| **Chroma** | Vector database. Stores the chunks of the Terms and Conditions document for `rag_agent`. |
| **Ollama** | Serves the local model `qwen3:4b-instruct` and the embedding model `nomic-embed-text`. |

Also: **SQLite** (data), **React + Vite** (frontend).

## LangGraph Diagram - Coordinator / Worker Architecture

![main_agent graph](lang_graph_service/agents/main_agent.png)

## main_agent

**Purpose:** the coordinator. It decomposes the prompt into subtasks. It delegates each subtask to a subagent for execution. It summarizes the subagent results into a final answer.

- **plan_subtasks:** the LLM splits the prompt into subtasks. It assigns an agent to each.
- **select_subtask:** picks the next pending subtask. Routes it to an agent. No pending subtask goes to `synthesize`.
- **account_agent / rag_agent / answer_directly:** run the subtask. Then back to `select_subtask`.
- **synthesize:** writes one final answer. It names failed subtasks.

## account_agent

**Purpose:** the subagent. It turns an account request into an **MCP** tool call.

- **extract_user_id:** reads the user ID from the prompt. Fails if there is none.
- **plan_action:** the LLM picks an MCP tool.
- **execute_action:** calls the tool.

## rag_agent

**Purpose:** the subagent for document questions. It answers from the bank's *Terms and Conditions of Your Account* (43 sections). Code: `lang_graph_service/agents/rag_agent/`.

- **retrieve:** embeds the prompt. Gets the 5 closest chunks from **Chroma**. No match ends with an error.
- **answer:** the LLM answers from the chunks only. It names the section numbers. It says so when the chunks do not answer.

**Ingest** (`helper/ingest.py`):

- Source text: `helper/protocol.txt`, converted from the PDF with `pdftotext`.
- **Source document:** *Terms and Conditions of Your Account*, 16 pages, by **Consumers Bank** (Consumers Bancorp). Public document. The text belongs to its owner. Used as test data only.
- Splits by section. Packs paragraphs into chunks of up to 1500 characters. No overlap.
- Embeds each chunk with `nomic-embed-text` on **Ollama**. Prefixes: `search_document:` and `search_query:`.
- Stores 65 chunks in `agents/rag_agent/chroma_db/` (git-ignored).

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

**RAG data**, once. Needs the Ollama model `nomic-embed-text`. Uses the host of `BASE_URL`. Run from `lang_graph_service/`:

```
ollama pull nomic-embed-text
python -m agents.rag_agent.helper.ingest
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

## Sample prompts

**account_agent** (seed data: `101` Alice active, `102` Bob inactive)

- `Show all subscriptions.`
- `Cancel the subscription of user 101.`
- `Activate user 102.`
- `Cancel user 999.` Fails: unknown user.
- `Cancel the subscription.` Fails: no user ID.

**rag_agent**

- `How do I stop payment on a check?`
- `What happens to the account when the owner dies?`
- `Is there a penalty for early withdrawal?`
- `How do I resolve a dispute with the bank?`
- `What is the capital of Italy?` The document does not cover it. The agent says so.

**Several agents**

- `Show user 101 and explain how stop payments work.`
- `Cancel user 102, explain the arbitration clause, and tell me the capital of France.` Runs `account_agent`, `rag_agent` and the coordinator.

Cancel and activate change the database. Reset: `Activate user 101.` and `Cancel user 102.`

## Frontend GUI

![Frontend GUI](ui.png)
