"""A* Path Planning algorithm for 2D grid environments."""

from __future__ import annotations

import heapq
import math
from typing import Callable, Dict, List, Optional, Tuple

from autonomous_navigation.environment.world import Coordinate
from autonomous_navigation.perception.obstacle_map import ObstacleMap


class AStarPlanner:
    """A* graph search path planner for grid environments."""

    def __init__(
        self,
        obstacle_map: ObstacleMap,
        allow_diagonal: bool = False,
        heuristic: str = "manhattan",
    ) -> None:
        self.obstacle_map = obstacle_map
        self.allow_diagonal = allow_diagonal
        self.heuristic_name = heuristic.lower()
        self._heuristic_func = self._get_heuristic_func(self.heuristic_name)

    @staticmethod
    def _get_heuristic_func(name: str) -> Callable[[Coordinate, Coordinate], float]:
        if name == "manhattan":
            return lambda a, b: float(abs(a[0] - b[0]) + abs(a[1] - b[1]))
        elif name == "euclidean":
            return lambda a, b: math.hypot(a[0] - b[0], a[1] - b[1])
        else:
            raise ValueError(f"Unknown heuristic '{name}'. Must be 'manhattan' or 'euclidean'.")

    def plan(self, start: Coordinate, goal: Coordinate) -> Optional[List[Coordinate]]:
        """Compute the shortest path from start to goal.

        Returns:
            A list of coordinates [start, ..., goal] if a valid path exists,
            or None if the goal is unreachable or endpoints are blocked.
        """
        # Validate endpoints
        if not self.obstacle_map.world.is_within_bounds(start) or not self.obstacle_map.world.is_within_bounds(goal):
            return None

        if self.obstacle_map.is_occupied(start) or self.obstacle_map.is_occupied(goal):
            return None

        if start == goal:
            return [start]

        # Priority queue stores tuples: (f_score, counter, current_node)
        # Counter breaks ties deterministically without comparing coordinates
        tie_breaker = 0
        open_set: List[Tuple[float, int, Coordinate]] = []
        heapq.heappush(open_set, (0.0, tie_breaker, start))

        came_from: Dict[Coordinate, Coordinate] = {}
        g_score: Dict[Coordinate, float] = {start: 0.0}
        closed_set: set[Coordinate] = set()

        while open_set:
            _, _, current = heapq.heappop(open_set)

            if current == goal:
                return self._reconstruct_path(came_from, current)

            if current in closed_set:
                continue
            closed_set.add(current)

            for neighbor, step_cost in self._get_valid_neighbors_with_costs(current):
                if neighbor in closed_set:
                    continue

                tentative_g = g_score[current] + step_cost

                if tentative_g < g_score.get(neighbor, float("inf")):
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g
                    h = self._heuristic_func(neighbor, goal)
                    f = tentative_g + h
                    tie_breaker += 1
                    heapq.heappush(open_set, (f, tie_breaker, neighbor))

        # Goal is unreachable
        return None

    def _get_valid_neighbors_with_costs(self, pos: Coordinate) -> List[Tuple[Coordinate, float]]:
        """Return free neighbors and their transition costs, preventing corner cutting."""
        x, y = pos
        valid_neighbors: List[Tuple[Coordinate, float]] = []

        # 1. 4-connected orthogonal transitions
        orthogonal = [
            ((x + 1, y), 1.0),
            ((x - 1, y), 1.0),
            ((x, y + 1), 1.0),
            ((x, y - 1), 1.0),
        ]
        for neighbor_pos, cost in orthogonal:
            if self.obstacle_map.world.is_within_bounds(neighbor_pos) and not self.obstacle_map.is_occupied(neighbor_pos):
                valid_neighbors.append((neighbor_pos, cost))

        # 2. 8-connected diagonal transitions (with strict corner-cutting prevention)
        if self.allow_diagonal:
            diag_cost = math.sqrt(2)
            diagonal_candidates = [
                ((x + 1, y + 1), (x + 1, y), (x, y + 1)),
                ((x + 1, y - 1), (x + 1, y), (x, y - 1)),
                ((x - 1, y + 1), (x - 1, y), (x, y + 1)),
                ((x - 1, y - 1), (x - 1, y), (x, y - 1)),
            ]
            for target_pos, adj1, adj2 in diagonal_candidates:
                if self.obstacle_map.world.is_within_bounds(target_pos) and not self.obstacle_map.is_occupied(target_pos):
                    # Prevent corner cutting: both adjacent orthogonal cells must not be occupied
                    if not self.obstacle_map.is_occupied(adj1) and not self.obstacle_map.is_occupied(adj2):
                        valid_neighbors.append((target_pos, diag_cost))

        return valid_neighbors

    @staticmethod
    def _reconstruct_path(came_from: Dict[Coordinate, Coordinate], current: Coordinate) -> List[Coordinate]:
        """Backtrack from goal to start to construct path."""
        total_path = [current]
        while current in came_from:
            current = came_from[current]
            total_path.append(current)
        total_path.reverse()
        return total_path
