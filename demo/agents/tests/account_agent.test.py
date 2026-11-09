import json
import unittest

from agents import main_agent
from helpers import SEED, DbTestCase, make_state, make_subtask, read_db, tearDownModule


class RunAccountAgentTest(DbTestCase):
    async def run_prompt(self, prompt):
        state = make_state(make_subtask(0, prompt=prompt), current=0)
        update = await main_agent.account_agent(state)
        return update["subtasks"][0]

    async def test_list_all_subscriptions(self):
        subtask = await self.run_prompt("Show all subscriptions.")
        self.assertEqual(subtask["status"], "done")
        ids = {account["id"] for account in json.loads(subtask["result"])}
        self.assertEqual(ids, {"101", "102"})

    async def test_cancel_user_changes_the_database(self):
        subtask = await self.run_prompt("Cancel the subscription of user 101.")
        self.assertEqual(subtask["status"], "done")
        self.assertFalse(read_db()["101"])
        self.assertFalse(json.loads(subtask["result"])["active"])

    async def test_reactivate_user_changes_the_database(self):
        subtask = await self.run_prompt("Reactivate the subscription of user 102.")
        self.assertEqual(subtask["status"], "done")
        self.assertTrue(read_db()["102"])

    async def test_unknown_user_fails(self):
        subtask = await self.run_prompt("Cancel the subscription of user 999.")
        self.assertEqual(subtask["status"], "failed")
        self.assertIn("999", subtask["result"])
        self.assertEqual(read_db(), SEED)

    async def test_missing_user_id_fails(self):
        subtask = await self.run_prompt("Cancel the subscription.")
        self.assertEqual(subtask["status"], "failed")
        self.assertEqual(read_db(), SEED)


if __name__ == "__main__":
    unittest.main()
