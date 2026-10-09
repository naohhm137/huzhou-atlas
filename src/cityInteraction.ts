const clamp = (value: number) => Math.min(100, Math.max(0, value));

export function adjustCompare(value: number, key: string): number {
  if (key === 'ArrowLeft') return clamp(value - 5);
  if (key === 'ArrowRight') return clamp(value + 5);
  if (key === 'Home') return 0;
  if (key === 'End') return 100;
  return value;
}
