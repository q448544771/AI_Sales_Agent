import unittest

from app.multi_agent.contracts import (
    AGENT_SEQUENCE,
    AGENT_TOOL_PERMISSIONS,
)
from app.multi_agent.supervisor import (
    mark_agent_complete,
    supervisor_node,
    supervisor_route,
)


class SupervisorTests(unittest.TestCase):

    def test_full_handoff_order(self):
        state = {
            "completed_agents": [],
            "supervisor_turns": 0,
        }

        for expected in AGENT_SEQUENCE:
            update = supervisor_node(state)

            self.assertEqual(update["next_agent"], expected)

            state.update(update)

            self.assertEqual(supervisor_route(state), expected)

            state.update(
                mark_agent_complete(state, expected)
            )

        result = supervisor_node(state)

        self.assertEqual(result["next_agent"], "finish")
        self.assertEqual(result["status"], "multi_agent_completed")

    def test_handoff_limit(self):
        update = supervisor_node({
            "completed_agents": [],
            "supervisor_turns": 2,
            "supervisor_max_turns": 2,
        })

        self.assertEqual(update["next_agent"], "finish")
        self.assertEqual(update["status"], "multi_agent_failed")

    def test_invalid_completed_worker(self):
        update = supervisor_node({
            "completed_agents": ["unknown"],
        })

        self.assertEqual(update["next_agent"], "finish")
        self.assertEqual(update["status"], "multi_agent_failed")

    def test_completion_idempotent(self):
        state = {"completed_agents": ["research"]}

        self.assertEqual(
            mark_agent_complete(state, "research"),
            state,
        )

        self.assertEqual(
            state["completed_agents"],
            ["research"],
        )

    def test_permissions_contract(self):
        self.assertEqual(
            set(AGENT_TOOL_PERMISSIONS),
            set(AGENT_SEQUENCE),
        )

        self.assertNotIn(
            "update_lead_stage",
            AGENT_TOOL_PERMISSIONS["research"],
        )

        self.assertEqual(
            AGENT_TOOL_PERMISSIONS["analysis"],
            frozenset(),
        )


if __name__ == "__main__":
    unittest.main()