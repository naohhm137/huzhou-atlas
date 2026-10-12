import { describe, expect, it } from 'vitest';
import { renderToStaticMarkup } from 'react-dom/server';
import { App } from '../site';
import { CITY_SCENES } from '../cityScenes';

describe('Huzhou city journey', () => {
  it('continues after the four exhibits through three distinct real places', () => {
    expect(CITY_SCENES.map((scene) => scene.id)).toEqual(['yishang', 'dongwu', 'nanxun-city']);
    expect(new Set(CITY_SCENES.map((scene) => scene.primaryImage)).size).toBe(3);
    expect(CITY_SCENES.every((scene) => scene.sourceUrl.startsWith('https://commons.wikimedia.org/wiki/File:'))).toBe(true);
    expect(CITY_SCENES.find((scene) => scene.id === 'yishang')?.modelParts).toContain('石板街');
    expect(CITY_SCENES.find((scene) => scene.id === 'dongwu')?.modelParts).toContain('斜纹');
    expect(CITY_SCENES.find((scene) => scene.id === 'nanxun-city')?.modelParts).toContain('百间楼');
  });

  it('renders every place as a reachable chapter with a visible image', () => {
    const markup = renderToStaticMarkup(<App />);
    for (const id of ['yishang', 'dongwu', 'nanxun-city']) {
      expect(markup).toContain(`id="${id}"`);
      expect(markup).toContain(`href="#${id}"`);
    }
    expect(markup).toContain('衣裳街');
    expect(markup).toContain('东吴双塔');
    expect(markup).not.toContain('龙之梦');
    expect(markup).toContain('南浔古镇');
  });
});
