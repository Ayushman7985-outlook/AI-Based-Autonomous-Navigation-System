"""Integration tests for NavigationSimulator and dynamic replanning."""

import unittest
from autonomous_navigation.control.controller import WaypointController
from autonomous_navigation.environment.world import GridWorld
from autonomous_navigation.perception.obstacle_map import ObstacleMap
from autonomous_navigation.planning.astar import AStarPlanner
from autonomous_navigation.simulation.simulator import DynamicObstacle, NavigationSimulator


class TestNavigationSimulator(unittest.TestCase):
    """Tests covering end-to-end simulation, dynamic obstacle encounters, and replanning."""

    def test_successful_navigation_without_obstacles(self):
        world = GridWorld(width=5, height=5, start=(0, 0), goal=(0, 4))
        obstacle_map = ObstacleMap(world)
        planner = AStarPlanner(obstacle_map)
        controller = WaypointController()
        simulator = NavigationSimulator(
            world=world,
            obstacle_map=obstacle_map,
            planner=planner,
            controller=controller,
            max_steps=20,
        )

        result = simulator.run()
        self.assertTrue(result.success)
        self.assertFalse(result.collision)
        self.assertEqual(result.trajectory[-1], (0, 4))
        self.assertEqual(result.total_steps, 4)

    def test_dynamic_obstacle_triggers_replanning(self):
        # 5x5 grid, start at (0, 0), goal at (4, 0).
        # Initial straight path along y=0: [(0,0), (1,0), (2,0), (3,0), (4,0)]
        # Dynamic obstacle steps into (2, 0) right as the agent approaches,
        # forcing the planner to detour through y=1.
        world = GridWorld(width=5, height=5, start=(0, 0), goal=(4, 0))
        obstacle_map = ObstacleMap(world)
        planner = AStarPlanner(obstacle_map)
        controller = WaypointController()

        # Dynamic obstacle starts at (2, 2) and steps down to (2, 0)
        dyn_obs = DynamicObstacle(
            id="blocking_agent",
            initial_position=(2, 2),
            trajectory=[(2, 2), (2, 1), (2, 0), (2, 0), (2, 0)],
        )

        simulator = NavigationSimulator(
            world=world,
            obstacle_map=obstacle_map,
            planner=planner,
            controller=controller,
            dynamic_obstacles=[dyn_obs],
            max_steps=30,
            replan_on_block=True,
        )

        result = simulator.run()
        self.assertTrue(result.success)
        self.assertFalse(result.collision)
        self.assertGreater(result.replan_count, 0)
        self.assertEqual(result.trajectory[-1], (4, 0))

    def test_robot_stops_when_path_blocked_and_unreachable(self):
        """When an obstacle completely blocks the route and no detour exists,

        robot stops and waits safely rather than driving into the obstacle.
        """
        # Corridor: 5x1 grid (height=1, width=5) from (0,0) to (4,0)
        world = GridWorld(width=5, height=1, start=(0, 0), goal=(4, 0))
        obstacle_map = ObstacleMap(world)
        planner = AStarPlanner(obstacle_map)
        controller = WaypointController()

        # Dynamic obstacle blocks the only corridor at (2, 0) permanently
        dyn_obs = DynamicObstacle(
            id="corridor_blocker",
            initial_position=(2, 0),
            trajectory=[(2, 0)] * 10,
        )

        simulator = NavigationSimulator(
            world=world,
            obstacle_map=obstacle_map,
            planner=planner,
            controller=controller,
            dynamic_obstacles=[dyn_obs],
            max_steps=5,
            replan_on_block=True,
        )

        result = simulator.run()
        # Must NOT succeed, and must NOT collide
        self.assertFalse(result.success)
        self.assertFalse(result.collision)
        # Robot never reached (2, 0)
        for pos in result.trajectory:
            self.assertNotEqual(pos, (2, 0))

    def test_collision_free_movement_guarantee(self):
        """In a multi-agent dynamic obstacle scenario, the robot never enters an occupied cell."""
        world = GridWorld(
            width=8,
            height=8,
            start=(0, 0),
            goal=(7, 7),
            static_obstacles=[(3, 3), (3, 4), (4, 3)],
        )
        obstacle_map = ObstacleMap(world)
        planner = AStarPlanner(obstacle_map)
        controller = WaypointController()

        dyn_obs_1 = DynamicObstacle(
            id="patrol_1",
            initial_position=(2, 2),
            trajectory=[(2, 2), (2, 3), (2, 4), (2, 3)],
        )
        dyn_obs_2 = DynamicObstacle(
            id="patrol_2",
            initial_position=(5, 5),
            trajectory=[(5, 5), (4, 5), (3, 5), (4, 5)],
        )

        simulator = NavigationSimulator(
            world=world,
            obstacle_map=obstacle_map,
            planner=planner,
            controller=controller,
            dynamic_obstacles=[dyn_obs_1, dyn_obs_2],
            max_steps=50,
            replan_on_block=True,
        )

        result = simulator.run()
        self.assertFalse(result.collision)

        # Verify against all recorded simulation history steps
        for step_data in result.history:
            robot_pos = step_data.robot_position
            # Verify robot position was never on a static obstacle
            self.assertNotIn(robot_pos, world.static_obstacles)
            # Verify robot position was never on any dynamic obstacle at that step
            for _, dyn_pos in step_data.dynamic_obstacles.items():
                self.assertNotEqual(robot_pos, dyn_pos)

    def test_timeout_when_max_steps_exceeded(self):
        world = GridWorld(width=10, height=10, start=(0, 0), goal=(9, 9))
        obstacle_map = ObstacleMap(world)
        planner = AStarPlanner(obstacle_map)
        controller = WaypointController()
        # Set max_steps very low so agent cannot reach goal
        simulator = NavigationSimulator(
            world=world,
            obstacle_map=obstacle_map,
            planner=planner,
            controller=controller,
            max_steps=3,
        )

        result = simulator.run()
        self.assertFalse(result.success)
        self.assertIn("exceeded", result.message)


if __name__ == "__main__":
    unittest.main()
