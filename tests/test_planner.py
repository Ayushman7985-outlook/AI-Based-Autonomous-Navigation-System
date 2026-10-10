"""Unit tests for A* path planner."""

import unittest
from autonomous_navigation.environment.world import GridWorld
from autonomous_navigation.perception.obstacle_map import ObstacleMap
from autonomous_navigation.planning.astar import AStarPlanner


class TestAStarPlanner(unittest.TestCase):
    """Tests covering path planning correctness, obstacle avoidance, and failure modes."""

    def setUp(self):
        self.world = GridWorld(
            width=10,
            height=10,
            start=(0, 0),
            goal=(9, 9),
            static_obstacles=[(1, 0), (1, 1), (1, 2), (1, 3)],
        )
        self.obstacle_map = ObstacleMap(self.world)

    def test_path_validity_and_continuity(self):
        planner = AStarPlanner(self.obstacle_map)
        path = planner.plan((0, 0), (9, 9))
        self.assertIsNotNone(path)
        self.assertEqual(path[0], (0, 0))
        self.assertEqual(path[-1], (9, 9))

        # Check step continuity: each step must be 1 unit orthogonal distance
        for i in range(len(path) - 1):
            x1, y1 = path[i]
            x2, y2 = path[i + 1]
            dist = abs(x2 - x1) + abs(y2 - y1)
            self.assertEqual(dist, 1)

    def test_obstacle_avoidance(self):
        planner = AStarPlanner(self.obstacle_map)
        path = planner.plan((0, 0), (9, 9))
        self.assertIsNotNone(path)
        for node in path:
            self.assertFalse(self.obstacle_map.is_occupied(node))

    def test_unreachable_goal(self):
        # Enclose the goal completely with static obstacles
        # Goal is at (9, 9), neighbors are (8, 9) and (9, 8)
        world = GridWorld(
            width=10,
            height=10,
            start=(0, 0),
            goal=(9, 9),
            static_obstacles=[(8, 9), (9, 8)],
        )
        obstacle_map = ObstacleMap(world)
        planner = AStarPlanner(obstacle_map, allow_diagonal=False)
        path = planner.plan((0, 0), (9, 9))
        self.assertIsNone(path)

    def test_blocked_start_or_goal(self):
        planner = AStarPlanner(self.obstacle_map)
        # Block start with dynamic obstacle
        self.obstacle_map.update_dynamic_obstacles([(0, 0)])
        self.assertIsNone(planner.plan((0, 0), (9, 9)))

        # Block goal with dynamic obstacle
        self.obstacle_map.clear_dynamic_obstacles()
        self.obstacle_map.update_dynamic_obstacles([(9, 9)])
        self.assertIsNone(planner.plan((0, 0), (9, 9)))

    def test_start_equals_goal(self):
        planner = AStarPlanner(self.obstacle_map)
        path = planner.plan((2, 2), (2, 2))
        self.assertEqual(path, [(2, 2)])

    def test_diagonal_movement_open_space(self):
        # Open 6x6 world from (0, 0) to (5, 5)
        world_open = GridWorld(width=6, height=6, start=(0, 0), goal=(5, 5))
        om_open = ObstacleMap(world_open)
        planner_diag = AStarPlanner(om_open, allow_diagonal=True)
        path_diag = planner_diag.plan((0, 0), (5, 5))
        self.assertIsNotNone(path_diag)
        # In open grid, diagonal path takes 5 diagonal steps: length 6 coordinates
        self.assertEqual(len(path_diag), 6)
        self.assertEqual(path_diag, [(0, 0), (1, 1), (2, 2), (3, 3), (4, 4), (5, 5)])

    def test_diagonal_movement_prevents_corner_cutting(self):
        """Diagonal movement must not squeeze between pinching obstacle corners."""
        # Pinching corner: (1, 0) and (0, 1) are blocked in 3x3 grid
        world_pinch = GridWorld(
            width=3, height=3, start=(0, 0), goal=(2, 2), static_obstacles=[(1, 0), (0, 1)]
        )
        om_pinch = ObstacleMap(world_pinch)
        planner = AStarPlanner(om_pinch, allow_diagonal=True)
        # Agent at (0, 0) is completely enclosed orthogonally; cannot cut corner to (1, 1)
        path = planner.plan((0, 0), (2, 2))
        self.assertIsNone(path)

    def test_diagonal_movement_routes_around_single_corner_obstacle(self):
        """When one orthogonal adjacent cell is an obstacle, diagonal move is prohibited,

        forcing a safe orthogonal route around the obstacle.
        """
        # Obstacle at (1, 0) only; (0, 1) is free
        world_single = GridWorld(
            width=4, height=4, start=(0, 0), goal=(2, 2), static_obstacles=[(1, 0)]
        )
        om_single = ObstacleMap(world_single)
        planner = AStarPlanner(om_single, allow_diagonal=True)
        path = planner.plan((0, 0), (2, 2))
        self.assertIsNotNone(path)
        # Cannot step (0, 0) -> (1, 1) because (1, 0) is blocked.
        # Must step (0, 0) -> (0, 1), then from (0, 1) to (1, 2) or (1, 1) since (0, 1) neighbors are free
        self.assertNotEqual(path[1], (1, 1))
        self.assertEqual(path[1], (0, 1))


if __name__ == "__main__":
    unittest.main()
