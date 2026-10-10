# System Architecture

## 1. Overview & Scope

The **AI-Based Autonomous Navigation System** is a modular Python package simulating 2D grid-based robot navigation. The system models an agent navigating from a start coordinate to a goal coordinate across static obstacles while actively responding to dynamic obstacles via online A* replanning.

> **Scope Note**: The system operates strictly as a discrete 2D grid simulation. It does not employ physical robotics middleware (ROS 2), camera-based computer vision (OpenCV/YOLO), or LiDAR sensor pipelines. The perception subsystem models discrete obstacle-grid state tracking.

---

## 2. High-Level Architecture

```
                       +-----------------------------+
                       |    configs/default.json     |
                       +--------------+--------------+
                                      |
                                      v
                       +-----------------------------+
                       |    NavigationConfig Loader  |
                       +--------------+--------------+
                                      |
       +------------------------------+------------------------------+
       |                              |                              |
       v                              v                              v
+---------------+              +---------------+              +---------------+
|   GridWorld   |              |  ObstacleMap  |              | Dynamic Obs   |
| (Static Grid) |              | (Perception)  |              | (Trajectory)  |
+-------+-------+              +-------+-------+              +-------+-------+
        |                              |                              |
        +-----------------------+------+------------------------------+
                                |
                                v
                       +-----------------+
                       |  AStarPlanner   |
                       |  (A* Algorithm) |
                       +--------+--------+
                                | (Planned Path)
                                v
                       +-----------------+
                       | WaypointContr.  |
                       | (Path Tracking) |
                       +--------+--------+
                                |
                                v
                 +-------------------------------+
                 |      NavigationSimulator      |
                 |  - Dynamic Obstacle Steps     |
                 |  - Obstacle Map Synchronization|
                 |  - Dynamic Block Detection    |
                 |  - Online A* Replanning       |
                 |  - Safety Governor & Stopping |
                 |  - Arrival & Timeout Checks   |
                 +---------------+---------------+
                                 |
                 +---------------+---------------+
                 |                               |
                 v                               v
       +-------------------+           +-------------------+
       | NavigationMetrics |           |SimulationRenderer |
       | (Outputs JSON)    |           | (Outputs PNG)     |
       +-------------------+           +-------------------+
```

---

## 3. Subsystem Breakdown

### 3.1 Environment (`autonomous_navigation.environment.world`)
- **`GridWorld`**: Encapsulates 2D grid dimensions, boundary validation, and immutable static obstacle coordinates.
- **Neighbor Generation**: Computes valid orthogonal (4-connected) and diagonal (8-connected) neighbor transitions.

### 3.2 Perception (`autonomous_navigation.perception.obstacle_map`)
- **`ObstacleMap`**: Represents the current perceived spatial occupancy of the grid.
- Combines static environment obstacles with dynamic obstacle positions updated at each simulation tick.
- Provides queries: `is_occupied(pos)`, `is_free(pos)`, and `get_all_obstacles()`.

### 3.3 Planning (`autonomous_navigation.planning.astar`)
- **`AStarPlanner`**: Computes the shortest collision-free coordinate sequence from current pose to goal.
- Uses priority queue (`heapq`) with deterministic tie-breaking.
- Evaluates Manhattan distance $h(n) = |x_1 - x_2| + |y_1 - y_2|$ or Euclidean distance $h(n) = \sqrt{(x_1 - x_2)^2 + (y_1 - y_2)^2}$.
- Safely handles blocked endpoints, disconnected graphs, and start equals goal edge cases.

### 3.4 Control (`autonomous_navigation.control.controller`)
- **`WaypointController`**: Manages step-by-step progress along the planned waypoint sequence.
- Advances target waypoint as the agent arrives at each waypoint.
- Safely integrates detours and resets targets when a replanned trajectory is supplied.

### 3.5 Simulation & Orchestration (`autonomous_navigation.simulation.simulator`)
- **`DynamicObstacle`**: Simulates moving obstacles along parameterized coordinate paths.
- **`NavigationSimulator`**:
  - Ticks dynamic obstacles each time step.
  - Updates perceived obstacle map.
  - Scans active path ahead: if a dynamic obstacle blocks the remaining path, it initiates an **online A* replan**.
  - **Safety Governor**: If the immediate path is blocked and no alternative route exists, the agent holds position rather than moving into an obstacle.
  - Advances agent position via controller.
  - Checks for collisions, goal arrival, and step limit timeouts.

### 3.6 Evaluation (`autonomous_navigation.evaluation.metrics`)
- Quantifies navigation performance:
  - `success`: Boolean goal arrival flag.
  - `collision`: Boolean obstacle contact flag.
  - `total_steps`: Number of discrete steps taken.
  - `trajectory_length`: Cumulative Euclidean distance traversed.
  - `optimal_path_length`: Length of theoretical static optimal path.
  - `path_efficiency`: Ratio of optimal length to executed length ($\le 1.0$).
  - `replan_count`: Number of dynamic replanning events triggered.
  - `execution_time_seconds`: Runtime duration.

### 3.7 Visualization (`autonomous_navigation.visualization.renderer`)
- Renders the complete simulation trajectory to a 2D plot using Matplotlib (`Agg` non-interactive backend).
- Visualizes static obstacle blocks, dynamic obstacle footprints and endpoints, initial planned route, executed trajectory, and replan locations.

---

## 4. End-to-End Data Flow

1. **Config Ingestion**: `NavigationConfig.load()` parses and validates JSON parameters into typed configuration models.
2. **Environment & Perception Init**: `GridWorld` and `ObstacleMap` initialize grid boundaries and static obstacle sets.
3. **Initial Plan**: `AStarPlanner` generates the initial baseline route from `world.start` to `world.goal`.
4. **Execution Loop (Per Step $t$)**:
   - Dynamic obstacles step forward: $p_{dyn}(t)$.
   - `ObstacleMap` updates dynamic occupancy set.
   - Forward path verification: if any future waypoint $w_k \in \text{path}$ has `is_occupied(w_k) == True`, `AStarPlanner` re-runs from $p_{agent}(t)$ to `goal`.
   - Controller steps agent to next valid cell.
   - Simulation records state snapshot in `history`.
5. **Post-Simulation**:
   - `calculate_metrics()` computes efficiency, step count, and replan frequency.
   - `SimulationRenderer` renders high-resolution PNG figure.

---

## 5. Data Models & Interface Contracts

### 5.1 Simulation Step History (`SimulationHistoryStep`)
```python
@dataclass
class SimulationHistoryStep:
    step: int
    robot_position: Tuple[int, int]
    dynamic_obstacles: Dict[str, Tuple[int, int]]
    replan_triggered: bool
    active_path: List[Tuple[int, int]]
```

### 5.2 Simulation Result (`SimulationResult`)
```python
@dataclass
class SimulationResult:
    success: bool
    collision: bool
    total_steps: int
    replan_count: int
    trajectory: List[Tuple[int, int]]
    history: List[SimulationHistoryStep]
    message: str
    execution_time_seconds: float = 0.0
```

### 5.3 Performance Metrics (`NavigationMetrics`)
```python
@dataclass
class NavigationMetrics:
    success: bool
    collision: bool
    total_steps: int
    trajectory_length: float
    optimal_path_length: float
    path_efficiency: float
    replan_count: int
    execution_time_seconds: float
    message: str
```

---

## 6. Module Mapping & Responsibilities

| Subsystem Module | File Path | Responsibilities |
| :--- | :--- | :--- |
| **Configuration** | `autonomous_navigation/config.py` | Typed loading, boundary and parameter validation, path resolution. |
| **Environment** | `autonomous_navigation/environment/world.py` | 2D GridWorld grid representation, static obstacles, neighbor expansion. |
| **Perception** | `autonomous_navigation/perception/obstacle_map.py` | Combined static and dynamic obstacle occupancy representation. |
| **Planning** | `autonomous_navigation/planning/astar.py` | A* graph search with Manhattan/Euclidean heuristics, 4/8-connected neighbors. |
| **Control** | `autonomous_navigation/control/controller.py` | Waypoint list tracking, goal check, detour path resetting. |
| **Simulation** | `autonomous_navigation/simulation/simulator.py` | Discrete execution loop, obstacle stepping, online A* replanning, collision prevention. |
| **Evaluation** | `autonomous_navigation/evaluation/metrics.py` | Path lengths, efficiency metrics, JSON output serialization. |
| **Visualization**| `autonomous_navigation/visualization/renderer.py` | Matplotlib headless rendering of environment, obstacles, paths, and replans. |
| **Entry Point** | `autonomous_navigation/main.py` | CLI execution entry point and simulation runner. |
