import asyncio
import functools
import inspect
import sqlite3
import unittest
from pathlib import Path

DB_PATH = Path(__file__).parent.parent.parent / "MCP/account_manager/subscriptions.db"
SEED = {"101": True, "102": False}


def reset_db():
    if not DB_PATH.exists():
        return
    conn = sqlite3.connect(DB_PATH)
    try:
        with conn:
            for user_id, active in SEED.items():
                conn.execute(
                    "UPDATE subscriptions SET active = ? WHERE user_id = ?",
                    (int(active), user_id),
                )
    finally:
        conn.close()


def read_db():
    conn = sqlite3.connect(DB_PATH)
    try:
        rows = conn.execute("SELECT user_id, active FROM subscriptions").fetchall()
    finally:
        conn.close()
    return {user_id: bool(active) for user_id, active in rows}


def make_subtask(index, agent="account_agent", status="pending", result=None, prompt=None):
    return {
        "id": index,
        "agent": agent,
        "prompt": prompt or f"task {index}",
        "status": status,
        "result": result,
    }


def make_state(*subtasks, current=None, prompt="request"):
    return {
        "prompt": prompt,
        "subtasks": list(subtasks),
        "current": current,
        "answer": None,
    }


LOOP = asyncio.new_event_loop()


def tearDownModule():
    LOOP.close()


def run_on_shared_loop(test):
    @functools.wraps(test)
    def wrapper(self):
        return LOOP.run_until_complete(test(self))

    return wrapper


class DbTestCase(unittest.TestCase):
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        for name, member in list(vars(cls).items()):
            if name.startswith("test") and inspect.iscoroutinefunction(member):
                setattr(cls, name, run_on_shared_loop(member))

    def setUp(self):
        reset_db()

    def tearDown(self):
        reset_db()
