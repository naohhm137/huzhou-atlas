export type Orbit = { yaw: number; pitch: number };
export type DragDelta = { x: number; y: number };
export type OrbitViewport = { width: number; height: number };

export function advanceOrbit(state: Orbit, delta: DragDelta, viewport: OrbitViewport): Orbit {
  const width = Math.max(1, viewport.width);
  const height = Math.max(1, viewport.height);
  return {
    yaw: state.yaw + (delta.x / width) * Math.PI * 1.7,
    pitch: Math.max(-0.75, Math.min(0.75, state.pitch + (delta.y / height) * Math.PI * 0.7)),
  };
}

export function advanceZoom(scale: number, wheelDeltaY: number): number {
  return Math.max(0.45, Math.min(1.8, scale * Math.exp(wheelDeltaY * 0.0013)));
}
