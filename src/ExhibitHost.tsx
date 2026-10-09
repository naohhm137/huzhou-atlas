import { useEffect, useRef, useState } from 'react';
import { ExhibitScene, type ExhibitKind } from './exhibits';
import { posterPathFor } from './modelAsset';
import { SceneFailure, sceneFailureMessage } from './sceneFailure';

export type SceneRegistration = (kind: ExhibitKind, scene: ExhibitScene | null) => void;

export function ExhibitHost({ kind, label, register, expanded = false }: { kind: ExhibitKind; label: string; register: SceneRegistration; expanded?: boolean }) {
  const host = useRef<HTMLDivElement>(null);
  const currentScene = useRef<ExhibitScene | null>(null);
  const expandedRef = useRef(expanded);
  expandedRef.current = expanded;
  const [failure, setFailure] = useState<SceneFailure | null>(null);
  const [attempt, setAttempt] = useState(0);
  useEffect(() => { currentScene.current?.setExpanded(expanded); }, [expanded]);
  useEffect(() => {
    if (!host.current || failure) return;
    let scene: ExhibitScene | null = null;
    let disposed = false;
    const mount = () => {
      if (disposed || scene) return;
      try {
        scene = new ExhibitScene(host.current!, kind, window.matchMedia('(prefers-reduced-motion: reduce)').matches, (error) => {
          if (!disposed) setFailure(error);
        });
        currentScene.current = scene;
        scene.setExpanded(expandedRef.current);
        register(kind, scene);
      } catch (error) {
        console.error(`[Huzhou ${kind}] Scene initialization failed`, error);
        setFailure(error instanceof SceneFailure ? error : new SceneFailure('initialization', 'Scene initialization failed', error));
      }
    };
    // A page can contain eight WebGL stages. Mount only the stage near the
    // viewport so browsers with a finite context budget do not evict older
    // canvases before the visitor reaches them.
    const observer = new IntersectionObserver(([entry]) => {
      if (entry?.isIntersecting) mount();
      else if (scene && !host.current?.closest('.chapter--expanded, .city--expanded')) {
        register(kind, null);
        scene.dispose();
        scene = null;
        currentScene.current = null;
      }
    }, { rootMargin: '0px' });
    observer.observe(host.current);
    return () => {
      disposed = true;
      observer.disconnect();
      if (scene) { register(kind, null); scene.dispose(); }
      currentScene.current = null;
    };
  }, [kind, register, failure, attempt]);
  return <div className={`exhibit-host${failure ? ' is-failed' : ''}`} ref={host} aria-label={`${label} 三维模型`} data-failure={failure?.kind}>
    <img className="exhibit-poster" src={posterPathFor(kind, expanded)} alt={`${label}模型 · ${expanded ? '拆解' : '合拢'}视图`} loading="lazy" />
    {!failure && <p className="exhibit-loading" role="status">正在载入可旋转场景…</p>}
    {failure && <div className="exhibit-status" role="status">
      <p>{sceneFailureMessage(failure.kind)}</p>
      <button type="button" onClick={() => { setFailure(null); setAttempt((value) => value + 1); }}>重试 3D</button>
    </div>}
  </div>;
}
