import { describe, expect, it } from 'vitest';
import { renderToStaticMarkup } from 'react-dom/server';
import { ExhibitHost } from '../ExhibitHost';

describe('model display before WebGL is available', () => {
  it('shows the brush model image while the interactive scene initializes', () => {
    const html = renderToStaticMarkup(<ExhibitHost kind="brush" label="湖笔" expanded={false} register={() => {}} />);
    expect(html).toContain('src="/media/models/brush.webp"');
    expect(html).toContain('alt="湖笔模型 · 合拢视图"');
  });

  it('preserves the expanded model view when the renderer is unavailable', () => {
    const html = renderToStaticMarkup(<ExhibitHost kind="nanxun-city" label="百间楼" expanded register={() => {}} />);
    expect(html).toContain('src="/media/models/city-nanxun-expanded.webp"');
    expect(html).toContain('alt="百间楼模型 · 拆解视图"');
  });
});
