"""Unit tests for GridWorld environment and configuration."""

import unittest
from autonomous_navigation.config import NavigationConfig
from autonomous_navigation.environment.world import GridWorld
from autonomous_navigation.perception.obstacle_map import ObstacleMap


class TestGridWorld(unittest.TestCase):
    """Tests for GridWorld creation, boundaries, and obstacle logic."""

    def test_valid_environment_initialization(self):
        world = GridWorld(
            width=10,
            height=10,
            start=(0, 0),
            goal=(9, 9),
            static_obstacles=[(2, 2), (2, 3)],
        )
        self.assertEqual(world.width, 10)
        self.assertEqual(world.height, 10)
        self.assertEqual(world.start, (0, 0))
        self.assertEqual(world.goal, (9, 9))
        self.assertIn((2, 2), world.static_obstacles)

    def test_invalid_dimensions(self):
        with self.assertRaises(ValueError):
            GridWorld(width=0, height=10, start=(0, 0), goal=(5, 5))
        with self.assertRaises(ValueError):
            GridWorld(width=10, height=-5, start=(0, 0), goal=(5, 5))

    def test_start_goal_out_of_bounds(self):
        with self.assertRaises(ValueError):
            GridWorld(width=5, height=5, start=(-1, 0), goal=(4, 4))
        with self.assertRaises(ValueError):
            GridWorld(width=5, height=5, start=(0, 0), goal=(5, 5))

    def test_start_equals_goal(self):
        with self.assertRaises(ValueError):
            GridWorld(width=5, height=5, start=(2, 2), goal=(2, 2))

    def test_start_or_goal_on_obstacle(self):
        with self.assertRaises(ValueError):
            GridWorld(width=5, height=5, start=(1, 1), goal=(4, 4), static_obstacles=[(1, 1)])
        with self.assertRaises(ValueError):
            GridWorld(width=5, height=5, start=(1, 1), goal=(4, 4), static_obstacles=[(4, 4)])

    def test_is_within_bounds_and_is_free(self):
        world = GridWorld(width=5, height=5, start=(0, 0), goal=(4, 4), static_obstacles=[(1, 1)])
        self.assertTrue(world.is_within_bounds((2, 2)))
        self.assertFalse(world.is_within_bounds((-1, 2)))
        self.assertFalse(world.is_within_bounds((5, 2)))

        self.assertTrue(world.is_free((0, 1)))
        self.assertFalse(world.is_free((1, 1)))
        self.assertTrue(world.is_occupied((1, 1)))

    def test_add_and_remove_obstacle(self):
        world = GridWorld(width=5, height=5, start=(0, 0), goal=(4, 4))
        world.add_static_obstacle((2, 3))
        self.assertTrue(world.is_occupied((2, 3)))

        world.remove_static_obstacle((2, 3))
        self.assertFalse(world.is_occupied((2, 3)))

    def test_get_neighbors(self):
        world = GridWorld(width=3, height=3, start=(0, 0), goal=(2, 2))
        # Corner: (0, 0) orthogonal has 2 neighbors
        neighbors_4 = world.get_neighbors((0, 0), allow_diagonal=False)
        self.assertEqual(len(neighbors_4), 2)
        self.assertIn((1, 0), neighbors_4)
        self.assertIn((0, 1), neighbors_4)

        # Corner: (0, 0) diagonal has 3 neighbors
        neighbors_diag = world.get_neighbors((0, 0), allow_diagonal=True)
        self.assertEqual(len(neighbors_diag), 3)
        self.assertIn((1, 1), neighbors_diag)

        # Center: (1, 1) has 4 orthogonal, 8 diagonal
        self.assertEqual(len(world.get_neighbors((1, 1), allow_diagonal=False)), 4)
        self.assertEqual(len(world.get_neighbors((1, 1), allow_diagonal=True)), 8)


class TestConfigValidation(unittest.TestCase):
    """Tests for configuration parsing and validation."""

    def test_load_default_config(self):
        config = NavigationConfig.load()
        self.assertGreater(config.environment.width, 0)
        self.assertGreater(config.environment.height, 0)
        self.assertNotEqual(config.environment.start, config.environment.goal)

    def test_invalid_config_heuristics(self):
        with self.assertRaises(ValueError):
            NavigationConfig.from_dict({
                "environment": {"width": 10, "height": 10, "start": [0, 0], "goal": [9, 9]},
                "planning": {"heuristic": "invalid_heuristic"},
            })


if __name__ == "__main__":
    unittest.main()
