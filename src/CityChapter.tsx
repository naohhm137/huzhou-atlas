import { useState, type CSSProperties, type KeyboardEvent } from 'react';
import { adjustCompare } from './cityInteraction';
import type { CitySceneData } from './cityScenes';
import { ExhibitHost, type SceneRegistration } from './ExhibitHost';
import type { ExhibitKind } from './exhibits';

const labelFor = (scene: CitySceneData, second: boolean) => {
  if (scene.id === 'yishang') return second ? '看青莲桥' : '看衣裳街';
  if (scene.id === 'dongwu') return second ? '从水岸远望' : '近看双塔';
  return second ? '进入舞台' : '回到入口';
};

export function CityChapter({ scene, register, expanded, onToggle }: {
  scene: CitySceneData; register: SceneRegistration; expanded: boolean; onToggle: (kind: ExhibitKind) => void;
}) {
  const [second, setSecond] = useState(false);
  const [compare, setCompare] = useState(50);
  const [photoCompare, setPhotoCompare] = useState(false);
  const comparing = scene.motion === 'water' && photoCompare && !expanded;
  const currentSource = second ? scene.secondarySourceUrl : scene.sourceUrl;
  const currentCredit = second ? scene.secondarySourceLabel : scene.sourceLabel;
  const currentCaption = second ? scene.secondaryCaption : scene.imageCaption;
  const compareStyle = { '--compare': `${compare}%` } as CSSProperties;

  const onCompareKey = (event: KeyboardEvent<HTMLInputElement>) => {
    const next = adjustCompare(compare, event.key);
    if (next !== compare) {
      event.preventDefault();
      setCompare(next);
    }
  };

  return <section id={scene.id} className={`city city--${scene.motion}${expanded ? ' city--expanded' : ''}${comparing ? ' city--photo-compare' : ''}`} data-story-section>
    <div className="city__viewport">
      <div className="city__media" style={comparing ? compareStyle : undefined}>
        <img className={`city__image city__image--primary${!second || comparing ? ' is-current' : ''}`} src={scene.primaryImage} alt={scene.primaryAlt} loading="lazy" aria-hidden={!comparing && second} />
        <img className={`city__image city__image--secondary${second || comparing ? ' is-current' : ''}`} src={scene.secondaryImage} alt={scene.secondaryAlt} loading="lazy" aria-hidden={!comparing && !second} />
        <div className="city__image-wash" aria-hidden="true" />
        {scene.motion === 'towers' && <div className="city__tower-lines" aria-hidden="true"><span /><span /><span /></div>}
        {scene.motion === 'theatre' && <div className="city__theatre-ring" aria-hidden="true" />}
        {scene.motion === 'street' && <div className="city__street-lines" aria-hidden="true"><span /><span /></div>}
        {comparing && <div className="city__compare" aria-label="南浔两处河巷的照片对照">
          <div className="city__compare-line" aria-hidden="true"><span>↔</span></div>
          <input type="range" min="0" max="100" step="1" value={compare} onChange={(event) => setCompare(Number(event.target.value))} onKeyDown={onCompareKey} aria-label="拖动对照南浔两处河巷" aria-valuetext={`左侧百间楼 ${compare}%，右侧另一处河巷 ${100 - compare}%`} />
          <span className="city__compare-name city__compare-name--left">百间楼</span>
          <span className="city__compare-name city__compare-name--right">南浔别处</span>
        </div>}
        <div className="city__media-credit">
          <span>{comparing ? '南浔两处河巷 · 拖动对照' : currentCaption}</span>
          <a href={currentSource} target="_blank" rel="noreferrer">{currentCredit} ↗</a>
        </div>
      </div>
      <div className="city__model-stage">
        <ExhibitHost kind={scene.id} label={scene.place.split(' · ')[0]} register={register} expanded={expanded} />
        <span className="city__model-label">Blender 实景参照模型 · 非测绘复原 · 拖动旋转</span>
        {expanded && <>
          <button type="button" className="stage-close" onClick={() => onToggle(scene.id)} aria-label={`合拢${scene.place.split(' · ')[0]}场景`}>合拢场景 <span aria-hidden="true">×</span></button>
          <div className="stage-anatomy"><span>城市结构剖览</span><h3>{scene.place.split(' · ')[0]}</h3><p>{scene.modelParts}</p><small>拖动旋转 · 滚轮近看 · Esc 合拢</small></div>
        </>}
      </div>
      <div className="city__copy">
        <p className="city__place">{scene.place}</p>
        <h2>{scene.title.split('\n').map((line, index) => <span key={line}>{index > 0 && <br />}{line}</span>)}</h2>
        <p className="city__body">{scene.body}</p>
        <div className="city__model-actions">
          <button type="button" className="text-button" aria-pressed={expanded} onClick={() => onToggle(scene.id)}>{expanded ? '合拢场景' : '拆开场景'} <span aria-hidden="true">↗</span></button>
          <span className="drag-hint">拖动模型可旋转</span>
        </div>
        {scene.motion !== 'water' && <div className="city__views" role="group" aria-label={`${scene.place}实景视角`}>
          <button type="button" className={!second ? 'is-selected' : ''} aria-pressed={!second} onClick={() => setSecond(false)}>{labelFor(scene, false)}</button>
          <button type="button" className={second ? 'is-selected' : ''} aria-pressed={second} onClick={() => setSecond(true)}>{labelFor(scene, true)}</button>
        </div>}
        {scene.motion === 'water' && <div className="city__views"><button type="button" className={comparing ? 'is-selected' : ''} aria-pressed={comparing} onClick={() => setPhotoCompare(!photoCompare)}>{comparing ? '返回三维河巷' : '对照两处实景'}</button></div>}
        {comparing && <p className="city__hint">拖动画面中的分界，或用方向键慢慢看。</p>}
      </div>
      <div className="city__index" aria-hidden="true">HUZHOU / {scene.id === 'nanxun-city' ? 'NANXUN' : scene.id.toUpperCase()}</div>
    </div>
  </section>;
}
