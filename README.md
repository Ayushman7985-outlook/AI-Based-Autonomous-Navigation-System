# AI-Based Autonomous Navigation System

[![Python Version](https://img.shields.io/badge/python-3.9%20%7C%203.10%20%7C%203.11%20%7C%203.12%20%7C%203.13-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Build Status](https://img.shields.io/badge/tests-passing-brightgreen.svg)]()

A modular Python package providing a 2D grid-based autonomous navigation simulation with static obstacle avoidance, A* shortest-path planning, dynamic obstacle simulation, real-time route replanning, and quantitative evaluation.

---

## Table of Contents
- [Project Overview & Objective](#project-overview--objective)
- [Key Features](#key-features)
- [Architecture Overview](#architecture-overview)
- [Repository Structure](#repository-structure)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Running the Simulation](#running-the-simulation)
- [Running Tests](#running-tests)
- [Expected Outputs & Metrics](#expected-outputs--metrics)
- [Limitations & Future Roadmap](#limitations--future-roadmap)
- [License](#license)

---

## Project Overview & Objective

The objective of this repository is to provide a clean, production-grade reference architecture for grid-based autonomous mobile robot navigation. The simulator enables an autonomous agent to plan collision-free routes across static grid environments and dynamically adapt its trajectory when moving obstacles block its active route.

> **Scope Note**: This project simulates 2D grid navigation and discrete obstacle state perception. It does not include camera-based computer vision (YOLO/OpenCV), LiDAR point clouds, ROS 2 middleware, or physical robot deployment.

---

## Key Features

- **2D Grid Environment**: Configurable dimensions, boundaries, start/goal positions, and static obstacles.
- **A* Path Planner**: Optimized priority-queue A* algorithm supporting Manhattan and Euclidean heuristics, 4-connected and 8-connected (diagonal) motion, and blocked endpoint detection.
- **Simulated Dynamic Obstacles**: Configurable moving obstacles with scripted or patrolling trajectories.
- **Dynamic Replanning Engine**: Automatic detection of obstructed future path segments with on-the-fly A* route recalculation.
- **Waypoint Controller**: Discrete waypoint queue tracking and advancement.
- **Quantitative Metrics**: Automated calculation of steps taken, trajectory length, baseline optimal length, path efficiency ratio, and replan events.
- **Headless Visualization**: Matplotlib renderer generating trajectory diagrams with obstacles, paths, and replan events.
- **Unit & Integration Test Suite**: Complete coverage with Python's standard `unittest` framework.

---

## Architecture Overview

```
                        configs/default.json
                                 │
                                 ▼
                     autonomous_navigation.config
                                 │
         ┌───────────────────────┼───────────────────────┐
         ▼                       ▼                       ▼
   environment/world      perception/obstacle_map   DynamicObstacle
         │                       │                       │
         └───────────────┬───────┘                       │
                         ▼                               ▼
                   planning/astar              simulation/simulator
                         │                               │
                         ▼                               ▼
                 control/controller            evaluation/metrics &
                                               visualization/renderer
```

For detailed architectural specifications, see [docs/architecture.md](docs/architecture.md).

---

## Repository Structure

```
AI-Autonomous-Navigation-System/
├── configs/
│   └── default.json             # Environment and simulation configuration
├── docs/
│   ├── architecture.md          # Detailed architecture, data flow, and schemas
│   ├── implementation_plan.md   # Milestone roadmap and status
│   ├── limitations_and_future_work.md # Current scope vs future enhancements
│   ├── EXECUTION_LOG.md         # Milestone and validation history
│   └── README.md                # Documentation index
├── outputs/
│   ├── figures/                 # Rendered simulation trajectory PNGs
│   │   └── .gitkeep
│   └── metrics/                 # Exported simulation metrics JSONs
│       └── .gitkeep
├── src/
│   └── autonomous_navigation/
│       ├── __init__.py
│       ├── config.py            # Typed config loading and validation
│       ├── main.py              # CLI entry point and orchestration
│       ├── control/
│       │   ├── __init__.py
│       │   └── controller.py    # Waypoint-following controller
│       ├── environment/
│       │   ├── __init__.py
│       │   └── world.py         # 2D GridWorld and obstacle geometry
│       ├── evaluation/
│       │   ├── __init__.py
│       │   └── metrics.py       # Performance metrics calculation
│       ├── perception/
│       │   ├── __init__.py
│       │   └── obstacle_map.py  # Sensed spatial occupancy map
│       ├── planning/
│       │   ├── __init__.py
│       │   └── astar.py         # A* path planning implementation
│       ├── simulation/
│       │   ├── __init__.py
│       │   └── simulator.py     # Dynamic execution loop and replanner
│       └── visualization/
│           ├── __init__.py
│           └── renderer.py      # Matplotlib trajectory renderer
├── tests/
│   ├── __init__.py
│   ├── test_controller.py       # Controller waypoint progression tests
│   ├── test_environment.py      # GridWorld boundaries and config tests
│   ├── test_metrics.py          # Metric accuracy and JSON tests
│   ├── test_planner.py          # A* optimality and avoidance tests
│   └── test_simulator.py        # End-to-end simulation and replan tests
├── assets/
│   └── .gitkeep
├── examples/
│   └── .gitkeep
├── .gitignore
├── LICENSE                      # MIT License
├── pyproject.toml               # Package build metadata
├── README.md                    # Project documentation (this file)
└── requirements.txt             # Runtime dependencies
```

---

## Prerequisites

- **Python**: 3.9 or higher (tested on Python 3.13)
- **Pip**: Latest version recommended

---

## Installation

Clone the repository and install in editable mode:

```bash
# Clone the repository
git clone https://github.com/your-username/AI-Autonomous-Navigation-System.git
cd AI-Autonomous-Navigation-System

# Install package and dependencies in editable mode
python -m pip install -e .
```

Alternatively, install dependencies directly from `requirements.txt`:

```bash
python -m pip install -r requirements.txt
```

---

## Running the Simulation

Execute the navigation simulator using default configuration:

```bash
python -m autonomous_navigation.main
```

Or pass a custom configuration file:

```bash
python -m autonomous_navigation.main --config configs/default.json
```

---

## Running Tests

Run the complete automated test suite using `unittest`:

```bash
python -m unittest discover -s tests -v
```

Or run via `pytest`:

```bash
python -m pytest tests -v
```

---

## Expected Outputs & Metrics

Upon executing the simulation, the system produces:

1. **Terminal Summary**:
   ```
   ============================================================
     AI-Based Autonomous Navigation System
   ============================================================
   ✓ Configuration successfully loaded and validated.
   ✓ World initialized: 20x20 grid | Start: (1, 1) | Goal: (18, 18)
   ✓ Dynamic obstacles configured: 2 active agent(s)
   ▶ Executing simulation run...
   ✓ Metrics saved to: outputs/metrics/navigation_metrics.json
   ✓ Figure saved to: outputs/figures/simulation_trajectory.png
   ------------------------------------------------------------
   Status           : SUCCESS
   Message          : Goal successfully reached.
   Total Steps      : 34
   Replanning Events: 2
   Path Efficiency  : 100.0%
   Execution Time   : 0.0084 s
   ============================================================
   ```

2. **Metrics File** (`outputs/metrics/navigation_metrics.json`):
   ```json
   {
     "success": true,
     "collision": false,
     "total_steps": 34,
     "trajectory_length": 34.0,
     "optimal_path_length": 34.0,
     "path_efficiency": 1.0,
     "replan_count": 2,
     "execution_time_seconds": 0.008412,
     "message": "Goal successfully reached."
   }
   ```

3. **Trajectory Plot** (`outputs/figures/simulation_trajectory.png`): High-resolution plot illustrating the 2D grid, static barriers, dynamic obstacles, planned path, actual trajectory, and replanning events.

---

## Limitations & Future Roadmap

For detailed limitations and roadmaps, see [docs/limitations_and_future_work.md](docs/limitations_and_future_work.md).

- **Current Boundaries**: Discrete grid resolution, holonomic movements without Ackermann steering constraints, and idealized obstacle state sensing.
- **Future Enhancements**: Continuous state space planning (Hybrid A* / RRT*), sensor noise modeling, Model Predictive Control (MPC), and ROS 2 middleware support.

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
