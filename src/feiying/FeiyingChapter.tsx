import { useCallback, useEffect, useRef, useState } from 'react';
import { FeiyingScene, type LabelId } from './scene';
import { FEIYING_LABELS, FEIYING_SCREENS } from './screens';
import { layerWeight, MIST, PINES, progressForScreen, screenOpacity, screenPosition } from './timeline';
import './feiying.css';

export type ProgressController = { setProgress: (value: number) => void; setExpanded: (value: boolean) => void; resetRotation: () => void };

const BASE = import.meta.env.BASE_URL;
const media = (name: string) => `${BASE}media/feiying/${name}`;
const LABEL_SETS: Record<number, LabelId[]> = { 2: ['spire', 'outer', 'inner', 'base'], 3: ['dou', 'gong', 'ang'] };

export function FeiyingChapter({ register }: { register: (kind: 'tower', controller: ProgressController | null) => void }) {
  const section = useRef<HTMLElement>(null);
  const stage = useRef<HTMLDivElement>(null);
  const scene = useRef<FeiyingScene | null>(null);
  const labelRefs = useRef<Partial<Record<LabelId, HTMLSpanElement | null>>>({});
  const progress = useRef(0);
  const [status, setStatus] = useState<'idle' | 'loading' | 'ready' | 'error'>('idle');
  const [loaded, setLoaded] = useState(0);
  const [active, setActive] = useState(0);
  const [free, setFree] = useState(false);
  const [manual, setManual] = useState({ explode: 0, cut: 0 });
  const [attempt, setAttempt] = useState(0);
  const reduced = typeof window !== 'undefined' && window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  // The page-level scroll loop drives this chapter through the same controller contract as the
  // other exhibits; every visual here is derived from that one progress value.
  const apply = useCallback((value: number) => {
    progress.current = value;
    const el = section.current;
    if (!el) return;
    const s = screenPosition(value);
    el.style.setProperty('--p', value.toFixed(4));
    el.style.setProperty('--s', s.toFixed(4));
    el.style.setProperty('--pines', layerWeight(PINES, s).toFixed(3));
    el.style.setProperty('--mist', layerWeight(MIST, s).toFixed(3));
    el.querySelectorAll<HTMLElement>('[data-screen]').forEach((node) => {
      const i = Number(node.dataset.screen);
      const o = screenOpacity(i, s);
      node.style.opacity = o.toFixed(3);
      node.style.setProperty('--offset', ((s - i) * -42).toFixed(1));
      node.style.visibility = o > 0.01 ? 'visible' : 'hidden';
    });
    const nearest = Math.round(s);
    setActive((prev) => (prev === nearest ? prev : nearest));
    scene.current?.setProgress(value);
  }, []);

  useEffect(() => {
    const controller: ProgressController = { setProgress: apply, setExpanded: () => {}, resetRotation: () => {} };
    register('tower', controller);
    apply(0);
    return () => register('tower', null);
  }, [register, apply]);

  // Mount WebGL when the chapter approaches, keep it while the page lives, pause off-screen.
  useEffect(() => {
    const host = stage.current;
    if (!host || status === 'error') return;
    let instance: FeiyingScene | null = null;
    const near = new IntersectionObserver(([entry]) => {
      if (!entry?.isIntersecting || instance) return;
      setStatus('loading');
      try {
        instance = new FeiyingScene(host, {
          reducedMotion: reduced,
          onLoadProgress: (f) => setLoaded(Math.round(f * 100)),
          onReady: () => { setStatus('ready'); instance?.setProgress(progress.current); },
          onError: (error) => { console.error('[Huzhou feiying] model failed to load', error); setStatus('error'); },
          onLabels: (labels) => {
            for (const [id, node] of Object.entries(labelRefs.current)) {
              const at = labels[id as LabelId];
              if (!node) continue;
              node.style.opacity = at ? '' : '0';
              if (at) node.style.transform = `translate3d(${at[0].toFixed(1)}px, ${at[1].toFixed(1)}px, 0)`;
            }
          },
        });
        scene.current = instance;
      } catch (error) {
        console.error('[Huzhou feiying] WebGL unavailable', error);
        setStatus('error');
      }
    }, { rootMargin: '150% 0px' });
    const seen = new IntersectionObserver(([entry]) => instance?.setVisible(Boolean(entry?.isIntersecting)));
    near.observe(host);
    seen.observe(section.current!);
    return () => { near.disconnect(); seen.disconnect(); instance?.dispose(); scene.current = null; };
  }, [attempt, reduced]);

  // Free view takes the canvas and pauses page scroll; Escape or the close button returns.
  useEffect(() => {
    scene.current?.setFreeView(free);
    if (!free) return;
    const previous = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    const onKey = (event: KeyboardEvent) => { if (event.key === 'Escape') setFree(false); };
    window.addEventListener('keydown', onKey);
    return () => { document.body.style.overflow = previous; window.removeEventListener('keydown', onKey); };
  }, [free]);
  useEffect(() => { scene.current?.setManual(manual.explode, manual.cut); }, [manual]);

  const jump = (index: number) => {
    const el = section.current;
    if (!el) return;
    const top = el.getBoundingClientRect().top + window.scrollY;
    const travel = el.offsetHeight - window.innerHeight;
    window.scrollTo({ top: top + travel * progressForScreen(index), behavior: reduced ? 'auto' : 'smooth' });
  };

  return <section id="tower" ref={section} className={`feiying feiying--${status}${free ? ' feiying--free' : ''}`} data-story-section aria-label="飞英塔">
    <div className="feiying__sticky">
      <div className="feiying__sky" style={{ backgroundImage: `url(${media('sky.webp')})` }} aria-hidden="true" />
      <div className="feiying__glow" aria-hidden="true" />
      <div className="feiying__stage" ref={stage}>
        {status !== 'ready' && <img className="feiying__poster" src={media(`poster-0${Math.min(6, active + 1)}.webp`)} alt="" />}
      </div>
      <div className="feiying__mist" style={{ backgroundImage: `url(${media('mist.webp')})` }} aria-hidden="true" />
      <div className="feiying__pines" style={{ backgroundImage: `url(${media('pines.webp')})` }} aria-hidden="true" />
      <div className="feiying__fade" aria-hidden="true" />
      <div className="feiying__grain" aria-hidden="true" />

      <header className="feiying__bar">
        <p className="feiying__mark"><span>飞英塔</span><small>FEIYING PAGODA</small></p>
        <nav className="feiying__nav" aria-label="飞英塔章节">
          {FEIYING_SCREENS.map((screen, i) => <button key={screen.id} type="button" aria-current={active === i ? 'step' : undefined} onClick={() => jump(i)}>
            <span>{String(i + 1).padStart(2, '0')}</span> {screen.nav}
          </button>)}
        </nav>
        <button type="button" className="feiying__free" onClick={() => setFree(true)} disabled={status !== 'ready'}>自由观塔 <span aria-hidden="true">↗</span></button>
      </header>

      <div className="feiying__labels" aria-hidden="true">
        {Object.entries(LABEL_SETS).map(([screen, ids]) => <div key={screen} data-screen={screen} className="feiying__labelset">
          {ids.map((id) => <span key={id} className={`feiying__label feiying__label--${id}`} ref={(node) => { labelRefs.current[id] = node; }}>
            <i /><b><span className="feiying__label-full">{FEIYING_LABELS[id][0]}</span><span className="feiying__label-short">{FEIYING_LABELS[id][1]}</span></b>
          </span>)}
        </div>)}
      </div>

      {FEIYING_SCREENS.map((screen, i) => <article key={screen.id} data-screen={i} className={`feiying__copy feiying__copy--${screen.layout}`} aria-hidden={active !== i}>
        {screen.layout === 'cover' ? <>
          <h2 className="feiying__split"><span>{screen.title[0]}</span><span>{screen.title[1]}</span></h2>
          <p className="feiying__split-meta"><span>{screen.eyebrow}</span><span>{screen.body[0]}</span></p>
          <p className="feiying__verse">一塔之内<br />石塔静立<br />千年相望</p>
          <p className="feiying__cue">向下，进入塔中之塔 <span aria-hidden="true">↓</span></p>
        </> : <>
          <p className="feiying__eyebrow">{screen.eyebrow}</p>
          <h2>{screen.title.map((line) => <span key={line}>{line}</span>)}</h2>
          <hr />
          <p className="feiying__body">{screen.body.map((line) => <span key={line}>{line}</span>)}</p>
          {screen.points && <ul className={`feiying__points feiying__points--${screen.id}`}>{screen.points.map((point) => <li key={point}>{point}</li>)}</ul>}
          {screen.id === 'within' && <small className="feiying__note">解释性拆解示意，非真实可拆构造</small>}
          {screen.id === 'guard' && <div className="feiying__actions">
            <button type="button" onClick={() => jump(0)}>返回全貌 <span aria-hidden="true">↗</span></button>
            <a href="#sources">查看资料 <span aria-hidden="true">↗</span></a>
          </div>}
        </>}
        <span className="feiying__count" aria-hidden="true">{String(i + 1).padStart(2, '0')} / 06</span>
      </article>)}

      {status === 'loading' && <p className="feiying__loading" role="status">正在载入飞英塔模型 {loaded}%</p>}
      {status === 'error' && <div className="feiying__error" role="status">
        <p>三维模型暂未载入，当前显示渲染图。</p>
        <button type="button" onClick={() => { setStatus('idle'); setAttempt((n) => n + 1); }}>重试 3D</button>
      </div>}

      {free && <div className="feiying__panel" role="dialog" aria-label="自由观塔">
        <p>拖动旋转 · 滚轮或双指缩放</p>
        <label>拆层 <input type="range" min={0} max={1} step={0.01} value={manual.explode} onChange={(e) => setManual((m) => ({ ...m, explode: Number(e.target.value) }))} /></label>
        <label>剖开外塔 <input type="range" min={0} max={1} step={0.01} value={manual.cut} onChange={(e) => setManual((m) => ({ ...m, cut: Number(e.target.value) }))} /></label>
        <button type="button" onClick={() => setFree(false)} autoFocus>返回滚动 <span aria-hidden="true">×</span></button>
      </div>}

      <footer className="feiying__foot" data-screen={5}>
        <span>层见湖州 · 飞英塔章节</span><span>模型为解释性数字示意 · 资料来源见索引</span>
      </footer>
    </div>
  </section>;
}
