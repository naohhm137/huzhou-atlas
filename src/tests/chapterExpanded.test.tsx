import { describe, expect, it } from 'vitest';
import { renderToStaticMarkup } from 'react-dom/server';
import { Chapter, chapters } from '../site';

describe('immersive close-up exhibit', () => {
  it('opens the stage to the viewport and gives the visitor a visible close control', () => {
    const markup = renderToStaticMarkup(<Chapter data={chapters[2]} register={() => {}} onToggle={() => {}} expanded />);
    expect(markup).toContain('chapter--expanded');
    expect(markup).toContain('aria-label="返回，结束近看茶"');
    expect(markup).toContain('青瓷茶盏 · 荷叶盏托 · 茶汤与紫笋芽叶');
  });
});
