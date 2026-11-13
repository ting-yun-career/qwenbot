import re
import unittest
from unittest.mock import patch

from agents import main_agent
from agents.rag_agent.rag_agent import search_chunks
from helpers import make_state, make_subtask, run_on_shared_loop, tearDownModule


def sections_of(chunks):
    return {int(re.match(r"\((\d+)\)", chunk)[1]) for chunk in chunks}


class SearchChunksTest(unittest.TestCase):
    def test_returns_five_chunks(self):
        self.assertEqual(len(search_chunks("How do I stop payment on a check?")), 5)

    def test_stop_payment_finds_section_8(self):
        self.assertIn(8, sections_of(search_chunks("How do I stop payment on a check?")))

    def test_death_finds_section_29(self):
        self.assertIn(29, sections_of(search_chunks("What happens when an account owner dies?")))

    def test_early_withdrawal_finds_section_37(self):
        self.assertIn(37, sections_of(search_chunks("Is there a penalty for early withdrawal?")))


class RunRagAgentTest(unittest.TestCase):
    async def run_prompt(self, prompt):
        state = make_state(
            make_subtask(0, agent="rag_agent", prompt=prompt), current=0
        )
        update = await main_agent.rag_agent(state)
        return update["subtasks"][0]

    @run_on_shared_loop
    async def test_answer_names_the_section(self):
        subtask = await self.run_prompt("How do I stop payment on a check?")
        self.assertEqual(subtask["status"], "done")
        self.assertRegex(subtask["result"], r"\b8\b")

    @run_on_shared_loop
    async def test_off_topic_question_is_not_answered(self):
        subtask = await self.run_prompt("What is the capital of Italy?")
        self.assertEqual(subtask["status"], "done")
        self.assertNotIn("Rome", subtask["result"])

    @run_on_shared_loop
    async def test_no_chunks_fails(self):
        with patch("agents.rag_agent.rag_agent.search_chunks", return_value=[]):
            subtask = await self.run_prompt("How do I stop payment on a check?")
        self.assertEqual(subtask["status"], "failed")


if __name__ == "__main__":
    unittest.main()
