"""Automated API and integration tests for the Autonomous Navigation FastAPI backend."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from autonomous_navigation.config import NavigationConfig
from backend.app.main import app
from backend.app.api.endpoints import get_simulation_service


@pytest.fixture(autouse=True)
def reset_service_state():
    """Reset the singleton simulation service before each test."""
    service = get_simulation_service()
    default_cfg = NavigationConfig.load()
    service.config = default_cfg
    service._build_components()
    service._init_state()
    yield


client = TestClient(app)


def test_health_check():
    """Test health endpoint returns 200 OK and expected structure."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "service" in data
    assert "version" in data


def test_get_config():
    """Test fetching active configuration."""
    response = client.get("/api/config")
    assert response.status_code == 200
    data = response.json()
    assert "environment" in data
    assert data["environment"]["width"] == 20
    assert data["environment"]["height"] == 20
    assert data["environment"]["start"] == [1, 1]
    assert data["environment"]["goal"] == [18, 18]
    assert "simulation" in data
    assert "planning" in data


def test_update_config_valid():
    """Test updating configuration with valid parameters."""
    new_cfg = {
        "environment": {
            "width": 10,
            "height": 10,
            "start": [0, 0],
            "goal": [9, 9],
            "static_obstacles": [[2, 2], [2, 3], [2, 4]],
        },
        "simulation": {
            "max_steps": 50,
            "dynamic_obstacles": [],
        },
        "planning": {
            "allow_diagonal": True,
            "heuristic": "euclidean",
        },
        "control": {
            "step_size": 1,
            "replan_on_block": True,
        },
    }
    response = client.put("/api/config", json=new_cfg)
    assert response.status_code == 200
    state = response.json()
    assert state["grid_size"] == [10, 10]
    assert state["start_position"] == [0, 0]
    assert state["goal_position"] == [9, 9]
    assert len(state["static_obstacles"]) == 3


def test_update_config_invalid_start_on_obstacle():
    """Test updating configuration with invalid start placed on an obstacle."""
    invalid_cfg = {
        "environment": {
            "width": 10,
            "height": 10,
            "start": [2, 2],
            "goal": [9, 9],
            "static_obstacles": [[2, 2]],
        },
        "simulation": {
            "max_steps": 50,
            "dynamic_obstacles": [],
        },
        "planning": {"allow_diagonal": False, "heuristic": "manhattan"},
        "control": {"step_size": 1, "replan_on_block": True},
    }
    response = client.put("/api/config", json=invalid_cfg)
    assert response.status_code == 422
    assert "obstacle" in response.json()["detail"].lower()


def test_simulation_step_and_reset():
    """Test manual stepping and resetting simulation."""
    # Reset
    reset_resp = client.post("/api/simulation/reset")
    assert reset_resp.status_code == 200
    state = reset_resp.json()
    assert state["step"] == 0
    assert state["status"] == "IDLE"

    # Step 1
    step_resp = client.post("/api/simulation/step")
    assert step_resp.status_code == 200
    state1 = step_resp.json()
    assert state1["step"] == 1
    assert len(state1["trajectory"]) == 2

    # Reset again
    reset_resp2 = client.post("/api/simulation/reset")
    assert reset_resp2.status_code == 200
    assert reset_resp2.json()["step"] == 0


def test_simulation_speed_endpoint():
    """Test setting simulation speed."""
    response = client.post("/api/simulation/speed", json={"speed_ms": 150})
    assert response.status_code == 200
    assert response.json()["speed_ms"] == 150


def test_events_and_clear():
    """Test events logging and clearing."""
    client.post("/api/simulation/reset")
    resp = client.get("/api/events")
    assert resp.status_code == 200
    events = resp.json()
    assert isinstance(events, list)
    assert len(events) > 0

    # Clear events
    del_resp = client.delete("/api/events")
    assert del_resp.status_code == 200

    events_after = client.get("/api/events").json()
    # Should only have the "cleared" log event
    assert len(events_after) == 1
    assert "cleared" in events_after[0]["message"].lower()


def test_full_navigation_to_goal_step_by_step():
    """Test stepping repeatedly until goal reached and checking generated metrics."""
    client.post("/api/simulation/reset")
    reached = False

    for _ in range(100):
        resp = client.post("/api/simulation/step")
        assert resp.status_code == 200
        state = resp.json()
        if state["status"] == "GOAL_REACHED":
            reached = True
            break

    assert reached is True
    assert state["robot_position"] == [18, 18]

    # Check metrics endpoint
    metrics_resp = client.get("/api/metrics")
    assert metrics_resp.status_code == 200
    metrics = metrics_resp.json()
    assert metrics is not None
    assert metrics["success"] is True
    assert metrics["collision"] is False
    assert metrics["total_steps"] > 0
    assert metrics["path_efficiency"] > 0.0

def test_update_config_invalid_out_of_bounds():
    """Test updating configuration with coordinates out of bounds."""
    invalid_cfg = {
        "environment": {
            "width": 10,
            "height": 10,
            "start": [-1, 0],
            "goal": [9, 9],
            "static_obstacles": [],
        },
        "simulation": {"max_steps": 50, "dynamic_obstacles": []},
        "planning": {"allow_diagonal": False, "heuristic": "manhattan"},
        "control": {"step_size": 1, "replan_on_block": True},
    }
    response = client.put("/api/config", json=invalid_cfg)
    assert response.status_code == 422
    assert "bounds" in response.json()["detail"].lower()


def test_update_config_start_equals_goal():
    """Test updating configuration where start equals goal returns validation error."""
    invalid_cfg = {
        "environment": {
            "width": 10,
            "height": 10,
            "start": [5, 5],
            "goal": [5, 5],
            "static_obstacles": [],
        },
        "simulation": {"max_steps": 50, "dynamic_obstacles": []},
        "planning": {"allow_diagonal": False, "heuristic": "manhattan"},
        "control": {"step_size": 1, "replan_on_block": True},
    }
    response = client.put("/api/config", json=invalid_cfg)
    assert response.status_code == 422
    assert "identical" in response.json()["detail"].lower()


def test_unreachable_goal_handling():
    """Test environment where goal is completely surrounded by static obstacles."""
    blocked_cfg = {
        "environment": {
            "width": 5,
            "height": 5,
            "start": [0, 0],
            "goal": [4, 4],
            "static_obstacles": [[3, 4], [4, 3], [3, 3]],
        },
        "simulation": {"max_steps": 10, "dynamic_obstacles": []},
        "planning": {"allow_diagonal": False, "heuristic": "manhattan"},
        "control": {"step_size": 1, "replan_on_block": True},
    }
    response = client.put("/api/config", json=blocked_cfg)
    assert response.status_code == 200
    state = response.json()
    assert state["status"] == "FAILED"
    assert len(state["active_path"]) == 0
    assert "unreachable" in state["message"].lower() or "failed" in state["message"].lower()


def test_get_run_details_not_found():
    """Test requesting non-existent run ID returns 404."""
    response = client.get("/api/runs/non_existent_run_123")
    assert response.status_code == 404


def test_websocket_start_broadcasts_movement():
    """Starting over WebSocket streams the backend's actual state envelope and movement."""
    service = get_simulation_service()
    original_speed = service.speed_ms
    service.set_speed(30)
    client.post("/api/simulation/reset")

    try:
        with client.websocket_connect("/ws/simulation") as websocket:
            initial = websocket.receive_json()
            assert initial["type"] == "STATE_UPDATE"
            assert "data" in initial

            websocket.send_json({"action": "START"})
            state_message = websocket.receive_json()
            while state_message["data"]["step"] == 0:
                state_message = websocket.receive_json()

            assert state_message["type"] == "STATE_UPDATE"
            assert state_message["data"]["robot_position"] != state_message["data"]["start_position"]
    finally:
        client.post("/api/simulation/reset")
        service.set_speed(original_speed)
