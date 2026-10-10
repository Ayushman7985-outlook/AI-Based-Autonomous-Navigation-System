"""FastAPI REST API routing endpoints for Autonomous Navigation."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status

from backend.app.schemas.models import (
    HealthResponse,
    NavigationConfigSchema,
    NavigationMetricsSchema,
    SimulationEvent,
    SimulationRunRecord,
    SimulationSpeedRequest,
    SimulationStepState,
)
from backend.app.services.simulation_service import SimulationService

router = APIRouter(prefix="/api", tags=["Autonomous Navigation"])

# Shared service instance singleton getter
_simulation_service: Optional[SimulationService] = None


def get_simulation_service() -> SimulationService:
    global _simulation_service
    if _simulation_service is None:
        _simulation_service = SimulationService()
    return _simulation_service


# ---------------- System Health ----------------

@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check",
    description="Verify backend service status and engine availability.",
)
async def health_check() -> HealthResponse:
    return HealthResponse(
        status="ok",
        service="AI-Based Autonomous Navigation Backend",
        version="1.0.0",
        timestamp=datetime.now().isoformat(),
    )


# ---------------- Configuration ----------------

@router.get(
    "/config",
    response_model=NavigationConfigSchema,
    summary="Get current configuration",
    description="Retrieve the currently active environment, planner, controller, and simulation configuration.",
)
async def get_config(
    service: SimulationService = Depends(get_simulation_service),
) -> NavigationConfigSchema:
    cfg = service.config
    return NavigationConfigSchema(
        environment={
            "width": cfg.environment.width,
            "height": cfg.environment.height,
            "start": cfg.environment.start,
            "goal": cfg.environment.goal,
            "static_obstacles": cfg.environment.static_obstacles,
        },
        simulation={
            "max_steps": cfg.simulation.max_steps,
            "dynamic_obstacles": [
                {
                    "id": d.id,
                    "initial_position": d.initial_position,
                    "trajectory": d.trajectory,
                }
                for d in cfg.simulation.dynamic_obstacles
            ],
        },
        planning={
            "allow_diagonal": cfg.planning.allow_diagonal,
            "heuristic": cfg.planning.heuristic,
        },
        control={
            "step_size": cfg.control.step_size,
            "replan_on_block": cfg.control.replan_on_block,
        },
        visualization={
            "save_figure": cfg.visualization.save_figure,
            "figure_path": str(cfg.visualization.figure_path),
            "figure_title": cfg.visualization.figure_title,
        },
        evaluation={
            "save_metrics": cfg.evaluation.save_metrics,
            "metrics_path": str(cfg.evaluation.metrics_path),
        },
    )


@router.put(
    "/config",
    response_model=SimulationStepState,
    summary="Update configuration",
    description="Update simulation and environment settings. Re-validates and re-initializes the environment.",
)
async def update_config(
    new_config: NavigationConfigSchema,
    service: SimulationService = Depends(get_simulation_service),
) -> SimulationStepState:
    try:
        return await service.update_config(new_config)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Configuration validation error: {str(e)}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal error applying configuration: {str(e)}",
        )


@router.post(
    "/config/reset",
    response_model=SimulationStepState,
    summary="Reset configuration to defaults",
    description="Restores the environment and simulation configuration back to configs/default.json.",
)
async def reset_config_to_default(
    service: SimulationService = Depends(get_simulation_service),
) -> SimulationStepState:
    try:
        return await service.reset_to_default_config()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reset configuration: {str(e)}",
        )


# ---------------- Simulation Execution Controls ----------------

@router.post(
    "/simulation/start",
    response_model=SimulationStepState,
    summary="Start simulation",
    description="Starts or continues autonomous navigation simulation execution.",
)
async def start_simulation(
    service: SimulationService = Depends(get_simulation_service),
) -> SimulationStepState:
    return await service.start()


@router.post(
    "/simulation/pause",
    response_model=SimulationStepState,
    summary="Pause simulation",
    description="Pauses the currently running simulation.",
)
async def pause_simulation(
    service: SimulationService = Depends(get_simulation_service),
) -> SimulationStepState:
    return await service.pause()


@router.post(
    "/simulation/resume",
    response_model=SimulationStepState,
    summary="Resume simulation",
    description="Resumes a paused simulation.",
)
async def resume_simulation(
    service: SimulationService = Depends(get_simulation_service),
) -> SimulationStepState:
    return await service.resume()


@router.post(
    "/simulation/step",
    response_model=SimulationStepState,
    summary="Step forward once",
    description="Advances the simulation by a single discrete time step.",
)
async def step_simulation(
    service: SimulationService = Depends(get_simulation_service),
) -> SimulationStepState:
    return await service.step()


@router.post(
    "/simulation/reset",
    response_model=SimulationStepState,
    summary="Reset simulation",
    description="Resets the agent position, obstacles, and path planning back to step 0.",
)
async def reset_simulation(
    service: SimulationService = Depends(get_simulation_service),
) -> SimulationStepState:
    return await service.reset()


@router.post(
    "/simulation/speed",
    summary="Set simulation speed",
    description="Update step delay duration in milliseconds.",
)
async def set_simulation_speed(
    payload: SimulationSpeedRequest,
    service: SimulationService = Depends(get_simulation_service),
) -> Dict[str, Any]:
    service.set_speed(payload.speed_ms)
    return {"speed_ms": service.speed_ms, "status": "updated"}


@router.get(
    "/simulation/state",
    response_model=SimulationStepState,
    summary="Get current state snapshot",
    description="Returns the full state of the grid, agent, active path, trajectory, and dynamic obstacles.",
)
async def get_simulation_state(
    service: SimulationService = Depends(get_simulation_service),
) -> SimulationStepState:
    return service.get_state()


@router.get(
    "/simulation/status",
    summary="Get status summary",
    description="Returns high-level status flag, step number, and message.",
)
async def get_simulation_status(
    service: SimulationService = Depends(get_simulation_service),
) -> Dict[str, Any]:
    state = service.get_state()
    return {
        "status": state.status,
        "step": state.step,
        "robot_position": state.robot_position,
        "replan_count": state.replan_count,
        "message": state.message,
    }


# ---------------- Metrics and History ----------------

@router.get(
    "/metrics",
    response_model=Optional[NavigationMetricsSchema],
    summary="Get latest metrics",
    description="Returns performance metrics of the latest completed or evaluated simulation run.",
)
async def get_metrics(
    service: SimulationService = Depends(get_simulation_service),
) -> Optional[NavigationMetricsSchema]:
    return service.get_metrics()


@router.get(
    "/history",
    response_model=List[SimulationRunRecord],
    summary="Get run history",
    description="Returns summary records of all completed simulation runs.",
)
@router.get(
    "/runs",
    response_model=List[SimulationRunRecord],
    summary="Get run history",
    description="Returns summary records of all completed simulation runs.",
)
async def get_runs(
    service: SimulationService = Depends(get_simulation_service),
) -> List[SimulationRunRecord]:
    return service.get_runs()


@router.get(
    "/history/{run_id}",
    response_model=SimulationRunRecord,
    summary="Get single run details",
    description="Retrieve details and metrics of a specific historical run.",
)
@router.get(
    "/runs/{run_id}",
    response_model=SimulationRunRecord,
    summary="Get single run details",
    description="Retrieve details and metrics of a specific historical run.",
)
async def get_run_details(
    run_id: str,
    service: SimulationService = Depends(get_simulation_service),
) -> SimulationRunRecord:
    for run in service.get_runs():
        if run.run_id == run_id:
            return run
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Run '{run_id}' not found.")


# ---------------- Audit Events ----------------

@router.get(
    "/events",
    response_model=List[SimulationEvent],
    summary="Get event log",
    description="Returns real-time simulation audit event log entries.",
)
async def get_events(
    service: SimulationService = Depends(get_simulation_service),
) -> List[SimulationEvent]:
    return service.get_events()


@router.delete(
    "/events",
    summary="Clear event log",
    description="Clears recorded audit event entries.",
)
async def clear_events(
    service: SimulationService = Depends(get_simulation_service),
) -> Dict[str, str]:
    service.clear_events()
    return {"status": "cleared"}
