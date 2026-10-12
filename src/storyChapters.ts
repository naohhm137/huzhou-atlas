export type StoryTextPosition = 'left' | 'right' | 'center';

export type StoryChapter = {
  id: string;
  start: number;
  end: number;
  title: string;
  focusPart?: string;
  camera: { distance: [number, number]; elevation: [number, number] };
  rotation: [number, number];
  explode: [number, number];
  textPosition: StoryTextPosition;
};

export const EXHIBIT_STORY_CHAPTERS: readonly StoryChapter[] = [
  { id: 'arrival', start: 0, end: 0.16, title: '初见', camera: { distance: [1, 0.98], elevation: [0, 0.02] }, rotation: [0, 0.08], explode: [0, 0], textPosition: 'left' },
  { id: 'whole', start: 0.16, end: 0.32, title: '整体', camera: { distance: [0.98, 0.94], elevation: [0.02, 0.04] }, rotation: [0.08, 0.18], explode: [0, 0.08], textPosition: 'right' },
  { id: 'structure', start: 0.32, end: 0.54, title: '结构', camera: { distance: [0.94, 0.88], elevation: [0.04, 0.02] }, rotation: [0.18, 0.32], explode: [0.08, 0.72], textPosition: 'left' },
  { id: 'detail', start: 0.54, end: 0.70, title: '细节', focusPart: 'detail', camera: { distance: [0.88, 0.64], elevation: [0.02, 0.08] }, rotation: [0.32, 0.46], explode: [0.72, 0.56], textPosition: 'right' },
  { id: 'meaning', start: 0.70, end: 0.86, title: '价值', camera: { distance: [0.64, 0.82], elevation: [0.08, 0.03] }, rotation: [0.46, 0.58], explode: [0.56, 0.24], textPosition: 'center' },
  { id: 'return', start: 0.86, end: 1, title: '收尾', camera: { distance: [0.82, 1], elevation: [0.03, 0] }, rotation: [0.58, 0.66], explode: [0.24, 0], textPosition: 'left' },
] as const;

export function chapterAtProgress(progress: number): StoryChapter {
  const value = Math.max(0, Math.min(1, progress));
  return EXHIBIT_STORY_CHAPTERS.find((chapter, index) => value < chapter.end || index === EXHIBIT_STORY_CHAPTERS.length - 1)!;
}

export function chapterLocalProgress(chapter: StoryChapter, progress: number): number {
  return Math.max(0, Math.min(1, (progress - chapter.start) / Math.max(0.0001, chapter.end - chapter.start)));
}
