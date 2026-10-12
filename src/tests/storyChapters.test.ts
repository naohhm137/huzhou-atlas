import { describe, expect, it } from 'vitest';
import { chapterAtProgress, chapterLocalProgress, EXHIBIT_STORY_CHAPTERS } from '../storyChapters';

describe('exhibit story chapters', () => {
  it('has six strictly increasing reversible chapters', () => {
    expect(EXHIBIT_STORY_CHAPTERS).toHaveLength(6);
    for (let i = 1; i < EXHIBIT_STORY_CHAPTERS.length; i += 1) {
      expect(EXHIBIT_STORY_CHAPTERS[i].start).toBe(EXHIBIT_STORY_CHAPTERS[i - 1].end);
      expect(EXHIBIT_STORY_CHAPTERS[i].end).toBeGreaterThan(EXHIBIT_STORY_CHAPTERS[i].start);
    }
    expect(EXHIBIT_STORY_CHAPTERS[0].start).toBe(0);
    expect(EXHIBIT_STORY_CHAPTERS.at(-1)?.end).toBe(1);
  });

  it('clamps chapter lookup and local progress', () => {
    expect(chapterAtProgress(-1).id).toBe('arrival');
    expect(chapterAtProgress(2).id).toBe('return');
    const structure = chapterAtProgress(0.4);
    expect(structure.id).toBe('structure');
    expect(chapterLocalProgress(structure, structure.start)).toBe(0);
    expect(chapterLocalProgress(structure, structure.end)).toBe(1);
  });
});
