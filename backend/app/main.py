"""Main FastAPI application entry point for AI-Based Autonomous Navigation System."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, WebSocket, WebSocketDisconnect # type: ignore
from fastapi.middleware.cors import CORSMiddleware # type: ignore

from backend.app.api.endpoints import get_simulation_service, router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("autonomous_navigation.main")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Lifespan context manager for application startup and graceful shutdown."""
    logger.info("Initializing Autonomous Navigation Backend service...")
    # Pre-initialize simulation service singleton
    service = get_simulation_service()
    logger.info("Simulation service ready with grid %dx%d.", service.world.width, service.world.height)
    yield
    logger.info("Shutting down Autonomous Navigation Backend service...")
    # Clean up any active simulation task
    if service._sim_task and not service._sim_task.done():
        service._sim_task.cancel()


app = FastAPI(
    title="AI-Based Autonomous Navigation System API",
    description="REST and WebSocket API for 2D grid path planning, dynamic obstacle avoidance, and online replanning.",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure CORS for local web development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include REST routes
app.include_router(router)


@app.websocket("/ws/simulation")
async def websocket_simulation_endpoint(websocket: WebSocket) -> None:
    """WebSocket endpoint for real-time simulation updates, state streaming, and events."""
    service = get_simulation_service()
    await service.register_websocket(websocket)
    try:
        while True:
            # Keep receiving client control messages or pings
            data = await websocket.receive_json()
            action = data.get("action")
            if action == "START":
                await service.start()
            elif action == "PAUSE":
                await service.pause()
            elif action == "RESUME":
                await service.resume()
            elif action == "STEP":
                await service.step()
            elif action == "RESET":
                await service.reset()
            elif action == "PING":
                await websocket.send_json({"type": "PONG"})
    except WebSocketDisconnect:
        service.unregister_websocket(websocket)
    except Exception as e:
        logger.debug(f"WebSocket client connection error: {e}")
        service.unregister_websocket(websocket)


if __name__ == "__main__":
    import uvicorn # type: ignore
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=True)
