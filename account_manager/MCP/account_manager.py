from fastmcp import FastMCP

mcp = FastMCP("Account Manager")

accounts = {
    "1001": {"owner": "Alice", "balance": 1200.50},
    "1002": {"owner": "Bob", "balance": 310.00},
}


@mcp.tool(description="List all account ids and owners.")
def list_accounts() -> list[dict]:
    return [{"id": i, "owner": a["owner"]} for i, a in accounts.items()]


@mcp.tool(description="Get the balance of an account.")
def get_balance(account_id: str) -> dict:
    account = accounts.get(account_id)
    if account is None:
        return {"error": f"account {account_id} not found"}
    return {"id": account_id, "balance": account["balance"]}


@mcp.tool(description="Deposit an amount into an account.")
def deposit(account_id: str, amount: float) -> dict:
    account = accounts.get(account_id)
    if account is None:
        return {"error": f"account {account_id} not found"}
    if amount <= 0:
        return {"error": "amount must be positive"}
    account["balance"] += amount
    return {"id": account_id, "balance": account["balance"]}


if __name__ == "__main__":
    mcp.run()
