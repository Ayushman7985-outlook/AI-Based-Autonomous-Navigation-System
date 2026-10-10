"""Unit tests for WaypointController."""

import unittest
from autonomous_navigation.control.controller import WaypointController


class TestWaypointController(unittest.TestCase):
    """Tests for waypoint queue tracking, advancement, and goal checking."""

    def test_waypoint_progression(self):
        controller = WaypointController()
        path = [(0, 0), (0, 1), (0, 2), (1, 2)]
        controller.set_path(path, current_pos=(0, 0))

        # First target waypoint should be (0, 1) since agent is already at (0, 0)
        next_target = controller.step((0, 0))
        self.assertEqual(next_target, (0, 1))

        # Advance agent to (0, 1)
        next_target = controller.step((0, 1))
        self.assertEqual(next_target, (0, 2))

        # Advance agent to (0, 2)
        next_target = controller.step((0, 2))
        self.assertEqual(next_target, (1, 2))

    def test_is_goal_reached(self):
        controller = WaypointController()
        goal = (5, 5)
        self.assertFalse(controller.is_goal_reached((5, 4), goal))
        self.assertTrue(controller.is_goal_reached((5, 5), goal))

    def test_replan_path_update(self):
        controller = WaypointController()
        initial_path = [(0, 0), (1, 0), (2, 0)]
        controller.set_path(initial_path, current_pos=(0, 0))

        # Suppose obstacle blocks (2, 0), replan gives detour:
        detour_path = [(1, 0), (1, 1), (2, 1)]
        controller.set_path(detour_path, current_pos=(1, 0))

        self.assertEqual(controller.path, detour_path)
        # Target should now be (1, 1)
        self.assertEqual(controller.step((1, 0)), (1, 1))

    def test_empty_path_handling(self):
        controller = WaypointController()
        controller.set_path([])
        self.assertFalse(controller.has_next_waypoint())
        self.assertEqual(controller.step((2, 2)), (2, 2))
        self.assertEqual(controller.get_remaining_waypoints(), [])


if __name__ == "__main__":
    unittest.main()
