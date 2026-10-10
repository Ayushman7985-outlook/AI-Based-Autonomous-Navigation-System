# Limitations & Future Work

This document distinguishes currently implemented functionality from architectural limitations and prospective future enhancements.

---

## 1. Implemented Functionality

The currently verified capabilities include:
- **Discrete 2D Grid Representation**: Configurable width and height with boundary bounds checking.
- **Static Obstacle Definition**: Coordinate-based static obstacles forming barriers.
- **A* Shortest-Path Graph Search**: Priority-queue implementation supporting Manhattan and Euclidean heuristics, 4-way orthogonal and 8-way diagonal steps, and unreachable goal detection.
- **Simulated Dynamic Obstacles**: Moving obstacles with predefined cyclical or linear coordinate paths.
- **Online Reactive Replanning**: Real-time path obstruction checks triggering A* route recalculation from the current agent coordinate.
- **Waypoint Navigation Controller**: Discrete waypoint tracking and queue advancement.
- **Deterministic Headless Rendering**: Matplotlib-based trajectory, obstacle, and replan event plotting saved to PNG.
- **Quantitative Metrics Pipeline**: Calculation of step counts, cumulative Euclidean trajectory lengths, theoretical optimal baseline length, path efficiency ratio, and JSON export.
- **Packaging & Test Infrastructure**: Standardized `pyproject.toml`, editable installation mode, and comprehensive `unittest` coverage.

---

## 2. Current Architectural Limitations

1. **Discrete Grid Resolution**: The world operates on discrete integer cells $(x, y)$ rather than continuous $(x, y, \theta)$ state spaces.
2. **Simplified Vehicle Kinematics**: The agent transitions between adjacent grid cells without modeling non-holonomic vehicle constraints (Ackermann steering, turning radius limits, inertia, acceleration/braking curves).
3. **Known Dynamic Obstacle Trajectories**: Dynamic obstacles follow simulated trajectories rather than stochastic intention prediction models.
4. **Idealized Perception Interface**: Obstacle locations are perceived directly from the simulation state without sensor noise, partial observability, occlusions, or false detections.
5. **Single-Agent Decision Making**: Replanning treats moving obstacles as passive transient obstructions rather than interactive agents (game-theoretic interaction).

---

## 3. Prospective Future Enhancements

These items represent planned future roadmap items outside the current scope:

### 3.1 Continuous State Space & Kinematic Planners
- Implement **Hybrid A*** or **RRT*** (Rapidly-exploring Random Trees) incorporating Ackermann vehicle steering geometry.
- Integrate continuous-time trajectory optimization (e.g., Timed Elastic Band or polynomial spline generation).

### 3.2 Sensor & Computer Vision Pipeline
- Camera feed integration with synthetic RGB rendering.
- Deep learning object detection models (e.g., YOLO or MobileNet-SSD) for detecting dynamic obstacles from camera frames.
- Depth estimation or simulated 2D LiDAR raycasting with probabilistic occupancy grid mapping.

### 3.3 Dynamic Prediction & Multi-Agent Planning
- Constant-velocity Kalman Filter tracking for dynamic obstacles.
- Model Predictive Contouring Control (MPCC) for joint dynamic obstacle avoidance and speed profiling.

### 3.4 Hardware & Middleware Integration
- ROS 2 (Robot Operating System) node encapsulation (`rclpy`) for topic-based pub/sub telemetry.
- Gazebo or Webots 3D simulation integration.
