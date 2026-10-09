import { describe, expect, it } from 'vitest';
import { renderToStaticMarkup } from 'react-dom/server';
import { Chapter, chapters } from '../site';

describe('immersive exploded exhibit', () => {
  it('opens the stage to the viewport and gives the visitor a visible close control', () => {
    const markup = renderToStaticMarkup(<Chapter data={chapters[2]} register={() => {}} onToggle={() => {}} expanded />);
    expect(markup).toContain('chapter--expanded');
    expect(markup).toContain('aria-label="合拢茶展品"');
    expect(markup).toContain('茶盏 · 茶汤 · 芽叶');
  });
});
