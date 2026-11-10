import re
import unittest

from agents import main_agent
from helpers import SEED, DbTestCase, make_state, make_subtask, read_db, tearDownModule


class UpdateSubtaskTest(unittest.TestCase):
    def test_changes_only_the_current_subtask(self):
        state = make_state(make_subtask(0), make_subtask(1), current=1)
        update = main_agent.update_subtask(state, "done", "ok")["subtasks"]
        self.assertEqual(update[0]["status"], "pending")
        self.assertEqual(update[1]["status"], "done")
        self.assertEqual(update[1]["result"], "ok")

    def test_does_not_change_the_old_state(self):
        state = make_state(make_subtask(0), current=0)
        main_agent.update_subtask(state, "done", "ok")
        self.assertEqual(state["subtasks"][0]["status"], "pending")
        self.assertIsNone(state["subtasks"][0]["result"])


class SelectSubtaskTest(unittest.TestCase):
    def test_picks_first_pending(self):
        state = make_state(make_subtask(0, status="done"), make_subtask(1), make_subtask(2))
        self.assertEqual(main_agent.select_subtask(state), {"current": 1})

    def test_returns_none_when_nothing_is_pending(self):
        state = make_state(make_subtask(0, status="done"), make_subtask(1, status="failed"))
        self.assertEqual(main_agent.select_subtask(state), {"current": None})

    def test_returns_none_for_empty_list(self):
        self.assertEqual(main_agent.select_subtask(make_state()), {"current": None})


class RouteSubtaskTest(unittest.TestCase):
    def test_no_current_goes_to_synthesize(self):
        self.assertEqual(main_agent.route_subtask(make_state(current=None)), "synthesize")

    def test_account_agent_goes_to_its_node(self):
        state = make_state(make_subtask(0, agent="account_agent"), current=0)
        self.assertEqual(main_agent.route_subtask(state), "account_agent")

    def test_coordinator_answers_directly(self):
        state = make_state(make_subtask(0, agent="coordinator"), current=0)
        self.assertEqual(main_agent.route_subtask(state), "answer_directly")

    def test_unknown_agent_answers_directly(self):
        state = make_state(make_subtask(0, agent="mystery"), current=0)
        self.assertEqual(main_agent.route_subtask(state), "answer_directly")


class PlanSubtasksTest(DbTestCase):
    async def plan(self, prompt):
        update = await main_agent.plan_subtasks({"prompt": prompt})
        return update["subtasks"]

    async def test_mixed_request_uses_both_agents(self):
        subtasks = await self.plan("Cancel user 101 and tell me the capital of France.")
        self.assertEqual({s["agent"] for s in subtasks}, {"account_agent", "coordinator"})
        account = [s for s in subtasks if s["agent"] == "account_agent"]
        self.assertTrue(any("101" in s["prompt"] for s in account))

    async def test_account_request_goes_to_account_agent(self):
        subtasks = await self.plan("Show all subscriptions.")
        self.assertEqual({s["agent"] for s in subtasks}, {"account_agent"})

    async def test_general_question_goes_to_coordinator(self):
        subtasks = await self.plan("What is the capital of France?")
        self.assertEqual({s["agent"] for s in subtasks}, {"coordinator"})

    async def test_missing_user_id_is_not_invented(self):
        subtasks = await self.plan("Cancel my subscription.")
        self.assertTrue(subtasks)
        for subtask in subtasks:
            self.assertIsNone(re.search(r"\d", subtask["prompt"]), subtask["prompt"])

    async def test_new_subtasks_start_pending(self):
        update = await main_agent.plan_subtasks({"prompt": "Show all subscriptions."})
        self.assertTrue(all(s["status"] == "pending" for s in update["subtasks"]))
        self.assertTrue(all(s["result"] is None for s in update["subtasks"]))
        self.assertIsNone(update["current"])
        self.assertIsNone(update["answer"])


class FullGraphTest(DbTestCase):
    async def run_graph(self, prompt):
        return await main_agent.main_agent.ainvoke({"prompt": prompt})

    async def test_cancel_and_list(self):
        final = await self.run_graph("Cancel the subscription of user 101 and show all subscriptions.")
        self.assertFalse(read_db()["101"])
        self.assertTrue(final["answer"])
        self.assertTrue(all(s["status"] != "pending" for s in final["subtasks"]))
        self.assertIsNone(final["current"])

    async def test_cancel_and_reactivate_two_users(self):
        await self.run_graph("Cancel user 101 and reactivate user 102.")
        self.assertEqual(read_db(), {"101": False, "102": True})

    async def test_mixed_request(self):
        final = await self.run_graph("Cancel user 101 and tell me the capital of France.")
        self.assertFalse(read_db()["101"])
        self.assertIn("Paris", final["answer"])
        self.assertEqual(
            {s["agent"] for s in final["subtasks"]}, {"account_agent", "coordinator"}
        )

    async def test_general_question_does_not_touch_accounts(self):
        final = await self.run_graph("What is the capital of France?")
        self.assertIn("Paris", final["answer"])
        self.assertEqual({s["agent"] for s in final["subtasks"]}, {"coordinator"})
        self.assertEqual(read_db(), SEED)

    async def test_missing_user_id_is_reported(self):
        final = await self.run_graph("Cancel my subscription.")
        self.assertTrue(any(s["status"] == "failed" for s in final["subtasks"]))
        self.assertEqual(read_db(), SEED)
        self.assertTrue(final["answer"])

    async def test_unknown_user_is_reported(self):
        final = await self.run_graph("Cancel the subscription of user 999.")
        self.assertTrue(any(s["status"] == "failed" for s in final["subtasks"]))
        self.assertEqual(read_db(), SEED)


if __name__ == "__main__":
    unittest.main()
