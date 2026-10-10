"""Perception interface managing static and dynamic obstacle occupancy states."""

from __future__ import annotations

from typing import Iterable, Set, Tuple

from autonomous_navigation.environment.world import Coordinate, GridWorld


class ObstacleMap:
    """Manages the current obstacle occupancy state of the grid world.

    Acts as the perception interface combining static environment geometry
    with sensed dynamic obstacle states.
    """

    def __init__(self, world: GridWorld) -> None:
        self.world = world
        self._dynamic_obstacles: Set[Coordinate] = set()

    @property
    def width(self) -> int:
        return self.world.width

    @property
    def height(self) -> int:
        return self.world.height

    def update_dynamic_obstacles(self, dynamic_positions: Iterable[Coordinate]) -> None:
        """Update currently sensed positions of dynamic obstacles."""
        self._dynamic_obstacles = {
            pos for pos in dynamic_positions if self.world.is_within_bounds(pos)
        }

    def clear_dynamic_obstacles(self) -> None:
        """Clear all active dynamic obstacles."""
        self._dynamic_obstacles.clear()

    def is_occupied(self, pos: Coordinate) -> bool:
        """Return True if position is out of bounds, static obstacle, or dynamic obstacle."""
        if not self.world.is_within_bounds(pos):
            return True
        if self.world.is_occupied(pos):
            return True
        return pos in self._dynamic_obstacles

    def is_free(self, pos: Coordinate) -> bool:
        """Return True if position is within bounds and free of all obstacles."""
        return not self.is_occupied(pos)

    def get_static_obstacles(self) -> Set[Coordinate]:
        """Return set of all static obstacle coordinates."""
        return set(self.world.static_obstacles)

    def get_dynamic_obstacles(self) -> Set[Coordinate]:
        """Return copy of currently active dynamic obstacle coordinates."""
        return set(self._dynamic_obstacles)

    def get_all_obstacles(self) -> Set[Coordinate]:
        """Return union of static and dynamic obstacle coordinates."""
        return self.world.static_obstacles.union(self._dynamic_obstacles)
