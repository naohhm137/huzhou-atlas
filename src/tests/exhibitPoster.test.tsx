import { describe, expect, it } from 'vitest';
import { renderToStaticMarkup } from 'react-dom/server';
import { ExhibitHost } from '../ExhibitHost';

describe('model display before WebGL is available', () => {
  it('shows the brush model image while the interactive scene initializes', () => {
    const html = renderToStaticMarkup(<ExhibitHost kind="brush" label="湖笔" expanded={false} register={() => {}} />);
    expect(html).toContain('src="/media/items/brush.webp"');
    expect(html).toContain('alt="湖笔模型 · 全貌视图"');
  });

  it('preserves the close-up model view when the renderer is unavailable', () => {
    const html = renderToStaticMarkup(<ExhibitHost kind="nanxun-city" label="百间楼" expanded register={() => {}} />);
    expect(html).toContain('src="/media/items/nanxun-detail.webp"');
    expect(html).toContain('alt="百间楼模型 · 近看视图"');
  });
});
