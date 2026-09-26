import unittest

from app.graph.multi_workflow import create_multi_graph
from app.multi_agent.contracts import AGENT_SEQUENCE


class MultiAgentGraphTests(unittest.TestCase):

    def create_mock_workers(self, calls):
        """
        Test-only worker implementations.

        No DeepSeek, MCP, CRM or Chroma calls.
        """

        workers = {}

        for name in AGENT_SEQUENCE:

            def make_worker(worker_name):

                def worker(state):
                    calls.append(worker_name)

                    return {
                        f"{worker_name}_output": {
                            "ok": True,
                        }
                    }

                return worker

            workers[name] = make_worker(name)

        return workers

    def test_full_graph_execution(self):
        calls = []

        graph = create_multi_graph(
            self.create_mock_workers(calls)
        )

        result = graph.invoke({
            "completed_agents": [],
            "supervisor_turns": 0,
            "supervisor_max_turns": 10,
        })

        self.assertEqual(
            calls,
            list(AGENT_SEQUENCE),
        )

        self.assertEqual(
            result["completed_agents"],
            list(AGENT_SEQUENCE),
        )

        self.assertEqual(
            result["next_agent"],
            "finish",
        )

        self.assertEqual(
            result["status"],
            "multi_agent_completed",
        )

        self.assertEqual(
            result["supervisor_turns"],
            5,
        )

        for name in AGENT_SEQUENCE:
            self.assertTrue(
                result[f"{name}_output"]["ok"]
            )

    def test_graph_handoff_limit(self):
        calls = []

        graph = create_multi_graph(
            self.create_mock_workers(calls)
        )

        result = graph.invoke({
            "completed_agents": [],
            "supervisor_turns": 0,
            "supervisor_max_turns": 2,
        })

        self.assertEqual(
            calls,
            ["research", "knowledge"],
        )

        self.assertEqual(
            result["completed_agents"],
            ["research", "knowledge"],
        )

        self.assertEqual(
            result["status"],
            "multi_agent_failed",
        )

    def test_missing_workers(self):
        with self.assertRaises(ValueError):
            create_multi_graph({})

    def test_worker_failure(self):
        calls = []

        workers = self.create_mock_workers(calls)

        def failing_knowledge(state):
            calls.append("knowledge")
            raise RuntimeError("simulated knowledge failure")

        workers["knowledge"] = failing_knowledge

        graph = create_multi_graph(workers)

        with self.assertRaisesRegex(
            RuntimeError,
            "simulated knowledge failure",
        ):
            graph.invoke({
                "completed_agents": [],
                "supervisor_turns": 0,
            })

        self.assertEqual(
            calls,
            ["research", "knowledge"],
        )

    def test_worker_cannot_modify_supervisor_fields(self):
        calls = []

        workers = self.create_mock_workers(calls)

        def invalid_research(state):
            return {
                "completed_agents": list(AGENT_SEQUENCE),
            }

        workers["research"] = invalid_research

        graph = create_multi_graph(workers)

        with self.assertRaises(ValueError):
            graph.invoke({
                "completed_agents": [],
                "supervisor_turns": 0,
            })


if __name__ == "__main__":
    unittest.main()