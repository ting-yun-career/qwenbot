import sqlite3
from pathlib import Path

from fastmcp import FastMCP
from fastmcp.exceptions import ToolError
from schemas import Account

mcp = FastMCP("Account Manager")

DB_PATH = Path(__file__).parent / "subscriptions.db"


def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with connect() as conn:
        conn.execute(
            "CREATE TABLE IF NOT EXISTS subscriptions ("
            "user_id TEXT PRIMARY KEY, name TEXT NOT NULL, active INTEGER NOT NULL)"
        )
        count = conn.execute("SELECT COUNT(*) FROM subscriptions").fetchone()[0]
        if count == 0:
            conn.executemany(
                "INSERT INTO subscriptions VALUES (?, ?, ?)",
                [("101", "Alice", 1), ("102", "Bob", 0)],
            )


def to_account(row: sqlite3.Row) -> Account:
    return Account(id=row["user_id"], name=row["name"], active=bool(row["active"]))


@mcp.tool(description="List all user subscriptions.")
def list_subscriptions() -> dict[str, Account]:
    with connect() as conn:
        rows = conn.execute("SELECT * FROM subscriptions").fetchall()
    return {row["user_id"]: to_account(row) for row in rows}


@mcp.tool(description="Get the subscription of a user.")
def get_subscription(user_id: str) -> Account:
    with connect() as conn:
        row = conn.execute(
            "SELECT * FROM subscriptions WHERE user_id = ?", (user_id,)
        ).fetchone()
    if row is None:
        raise ToolError(f"user {user_id} not found")
    return to_account(row)


@mcp.tool(description="Set the subscription state of a user to active or inactive.")
def set_subscription_state(user_id: str, active: bool) -> Account:
    with connect() as conn:
        cursor = conn.execute(
            "UPDATE subscriptions SET active = ? WHERE user_id = ?",
            (int(active), user_id),
        )
        if cursor.rowcount == 0:
            raise ToolError(f"user {user_id} not found")
        row = conn.execute(
            "SELECT * FROM subscriptions WHERE user_id = ?", (user_id,)
        ).fetchone()
    return to_account(row)


init_db()

if __name__ == "__main__":
    mcp.run(show_banner=False, log_level="WARNING")
