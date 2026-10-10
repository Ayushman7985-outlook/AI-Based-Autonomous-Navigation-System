import React, { useRef, useEffect, useState, useCallback } from 'react';
import type { Coordinate, InteractiveTool, SimulationStepState } from '../types/navigation';

interface NavigationCanvasProps {
  state: SimulationStepState | null;
  activeTool: InteractiveTool;
  onCellClick: (coord: Coordinate) => void;
  onCellDrag: (coords: Coordinate[]) => void;
}

export const NavigationCanvas: React.FC<NavigationCanvasProps> = ({
  state,
  activeTool,
  onCellClick,
  onCellDrag,
}) => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const containerRef = useRef<HTMLDivElement | null>(null);
  const [hoveredCell, setHoveredCell] = useState<Coordinate | null>(null);
  const [isMouseDown, setIsMouseDown] = useState(false);
  const draggedCellsRef = useRef<Set<string>>(new Set());

  const gridWidth = state?.grid_size?.[0] || 20;
  const gridHeight = state?.grid_size?.[1] || 20;

  // Coordinate helper: Canvas pixels -> Grid (x, y)
  const getGridCoordFromEvent = useCallback(
    (e: React.MouseEvent<HTMLCanvasElement>): Coordinate | null => {
      const canvas = canvasRef.current;
      if (!canvas) return null;
      const rect = canvas.getBoundingClientRect();
      const scaleX = canvas.width / rect.width;
      const scaleY = canvas.height / rect.height;

      const clickX = (e.clientX - rect.left) * scaleX;
      const clickY = (e.clientY - rect.top) * scaleY;

      const padding = 20;
      const drawW = canvas.width - padding * 2;
      const drawH = canvas.height - padding * 2;

      if (
        clickX < padding ||
        clickX > canvas.width - padding ||
        clickY < padding ||
        clickY > canvas.height - padding
      ) {
        return null;
      }

      const cellSize = Math.min(drawW / gridWidth, drawH / gridHeight);
      const offsetX = padding + (drawW - cellSize * gridWidth) / 2;
      const offsetY = padding + (drawH - cellSize * gridHeight) / 2;

      const gx = Math.floor((clickX - offsetX) / cellSize);
      // Invert Y coordinate so (0,0) is at bottom-left
      const gy = gridHeight - 1 - Math.floor((clickY - offsetY) / cellSize);

      if (gx >= 0 && gx < gridWidth && gy >= 0 && gy < gridHeight) {
        return [gx, gy];
      }
      return null;
    },
    [gridWidth, gridHeight]
  );

  // Main Canvas Render Loop
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // High DPI Support
    const dpr = window.devicePixelRatio || 1;
    const rect = canvas.getBoundingClientRect();
    if (rect.width > 0 && rect.height > 0) {
      canvas.width = rect.width * dpr;
      canvas.height = rect.height * dpr;
      ctx.scale(dpr, dpr);
    }

    const width = rect.width;
    const height = rect.height;

    // Clear Canvas
    ctx.clearRect(0, 0, width, height);

    // Background Gradient
    const bgGrad = ctx.createLinearGradient(0, 0, width, height);
    bgGrad.addColorStop(0, '#0a0d14');
    bgGrad.addColorStop(1, '#0e131f');
    ctx.fillStyle = bgGrad;
    ctx.fillRect(0, 0, width, height);

    const padding = 24;
    const drawW = width - padding * 2;
    const drawH = height - padding * 2;
    const cellSize = Math.min(drawW / gridWidth, drawH / gridHeight);
    const offsetX = padding + (drawW - cellSize * gridWidth) / 2;
    const offsetY = padding + (drawH - cellSize * gridHeight) / 2;

    // Helper: Grid (x, y) -> Canvas pixel rect (top-left x, top-left y)
    const toCanvasPos = (x: number, y: number) => {
      const px = offsetX + x * cellSize;
      const py = offsetY + (gridHeight - 1 - y) * cellSize;
      return { px, py };
    };

    // 1. Draw Grid Cells & Lattice
    ctx.lineWidth = 1;
    for (let x = 0; x < gridWidth; x++) {
      for (let y = 0; y < gridHeight; y++) {
        const { px, py } = toCanvasPos(x, y);

        ctx.fillStyle = (x + y) % 2 === 0 ? 'rgba(255, 255, 255, 0.015)' : 'rgba(255, 255, 255, 0.025)';
        ctx.fillRect(px, py, cellSize, cellSize);

        ctx.strokeStyle = 'rgba(255, 255, 255, 0.05)';
        ctx.strokeRect(px, py, cellSize, cellSize);
      }
    }

    // 2. Draw Trajectory History Trail
    if (state?.trajectory && state.trajectory.length > 1) {
      ctx.save();
      for (let i = 0; i < state.trajectory.length - 1; i++) {
        const [x1, y1] = state.trajectory[i];
        const [x2, y2] = state.trajectory[i + 1];
        const p1 = toCanvasPos(x1, y1);
        const p2 = toCanvasPos(x2, y2);

        const progress = (i + 1) / state.trajectory.length;
        ctx.strokeStyle = `rgba(168, 85, 247, ${0.2 + progress * 0.6})`;
        ctx.lineWidth = Math.max(2, cellSize * 0.2);
        ctx.lineCap = 'round';

        ctx.beginPath();
        ctx.moveTo(p1.px + cellSize / 2, p1.py + cellSize / 2);
        ctx.lineTo(p2.px + cellSize / 2, p2.py + cellSize / 2);
        ctx.stroke();

        // Breadcrumb dots
        ctx.fillStyle = `rgba(168, 85, 247, ${0.4 + progress * 0.6})`;
        ctx.beginPath();
        ctx.arc(p1.px + cellSize / 2, p1.py + cellSize / 2, cellSize * 0.12, 0, Math.PI * 2);
        ctx.fill();
      }
      ctx.restore();
    }

    // 3. Draw Planned A* Path (Neon Cyan Ribbon)
    if (state?.active_path && state.active_path.length > 0) {
      ctx.save();
      ctx.strokeStyle = '#00f0ff';
      ctx.lineWidth = Math.max(3, cellSize * 0.25);
      ctx.shadowColor = 'rgba(0, 240, 255, 0.8)';
      ctx.shadowBlur = 12;
      ctx.lineCap = 'round';
      ctx.lineJoin = 'round';
      ctx.setLineDash([6, 4]);

      ctx.beginPath();
      state.active_path.forEach(([x, y], idx) => {
        const { px, py } = toCanvasPos(x, y);
        const cx = px + cellSize / 2;
        const cy = py + cellSize / 2;
        if (idx === 0) ctx.moveTo(cx, cy);
        else ctx.lineTo(cx, cy);
      });
      ctx.stroke();
      ctx.restore();

      // Path waypoint nodes
      state.active_path.forEach(([x, y]) => {
        const { px, py } = toCanvasPos(x, y);
        ctx.fillStyle = '#00f0ff';
        ctx.shadowColor = '#00f0ff';
        ctx.shadowBlur = 6;
        ctx.beginPath();
        ctx.arc(px + cellSize / 2, py + cellSize / 2, cellSize * 0.1, 0, Math.PI * 2);
        ctx.fill();
        ctx.shadowBlur = 0;
      });
    }

    // 4. Draw Static Obstacles
    if (state?.static_obstacles) {
      state.static_obstacles.forEach(([x, y]) => {
        const { px, py } = toCanvasPos(x, y);
        const margin = 2;
        const rw = cellSize - margin * 2;
        const rh = cellSize - margin * 2;

        ctx.save();
        // Dark slate fill
        const obsGrad = ctx.createLinearGradient(px, py, px + rw, py + rh);
        obsGrad.addColorStop(0, '#334155');
        obsGrad.addColorStop(1, '#1e293b');
        ctx.fillStyle = obsGrad;

        // Rounded rect for obstacles
        const radius = Math.min(4, cellSize * 0.15);
        ctx.beginPath();
        ctx.roundRect(px + margin, py + margin, rw, rh, radius);
        ctx.fill();

        ctx.strokeStyle = 'rgba(148, 163, 184, 0.3)';
        ctx.lineWidth = 1.5;
        ctx.stroke();

        // Subtle cross hatch
        ctx.strokeStyle = 'rgba(255, 255, 255, 0.08)';
        ctx.beginPath();
        ctx.moveTo(px + margin + 3, py + margin + 3);
        ctx.lineTo(px + margin + rw - 3, py + margin + rh - 3);
        ctx.stroke();

        ctx.restore();
      });
    }

    // 5. Draw Dynamic Obstacles (Hazard Amber/Orange with pulsing rings)
    if (state?.dynamic_obstacles) {
      Object.entries(state.dynamic_obstacles).forEach(([id, [dx, dy]]) => {
        const { px, py } = toCanvasPos(dx, dy);
        const cx = px + cellSize / 2;
        const cy = py + cellSize / 2;
        const r = cellSize * 0.38;

        ctx.save();
        // Pulsing glow aura
        ctx.shadowColor = 'rgba(245, 158, 11, 0.9)';
        ctx.shadowBlur = 14;

        // Dynamic obstacle outer ring
        ctx.strokeStyle = '#f59e0b';
        ctx.lineWidth = 2.5;
        ctx.beginPath();
        ctx.arc(cx, cy, r, 0, Math.PI * 2);
        ctx.stroke();

        // Radial fill
        const dynGrad = ctx.createRadialGradient(cx, cy, 2, cx, cy, r);
        dynGrad.addColorStop(0, '#fef3c7');
        dynGrad.addColorStop(0.5, '#f59e0b');
        dynGrad.addColorStop(1, '#b45309');
        ctx.fillStyle = dynGrad;
        ctx.beginPath();
        ctx.arc(cx, cy, r - 2, 0, Math.PI * 2);
        ctx.fill();

        // Hazard symbol / icon
        ctx.fillStyle = '#1e1b4b';
        ctx.font = `bold ${Math.max(10, Math.floor(cellSize * 0.35))}px 'JetBrains Mono', monospace`;
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText('!', cx, cy);

        // ID tag badge above obstacle
        ctx.shadowBlur = 0;
        ctx.fillStyle = 'rgba(15, 23, 42, 0.85)';
        ctx.strokeStyle = 'rgba(245, 158, 11, 0.6)';
        ctx.lineWidth = 1;
        const tagText = id.length > 8 ? id.slice(0, 7) + '..' : id;
        ctx.font = `600 ${Math.max(8, Math.floor(cellSize * 0.22))}px sans-serif`;
        const textWidth = ctx.measureText(tagText).width;
        ctx.beginPath();
        ctx.roundRect(cx - textWidth / 2 - 4, py - 12, textWidth + 8, 11, 3);
        ctx.fill();
        ctx.stroke();

        ctx.fillStyle = '#fbbf24';
        ctx.fillText(tagText, cx, py - 7);

        ctx.restore();
      });
    }

    // 6. Draw Start Coordinate (Emerald Node)
    if (state?.start_position) {
      const [sx, sy] = state.start_position;
      const { px, py } = toCanvasPos(sx, sy);
      const cx = px + cellSize / 2;
      const cy = py + cellSize / 2;
      const r = cellSize * 0.38;

      ctx.save();
      ctx.shadowColor = 'rgba(16, 185, 129, 0.8)';
      ctx.shadowBlur = 16;

      ctx.fillStyle = '#10b981';
      ctx.beginPath();
      ctx.arc(cx, cy, r, 0, Math.PI * 2);
      ctx.fill();

      ctx.strokeStyle = '#a7f3d0';
      ctx.lineWidth = 2;
      ctx.stroke();

      ctx.fillStyle = '#ffffff';
      ctx.font = `bold ${Math.max(10, Math.floor(cellSize * 0.4))}px sans-serif`;
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillText('S', cx, cy);
      ctx.restore();
    }

    // 7. Draw Goal Coordinate (Gold / Crimson Target Node)
    if (state?.goal_position) {
      const [gx, gy] = state.goal_position;
      const { px, py } = toCanvasPos(gx, gy);
      const cx = px + cellSize / 2;
      const cy = py + cellSize / 2;
      const r = cellSize * 0.38;

      ctx.save();
      ctx.shadowColor = 'rgba(239, 68, 68, 0.8)';
      ctx.shadowBlur = 16;

      ctx.fillStyle = '#ef4444';
      ctx.beginPath();
      ctx.arc(cx, cy, r, 0, Math.PI * 2);
      ctx.fill();

      ctx.strokeStyle = '#fecaca';
      ctx.lineWidth = 2;
      ctx.stroke();

      ctx.fillStyle = '#ffffff';
      ctx.font = `bold ${Math.max(10, Math.floor(cellSize * 0.4))}px sans-serif`;
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillText('G', cx, cy);
      ctx.restore();
    }

    // 8. Draw Robot Agent (Cyan Rover with Heading Vector & Pulse Glow)
    if (state?.robot_position) {
      const [rx, ry] = state.robot_position;
      const { px, py } = toCanvasPos(rx, ry);
      const cx = px + cellSize / 2;
      const cy = py + cellSize / 2;
      const r = cellSize * 0.42;

      ctx.save();
      // Outer pulse aura
      ctx.shadowColor = '#00f0ff';
      ctx.shadowBlur = 20;

      // Glow halo
      ctx.strokeStyle = 'rgba(0, 240, 255, 0.8)';
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.arc(cx, cy, r + 3, 0, Math.PI * 2);
      ctx.stroke();

      // Robot Body Gradient
      const botGrad = ctx.createRadialGradient(cx, cy, 2, cx, cy, r);
      botGrad.addColorStop(0, '#e0f2fe');
      botGrad.addColorStop(0.4, '#38bdf8');
      botGrad.addColorStop(1, '#0284c7');
      ctx.fillStyle = botGrad;
      ctx.beginPath();
      ctx.arc(cx, cy, r, 0, Math.PI * 2);
      ctx.fill();

      // Drone rotor / cross details
      ctx.strokeStyle = '#ffffff';
      ctx.lineWidth = 1.5;
      ctx.beginPath();
      ctx.moveTo(cx - r * 0.6, cy);
      ctx.lineTo(cx + r * 0.6, cy);
      ctx.moveTo(cx, cy - r * 0.6);
      ctx.lineTo(cx, cy + r * 0.6);
      ctx.stroke();

      // Center navigation core
      ctx.fillStyle = '#ffffff';
      ctx.beginPath();
      ctx.arc(cx, cy, r * 0.25, 0, Math.PI * 2);
      ctx.fill();

      ctx.restore();
    }

    // 9. Draw Hovered Cell Highlighter & Tooltip
    if (hoveredCell) {
      const [hx, hy] = hoveredCell;
      const { px, py } = toCanvasPos(hx, hy);

      ctx.save();
      ctx.strokeStyle = activeTool === 'remove_obstacle' ? '#ef4444' : '#00f0ff';
      ctx.fillStyle = activeTool === 'remove_obstacle' ? 'rgba(239, 68, 68, 0.15)' : 'rgba(0, 240, 255, 0.15)';
      ctx.lineWidth = 2;
      ctx.fillRect(px, py, cellSize, cellSize);
      ctx.strokeRect(px, py, cellSize, cellSize);
      ctx.restore();
    }

    // 10. Draw Axis Coordinate Labels
    ctx.fillStyle = 'rgba(148, 163, 184, 0.6)';
    ctx.font = '10px "JetBrains Mono", monospace';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'top';
    for (let x = 0; x < gridWidth; x += 5) {
      const { px } = toCanvasPos(x, 0);
      ctx.fillText(String(x), px + cellSize / 2, height - padding + 6);
    }

    ctx.textAlign = 'right';
    ctx.textBaseline = 'middle';
    for (let y = 0; y < gridHeight; y += 5) {
      const { py } = toCanvasPos(0, y);
      ctx.fillText(String(y), offsetX - 6, py + cellSize / 2);
    }
  }, [state, gridWidth, gridHeight, hoveredCell, activeTool]);

  // Mouse Handlers
  const handleMouseMove = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const coord = getGridCoordFromEvent(e);
    setHoveredCell(coord);

    if (isMouseDown && coord && (activeTool === 'add_obstacle' || activeTool === 'remove_obstacle')) {
      const key = `${coord[0]},${coord[1]}`;
      if (!draggedCellsRef.current.has(key)) {
        draggedCellsRef.current.add(key);
        onCellDrag([coord]);
      }
    }
  };

  const handleMouseDown = (e: React.MouseEvent<HTMLCanvasElement>) => {
    setIsMouseDown(true);
    draggedCellsRef.current.clear();
    const coord = getGridCoordFromEvent(e);
    if (coord) {
      const key = `${coord[0]},${coord[1]}`;
      draggedCellsRef.current.add(key);
      onCellClick(coord);
    }
  };

  const handleMouseUp = () => {
    setIsMouseDown(false);
    draggedCellsRef.current.clear();
  };

  const handleMouseLeave = () => {
    setHoveredCell(null);
    setIsMouseDown(false);
    draggedCellsRef.current.clear();
  };

  return (
    <div
      ref={containerRef}
      id="simulation-canvas-container"
      style={{
        position: 'relative',
        width: '100%',
        height: '100%',
        minHeight: '520px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: '#07090e',
        borderRadius: '16px',
        overflow: 'hidden',
        border: '1px solid rgba(255, 255, 255, 0.08)',
        boxShadow: '0 8px 32px rgba(0, 0, 0, 0.4)',
      }}
    >
      <canvas
        ref={canvasRef}
        id="navigation-grid-canvas"
        onMouseMove={handleMouseMove}
        onMouseDown={handleMouseDown}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseLeave}
        style={{
          width: '100%',
          height: '100%',
          cursor:
            activeTool === 'add_obstacle'
              ? 'crosshair'
              : activeTool === 'remove_obstacle'
              ? 'not-allowed'
              : activeTool === 'set_start' || activeTool === 'set_goal'
              ? 'pointer'
              : 'default',
        }}
      />

      {/* Coordinate HUD pill */}
      <div
        id="canvas-hud-coordinate"
        style={{
          position: 'absolute',
          bottom: '12px',
          right: '16px',
          background: 'rgba(15, 23, 42, 0.85)',
          backdropFilter: 'blur(8px)',
          border: '1px solid rgba(255, 255, 255, 0.1)',
          padding: '6px 12px',
          borderRadius: '8px',
          fontSize: '11px',
          fontFamily: "'JetBrains Mono', monospace",
          color: '#94a3b8',
          display: 'flex',
          gap: '12px',
          pointerEvents: 'none',
        }}
      >
        <span>
          Cursor: {hoveredCell ? `(${hoveredCell[0]}, ${hoveredCell[1]})` : '--'}
        </span>
        <span>Grid: {gridWidth}x{gridHeight}</span>
      </div>
    </div>
  );
};
