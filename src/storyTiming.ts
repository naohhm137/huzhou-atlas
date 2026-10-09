export const MEDIA_RANGES = {
  opening: [0.01, 2.04],
  brush: [2.04, 2.04],
  'thread-bridge': [2.04, 5.2],
  silk: [5.2, 5.2],
  'tea-bridge': [5.2, 7.75],
  tea: [7.75, 7.75],
  tower: [7.75, 7.75],
  'city-gate': [7.75, 7.75],
  yishang: [7.75, 7.75],
  dongwu: [7.75, 7.75],
  longemont: [7.75, 7.75],
  'nanxun-city': [7.75, 7.75],
  ending: [7.75, 9.9],
} as const satisfies Record<string, readonly [number, number]>;

export type StorySection = keyof typeof MEDIA_RANGES;

export function chapterMediaTime(section: StorySection, progress: number) {
  const [start, end] = MEDIA_RANGES[section];
  const t = Math.max(0, Math.min(1, progress));
  return start + (end - start) * t;
}
