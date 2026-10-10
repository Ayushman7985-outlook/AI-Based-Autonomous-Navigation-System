"""Waypoint following controller for grid-based autonomous navigation."""

from __future__ import annotations

from typing import List, Optional

from autonomous_navigation.environment.world import Coordinate


class WaypointController:
    """Controller that guides the agent sequentially along planned waypoints."""

    def __init__(self, step_size: int = 1) -> None:
        self.step_size = step_size
        self._path: List[Coordinate] = []
        self._waypoint_index: int = 0

    def set_path(self, path: List[Coordinate], current_pos: Optional[Coordinate] = None) -> None:
        """Assign a new or replanned trajectory path."""
        self._path = list(path) if path else []
        self._waypoint_index = 0

        if current_pos and self._path:
            # If current position is in the path, advance index to next step
            if current_pos in self._path:
                idx = self._path.index(current_pos)
                self._waypoint_index = min(idx + 1, len(self._path))
            elif self._path and self._path[0] == current_pos:
                self._waypoint_index = 1 if len(self._path) > 1 else 0

    @property
    def path(self) -> List[Coordinate]:
        return list(self._path)

    @property
    def current_waypoint_index(self) -> int:
        return self._waypoint_index

    def has_next_waypoint(self) -> bool:
        """Check if there are remaining waypoints to visit."""
        return self._waypoint_index < len(self._path)

    def get_target_waypoint(self) -> Optional[Coordinate]:
        """Return the current target waypoint without advancing."""
        if self.has_next_waypoint():
            return self._path[self._waypoint_index]
        return None

    def step(self, current_pos: Coordinate) -> Coordinate:
        """Determine and return the next position command.

        If the agent has reached the current target waypoint, advances
        to the next waypoint in the queue.
        """
        if not self._path:
            return current_pos

        if self.has_next_waypoint():
            target = self._path[self._waypoint_index]
            if current_pos == target:
                self._waypoint_index += 1
                if self.has_next_waypoint():
                    return self._path[self._waypoint_index]
                return current_pos
            return target

        return current_pos

    def is_goal_reached(self, current_pos: Coordinate, goal: Coordinate) -> bool:
        """Return True if the agent is at the goal location."""
        return current_pos == goal

    def get_remaining_waypoints(self) -> List[Coordinate]:
        """Return list of waypoints that have not yet been reached."""
        if not self.has_next_waypoint():
            return []
        return self._path[self._waypoint_index:]
