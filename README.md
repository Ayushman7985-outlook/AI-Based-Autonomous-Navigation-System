# AI-Based Autonomous Navigation System

A 2D autonomous navigation simulator with A* path planning, static and dynamic obstacle avoidance, real-time route replanning, performance metrics, and a web-based dashboard.

**Repository:** [AI-Based-Autonomous-Navigation-System](https://github.com/Ayushman7985-outlook/AI-Based-Autonomous-Navigation-System)

## Overview

This project demonstrates how an autonomous agent can navigate a grid-based environment, plan a path to a goal, avoid obstacles, and replan its route when dynamic obstacles interfere with its planned trajectory.

The project combines a Python navigation simulator with a FastAPI backend and a React-based frontend for interacting with and monitoring simulations.

## Key Features

- **2D Grid Environment:** Configurable environment dimensions, start and goal positions, and static obstacles.
- **A* Path Planning:** Heuristic-based pathfinding for finding routes through the environment.
- **Dynamic Obstacles:** Simulation of moving obstacles that can interfere with the planned path.
- **Automatic Replanning:** Recalculates a route when an obstacle blocks the active path.
- **Waypoint Control:** Guides the simulated agent through planned waypoints.
- **Performance Evaluation:** Measures navigation steps, trajectory length, path efficiency, and replanning events.
- **Trajectory Visualization:** Uses Matplotlib to visualize the planned route, actual trajectory, and obstacles.
- **Web Dashboard:** React and TypeScript frontend connected to a FastAPI backend.
- **REST API and WebSocket Communication:** Supports backend API operations and live simulation updates.
- **Automated Tests:** Tests for navigation logic, planning, simulation, and API functionality.

## Technology Stack

| Component | Technologies |
|---|---|
| Programming language | Python |
| Path planning | A* search algorithm |
| Simulation | Custom 2D grid-world environment |
| Visualization | Matplotlib |
| Backend | FastAPI, Uvicorn |
| Frontend | React, TypeScript, Vite |
| Communication | REST API, WebSocket |
| Testing | pytest |
| Version control | Git and GitHub |

## Architecture

The project is organized into three main layers.

1. **Navigation and simulation layer:** Creates the grid world, represents obstacles, plans paths, controls waypoints, simulates movement, and calculates metrics.
2. **Backend layer:** Exposes API endpoints and WebSocket communication to connect the simulator with the web interface.
3. **Frontend layer:** Provides the dashboard for starting and monitoring navigation simulations and viewing simulation information.

The overall workflow is:

```text
User
 |
 v
React + TypeScript Dashboard
 |
 | REST API / WebSocket
 v
FastAPI Backend
 |
 v
Navigation Simulator
 |
 +--> Grid Environment
 |
 +--> A* Path Planner
 |
 +--> Waypoint Controller
 |
 +--> Dynamic Obstacle Handling
 |
 +--> Route Replanning
 |
 v
Metrics and Trajectory Visualization
```

## Project Structure

```text
AI-Based-Autonomous-Navigation-System/
|
|-- backend/
|   |-- app/
|   |   |-- main.py
|   |   |-- api/
|   |   |-- services/
|   |   `-- schemas/
|
|-- frontend/
|   |-- src/
|   |-- package.json
|   `-- index.html
|
|-- src/
|   `-- autonomous_navigation/
|       |-- config.py
|       |-- main.py
|       |-- environment/
|       |-- perception/
|       |-- planning/
|       |-- control/
|       |-- simulation/
|       |-- evaluation/
|       `-- visualization/
|
|-- configs/
|   `-- default.json
|
|-- docs/
|   |-- architecture.md
|   |-- implementation_plan.md
|   |-- EXECUTION_LOG.md
|   `-- limitations_and_future_work.md
|
|-- Screenshots/
|-- assets/
|-- examples/
|-- outputs/
|   |-- figures/
|   `-- metrics/
|
|-- tests/
|-- requirements.txt
|-- pyproject.toml
|-- .gitignore
|-- LICENSE
`-- README.md
```

## Getting Started

### Prerequisites

Install the following tools before running the project:

- Python 3.9 or a compatible newer version
- Node.js and npm
- Git

### 1. Clone the repository

Open PowerShell or a terminal and run:

```powershell
git clone https://github.com/Ayushman7985-outlook/AI-Based-Autonomous-Navigation-System.git

cd AI-Based-Autonomous-Navigation-System
```

### 2. Set up the Python environment

Create and activate a virtual environment:

```powershell
python -m venv .venv

.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, run this in the same terminal:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
```

Then activate the environment again.

Install the Python dependencies:

```powershell
python -m pip install --upgrade pip

python -m pip install -r requirements.txt
```

If you want to run the navigation package directly, install the project in editable mode if supported by its package configuration:

```powershell
python -m pip install -e .
```

### 3. Start the FastAPI backend

From the project root, run:

```powershell
python -m uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```

The backend will be available at:

- API base: http://127.0.0.1:8000
- Interactive API documentation: http://127.0.0.1:8000/docs

Keep this terminal running.

### 4. Start the React frontend

Open a **second terminal** in VS Code and run:

```powershell
cd frontend

npm install

npm run dev
```

Open the local URL printed by Vite in your terminal, typically:

http://localhost:5173

Keep both the frontend and backend running while using the dashboard.

> **Note:** The backend API documentation is available at `/docs`. The root API URL does not necessarily serve a webpage; use the frontend URL to access the dashboard.

## Running the Python Simulator

The navigation simulator can also be run independently of the web dashboard.

From the project root, with the virtual environment activated:

```powershell
python -m autonomous_navigation.main
```

To provide a custom configuration:

```powershell
python -m autonomous_navigation.main --config configs/default.json
```

The exact command-line options depend on the simulator's implemented entry point and configuration support.

## Running Tests

From the project root, activate the Python virtual environment and run:

```powershell
python -m pytest tests -v
```

To check the frontend production build, open a terminal in the `frontend` directory and run:

```powershell
npm run build
```

These commands check the Python test suite and compile the frontend for production, respectively.

## Screenshots and Outputs

The repository includes a `Screenshots/` directory for visual evidence of the project.

The simulator can generate trajectory plots and navigation metrics under the `outputs/` directory, depending on the selected execution path and configuration.

Typical outputs include:

- Navigation trajectory visualization
- Planned path and executed trajectory
- Obstacle locations
- Navigation performance metrics
- Replanning information

Generated output files may be excluded from Git by `.gitignore`. Check the repository contents before assuming a generated image or metrics file is available to other users.

## Limitations

- Navigation takes place in a simulated 2D grid environment.
- Obstacle perception is based on simulated environment information rather than physical sensors.
- The project does not currently represent a complete physical robot navigation stack.
- Performance in a grid-world simulation does not establish real-world navigation performance.

## Future Improvements

Potential extensions include:

- More complex path-planning algorithms such as RRT* and Hybrid A*
- More realistic sensor and perception models
- Improved motion planning and control
- Integration with ROS 2
- Testing in a physical or higher-fidelity simulated robot environment

These are potential future extensions, not claims about existing functionality.

## License

This project is distributed under the MIT License. See the [LICENSE](./LICENSE) file for details.

## Author

Developed as an AI-based autonomous navigation project exploring path planning, simulation, dynamic obstacle handling, and full-stack integration.