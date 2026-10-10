"""Grid world representation for autonomous navigation simulation."""

from __future__ import annotations

from typing import Iterable, List, Set, Tuple

Coordinate = Tuple[int, int]


class GridWorld:
    """2D Grid World environment defining boundaries and static obstacles."""

    def __init__(
        self,
        width: int,
        height: int,
        start: Coordinate,
        goal: Coordinate,
        static_obstacles: Iterable[Coordinate] | None = None,
    ) -> None:
        if width <= 0 or height <= 0:
            raise ValueError("Grid width and height must be positive integers.")

        self.width = width
        self.height = height
        self.start = start
        self.goal = goal
        self.static_obstacles: Set[Coordinate] = set(static_obstacles or [])

        self._validate_points()

    def _validate_points(self) -> None:
        if not self.is_within_bounds(self.start):
            raise ValueError(f"Start point {self.start} is out of bounds for {self.width}x{self.height} grid.")
        if not self.is_within_bounds(self.goal):
            raise ValueError(f"Goal point {self.goal} is out of bounds for {self.width}x{self.height} grid.")
        if self.start == self.goal:
            raise ValueError("Start and goal points cannot be identical.")
        if self.start in self.static_obstacles:
            raise ValueError(f"Start point {self.start} cannot be placed on an obstacle.")
        if self.goal in self.static_obstacles:
            raise ValueError(f"Goal point {self.goal} cannot be placed on an obstacle.")

    def is_within_bounds(self, pos: Coordinate) -> bool:
        """Check whether position (x, y) is within grid boundaries."""
        x, y = pos
        return 0 <= x < self.width and 0 <= y < self.height

    def is_occupied(self, pos: Coordinate) -> bool:
        """Check whether position contains a static obstacle or is out of bounds."""
        if not self.is_within_bounds(pos):
            return True
        return pos in self.static_obstacles

    def is_free(self, pos: Coordinate) -> bool:
        """Check whether position is within bounds and free of static obstacles."""
        return self.is_within_bounds(pos) and (pos not in self.static_obstacles)

    def add_static_obstacle(self, pos: Coordinate) -> None:
        """Add a static obstacle cell."""
        if not self.is_within_bounds(pos):
            raise ValueError(f"Obstacle coordinate {pos} is out of bounds.")
        if pos == self.start or pos == self.goal:
            raise ValueError(f"Cannot place an obstacle on start {self.start} or goal {self.goal}.")
        self.static_obstacles.add(pos)

    def remove_static_obstacle(self, pos: Coordinate) -> None:
        """Remove a static obstacle cell if present."""
        self.static_obstacles.discard(pos)

    def get_neighbors(self, pos: Coordinate, allow_diagonal: bool = False) -> List[Coordinate]:
        """Generate reachable adjacent grid cells within bounds."""
        x, y = pos
        directions = [
            (0, 1),   # Up
            (0, -1),  # Down
            (1, 0),   # Right
            (-1, 0),  # Left
        ]
        if allow_diagonal:
            directions.extend([
                (1, 1),
                (1, -1),
                (-1, 1),
                (-1, -1),
            ])

        neighbors: List[Coordinate] = []
        for dx, dy in directions:
            neighbor = (x + dx, y + dy)
            if self.is_within_bounds(neighbor):
                neighbors.append(neighbor)
        return neighbors
