import { useCallback, useEffect, useRef, useState } from 'react';
import gsap from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';
import { ExhibitScene, type ExhibitKind } from './exhibits';
import { chapterMediaTime, type StorySection } from './storyTiming';
import { CityChapter } from './CityChapter';
import { CITY_SCENES } from './cityScenes';
import { ExhibitHost, type SceneRegistration } from './ExhibitHost';

gsap.registerPlugin(ScrollTrigger);

type ExhibitController = { setProgress: (value: number) => void; setExpanded: (value: boolean) => void; resetRotation: () => void };
type ControllerMap = Map<ExhibitKind, ExhibitController>;

const clamp = (value: number, min = 0, max = 1) => Math.min(max, Math.max(min, value));
export const chapters: { id: ExhibitKind; word: string; title: string; subtitle: string; body: string; note: string; fact: string; photo: string; photoNote: string; parts: string }[] = [
  {
    id: 'brush', word: '笔', title: '一支笔，写下江南。', subtitle: '湖笔 · 善琏',
    body: '善琏湖笔以细竹为管，以毫成锋。沿着竹管、捆扎的毫根与一束束笔毫，读出一支笔的力道。',
    note: '清代吴兴贡笔形制参考 · 笔锋是一整束', fact: '“尖、齐、圆、健”是湖笔品评的四字要诀。',
    photo: 'media/chapter-brush.jpg', photoNote: '毛笔锋毫的材质参考影像', parts: '竹管 · 毫根 · 一整束笔锋',
  },
  {
    id: 'silk', word: '丝', title: '丝线交错，织出江南。', subtitle: '双林 · 绫绢',
    body: '这是一架依双林绫绢织造原理设计的水平织机示意。经丝逐根绷紧，梭子送入纬丝，筘把纹理推向织物。',
    note: '96 根经丝逐根建模 · 织机结构为工艺示意', fact: '送经、开口、投梭、打纬、卷布，织造在反复的秩序里完成。',
    photo: 'media/chapter-silk.jpg', photoNote: '传统织机的经丝场景参考影像', parts: '机架 · 经轴 · 综筘 · 经丝 · 纬丝',
  },
  {
    id: 'tea', word: '叶', title: '一片叶，留住山水。', subtitle: '茶 · 顾渚',
    body: '当代顾渚紫笋在茶汤中舒展。盏身、托盘、澄黄茶汤与芽叶各成一层，托起这一刻的山水。',
    note: '唐越窑带托盏形制参考 · 冲泡情境为当代示意', fact: '唐代煎茶与今天的整叶冲泡不同；这里展示的是跨时代的器与茶。',
    photo: 'media/chapter-tea.jpg', photoNote: '长兴茶园 · 山间茶田', parts: '茶盏 · 茶汤 · 芽叶',
  },
  {
    id: 'tower', word: '塔', title: '一座塔，藏着另一座塔。', subtitle: '飞英塔 · 吴兴',
    body: '飞英塔的奇妙，在于七层八角砖木外塔包裹着五层石塔。拆开飞檐与斗拱，才能看见塔中塔。',
    note: '外塔七层 · 内塔五层 · 正面开口为观察剖面', fact: '模型是据可查结构制作的数字示意，并非文物测绘复原。',
    photo: 'media/chapter-tower.jpg', photoNote: '飞英塔内部 · 石塔与外塔木构', parts: '外塔七层 · 斗拱飞檐 · 内塔五层',
  },
];

function Film({ videoRef, status }: { videoRef: React.RefObject<HTMLVideoElement | null>; status: 'loading' | 'ready' | 'error' }) {
  return <div className="film-layer" aria-hidden="true">
    <div className="film-poster" style={{ backgroundImage: 'url(media/film-first-frame.jpg)' }} />
    <video ref={videoRef} className={`film-video film-video--${status}`} muted playsInline preload="auto" poster="media/film-first-frame.jpg">
      <source src="media/huzhou-film.mp4" type="video/mp4" />
    </video>
    <div className="film-shade" />
  </div>;
}

export function Chapter({ data, register, onToggle, expanded }: {
  data: typeof chapters[number]; register: SceneRegistration;
  onToggle: (kind: ExhibitKind) => void; expanded: boolean;
}) {
  return <section id={data.id} className={`chapter chapter--${data.id}${expanded ? ' chapter--expanded' : ''}`} data-story-section>
    <div className="chapter__viewport">
      <div className="chapter__texture" />
      <div className="chapter__copy">
        <p className="chapter__small">{data.subtitle}</p>
        <span className="chapter__word" aria-hidden="true">{data.word}</span>
        <h2>{data.title}</h2>
        <p className="chapter__body">{data.body}</p>
        <p className="chapter__fact">{data.fact}</p>
        <div className="chapter__actions">
          <button type="button" className="text-button" aria-pressed={expanded} onClick={() => onToggle(data.id)}>
            {expanded ? '合拢展品' : '拆开展品'} <span aria-hidden="true">↗</span>
          </button>
          <span className="drag-hint">拖动模型可旋转</span>
        </div>
      </div>
      <div className="chapter__stage">
        <figure className="chapter__photo"><img src={data.photo} alt="" loading="lazy" /><figcaption>{data.photoNote}</figcaption></figure>
        <div className="stage-orbit stage-orbit--one" /><div className="stage-orbit stage-orbit--two" />
        <ExhibitHost kind={data.id} label={data.subtitle.split(' · ')[0]} register={register} expanded={expanded} />
        <span className="stage-caption">{data.note}</span>
        {expanded && <>
          <button type="button" className="stage-close" aria-label={`合拢${data.subtitle.split(' · ')[0]}展品`} onClick={() => onToggle(data.id)}>合拢展品 <span aria-hidden="true">×</span></button>
          <div className="stage-anatomy"><span>数字工艺剖览</span><h3>{data.subtitle}</h3><p>{data.parts}</p><small>拖动旋转 · 滚轮近看</small></div>
        </>}
      </div>
    </div>
  </section>;
}

export function App() {
  const videoRef = useRef<HTMLVideoElement>(null);
  const controllers = useRef<ControllerMap>(new Map());
  const [active, setActive] = useState('opening');
  const [videoStatus, setVideoStatus] = useState<'loading' | 'ready' | 'error'>('loading');
  const [expanded, setExpanded] = useState<Partial<Record<ExhibitKind, boolean>>>({});
  const register = useCallback((kind: ExhibitKind, scene: ExhibitScene | null) => {
    if (scene) controllers.current.set(kind, scene);
    else controllers.current.delete(kind);
  }, []);
  const onToggle = (kind: ExhibitKind) => {
    const next = !expanded[kind];
    for (const [id, controller] of controllers.current) controller.setExpanded(id === kind && next);
    setExpanded({ [kind]: next });
  };

  useEffect(() => {
    if (!Object.values(expanded).some(Boolean)) return;
    const previous = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    const onEscape = (event: KeyboardEvent) => {
      if (event.key !== 'Escape') return;
      for (const controller of controllers.current.values()) controller.setExpanded(false);
      setExpanded({});
    };
    window.addEventListener('keydown', onEscape);
    return () => { document.body.style.overflow = previous; window.removeEventListener('keydown', onEscape); };
  }, [expanded]);

  useEffect(() => {
    const video = videoRef.current;
    if (!video) return;
    let latest = 0.01;
    let settle: ReturnType<typeof setTimeout> | undefined;
    const seek = () => {
      if (video.readyState < 1 || video.seeking || !Number.isFinite(video.duration)) return;
      const wanted = clamp(latest, 0.01, Math.max(0.01, video.duration - 0.05));
      if (Math.abs(video.currentTime - wanted) > 1 / 24) video.currentTime = wanted;
    };
    const setTime = (value: number) => {
      latest = value;
      seek();
      clearTimeout(settle);
      settle = setTimeout(seek, 120);
    };
    const onReady = () => { setVideoStatus('ready'); seek(); };
    const onError = () => setVideoStatus('error');
    video.addEventListener('loadeddata', onReady);
    video.addEventListener('seeked', seek);
    video.addEventListener('error', onError);
    if (video.readyState >= 2) onReady();
    else if (video.error) onError();

    const ids: StorySection[] = ['opening', 'brush', 'thread-bridge', 'silk', 'tea-bridge', 'tea', 'tower', 'city-gate', 'yishang', 'dongwu', 'longemont', 'nanxun-city', 'ending'];
    let positions: { id: StorySection; element: HTMLElement; top: number; travel: number }[] = [];
    const measure = () => {
      positions = ids.map((id) => {
        const el = document.getElementById(id)!;
        const top = el.getBoundingClientRect().top + window.scrollY;
        return { id, element: el, top, travel: Math.max(1, el.offsetHeight - window.innerHeight) };
      });
    };
    const update = (y: number) => {
      if (!positions.length) measure();
      const section = [...positions].reverse().find((item) => y >= item.top - 1) ?? positions[0];
      const local = clamp((y - section.top) / section.travel);
      setTime(chapterMediaTime(section.id, local));
      document.documentElement.style.setProperty('--story-progress', String(clamp(y / Math.max(1, ScrollTrigger.maxScroll(window)))));
      document.documentElement.dataset.activeChapter = section.id;
      setActive((previous) => previous === section.id ? previous : section.id);
      for (const item of positions) {
        if (item.id === 'brush' || item.id === 'silk' || item.id === 'tea' || item.id === 'tower'
          || item.id === 'yishang' || item.id === 'dongwu' || item.id === 'longemont' || item.id === 'nanxun-city') {
          controllers.current.get(item.id)?.setProgress(clamp((y - item.top) / item.travel));
        }
        if (item.id === 'yishang' || item.id === 'dongwu' || item.id === 'longemont' || item.id === 'nanxun-city') {
          const progress = clamp((y - item.top) / item.travel);
          item.element.style.setProperty('--place-progress', String(progress));
          item.element.style.setProperty('--scene-scale', String(1.04 + progress * 0.08));
          item.element.style.setProperty('--scene-shift', `${Math.round((progress - 0.5) * 32)}px`);
          item.element.style.setProperty('--tower-reveal', `${Math.round((1 - progress) * 8)}%`);
          item.element.style.setProperty('--iris', `${Math.round(76 + progress * 70)}%`);
        }
      }
    };
    measure();
    const scroll = ScrollTrigger.create({
      id: 'huzhou-story',
      trigger: document.documentElement,
      start: 0,
      end: () => ScrollTrigger.maxScroll(window),
      onUpdate: (self) => update(self.scroll()),
      onRefresh: () => { measure(); update(window.scrollY); },
    });
    update(window.scrollY);
    document.fonts.ready.then(() => ScrollTrigger.refresh());
    const resize = () => { measure(); update(window.scrollY); ScrollTrigger.refresh(); };
    window.addEventListener('resize', resize);
    return () => {
      scroll.kill();
      clearTimeout(settle);
      window.removeEventListener('resize', resize);
      video.removeEventListener('loadeddata', onReady);
      video.removeEventListener('seeked', seek);
      video.removeEventListener('error', onError);
    };
  }, []);

  return <>
    <Film videoRef={videoRef} status={videoStatus} />
    <header className="masthead">
      <a href="#opening" className="brand" aria-label="回到开篇"><span className="brand__han">层见湖州</span><span className="brand__latin">HUZHOU / AN ATLAS</span></a>
      <nav className="nav nav--desktop" aria-label="章节导航">
        <a className={active === 'brush' ? 'is-active' : ''} href="#brush">湖笔</a>
        <a className={active === 'silk' ? 'is-active' : ''} href="#silk">蚕丝</a>
        <a className={active === 'tea' ? 'is-active' : ''} href="#tea">茶</a>
        <a className={active === 'tower' ? 'is-active' : ''} href="#tower">飞英塔</a>
        <details className="nav__places">
          <summary className={CITY_SCENES.some((scene) => scene.id === active) ? 'is-active' : ''}>城中漫游 <span aria-hidden="true">⌄</span></summary>
          <div className="nav__places-list">{CITY_SCENES.map((scene) => <a key={scene.id} className={active === scene.id ? 'is-active' : ''} href={`#${scene.id}`} onClick={(event) => event.currentTarget.closest('details')?.removeAttribute('open')}>{scene.place.split(' · ')[0]}</a>)}</div>
        </details>
      </nav>
      <nav className="nav nav--mobile" aria-label="移动端章节导航"><details><summary>目录 <span aria-hidden="true">⌄</span></summary><div className="nav__mobile-list">
        <a href="#brush" onClick={(event) => event.currentTarget.closest('details')?.removeAttribute('open')}>湖笔</a>
        <a href="#silk" onClick={(event) => event.currentTarget.closest('details')?.removeAttribute('open')}>蚕丝</a>
        <a href="#tea" onClick={(event) => event.currentTarget.closest('details')?.removeAttribute('open')}>茶</a>
        <a href="#tower" onClick={(event) => event.currentTarget.closest('details')?.removeAttribute('open')}>飞英塔</a>
        {CITY_SCENES.map((scene) => <a key={scene.id} href={`#${scene.id}`} onClick={(event) => event.currentTarget.closest('details')?.removeAttribute('open')}>{scene.place.split(' · ')[0]}</a>)}
      </div></details></nav>
      <a className="masthead__about" href="#sources">资料与鸣谢 <span aria-hidden="true">↗</span></a>
    </header>

    <main id="story">
      <section id="opening" className="film-section opening" data-story-section>
        <div className="film-section__viewport opening__viewport">
          <div className="opening__topline"><span>浙江 · 湖州</span><span>太湖南岸的文化漫游</span></div>
          <div className="opening__title-wrap">
            <p className="opening__preface">一座城的层层来处</p>
            <h1><span>层见</span><span>湖州</span></h1>
            <p className="opening__intro">从笔尖、丝线与茶盏，走到塔中之塔。<br />拆开湖州，看见它的手艺与岁月。</p>
          </div>
          <div className="opening__bottom"><span>南浔的水，故事的起点</span><a href="#brush">开始漫游 <span aria-hidden="true">↗</span></a></div>
        </div>
      </section>

      <Chapter data={chapters[0]} register={register} onToggle={onToggle} expanded={Boolean(expanded.brush)} />

      <section id="thread-bridge" className="film-section bridge bridge--thread" data-story-section>
        <div className="film-section__viewport bridge__viewport">
          <p>笔锋落下，线便有了方向。</p>
          <h2>一条墨线，<br />慢慢变成一根丝。</h2>
          <span className="bridge__small">继续向下，跟随它穿过水乡。</span>
        </div>
      </section>

      <Chapter data={chapters[1]} register={register} onToggle={onToggle} expanded={Boolean(expanded.silk)} />

      <section id="tea-bridge" className="film-section bridge bridge--tea" data-story-section>
        <div className="film-section__viewport bridge__viewport">
          <p>丝线在光里展开。</p>
          <h2>风穿过织物，<br />也吹进了茶山。</h2>
          <span className="bridge__small">下一站，顾渚。</span>
        </div>
      </section>

      <Chapter data={chapters[2]} register={register} onToggle={onToggle} expanded={Boolean(expanded.tea)} />

      <Chapter data={chapters[3]} register={register} onToggle={onToggle} expanded={Boolean(expanded.tower)} />

      <section id="city-gate" className="city-gate" data-story-section>
        <div className="city-gate__viewport">
          <span className="city-gate__rule" aria-hidden="true" />
          <p>从器物，走到城中。</p>
          <h2>一毫、一线、一盏、一塔。<br />再向外走，是湖州的街与城。</h2>
          <a href="#yishang">继续入城 <span aria-hidden="true">↗</span></a>
        </div>
      </section>

      {CITY_SCENES.map((scene) => <CityChapter key={scene.id} scene={scene} register={register} expanded={Boolean(expanded[scene.id])} onToggle={onToggle} />)}

      <section id="ending" className="film-section ending" data-story-section>
        <div className="film-section__viewport ending__viewport">
          <p>万象归湖</p>
          <h2>由手中之物，<br />走向城中万象。<br />终究，回到水边。</h2>
          <a href="#opening" className="ending__restart">重新漫游 <span aria-hidden="true">↗</span></a>
        </div>
      </section>
    </main>

    <footer id="sources" className="colophon">
      <div><span className="colophon__mark">层见湖州</span><p>在器物与建筑的层次里，重新认识一座城。</p></div>
      <div className="colophon__sources">
        <p>内容与影像</p>
        <a href="https://commons.wikimedia.org/wiki/File:Nanxun_-_Ancient_water_town_-_0081.jpg" target="_blank" rel="noreferrer">南浔照片 · Stefan Fussan / Wikimedia Commons ↗</a>
        <a href="https://creativecommons.org/licenses/by-sa/3.0/" target="_blank" rel="noreferrer">照片与改编影片 · CC BY-SA 3.0 ↗</a>
        <a href="https://ich.unesco.org/en/RL/sericulture-and-silk-craftsmanship-of-china-00197" target="_blank" rel="noreferrer">中国蚕桑丝织技艺 · UNESCO ↗</a>
        <a href="https://www.ihchina.cn/" target="_blank" rel="noreferrer">中国非物质文化遗产网 ↗</a>
        <a href="https://www.dpm.org.cn/collection/studie/234676.html" target="_blank" rel="noreferrer">湖笔形制 · 故宫博物院 ↗</a>
        <a href="https://www.chinasilkmuseum.com/yz/info_18.aspx?itemid=26687" target="_blank" rel="noreferrer">双林绫绢织机 · 中国丝绸博物馆 ↗</a>
        <a href="https://www.teamuseum.cn/mobile/holding-detail.htm?id=506" target="_blank" rel="noreferrer">越窑带托盏 · 中国茶叶博物馆 ↗</a>
        <a href="https://zh.wikipedia.org/wiki/%E9%A3%9E%E8%8B%B1%E5%A1%94" target="_blank" rel="noreferrer">飞英塔结构资料 ↗</a>
        <a href="https://commons.wikimedia.org/wiki/File:Xuan_Brushes_for_Chinese_Brush_painting_and_calligraphy.jpg" target="_blank" rel="noreferrer">毛笔材质照片 · ink stone / CC BY-SA 2.0 ↗</a>
        <a href="https://commons.wikimedia.org/wiki/File:Silk-weaving_loom_(7440319270).jpg" target="_blank" rel="noreferrer">织机照片 · Caitriana Nicholson / CC BY-SA 2.0 ↗</a>
        <a href="https://commons.wikimedia.org/wiki/File:%E5%B8%B8%E8%88%88%E8%8C%B6%E5%9C%92_Changxing_Tea_Plantation_-_panoramio.jpg" target="_blank" rel="noreferrer">长兴茶园照片 · lienyuan lee / CC BY 3.0 ↗</a>
        <a href="https://commons.wikimedia.org/wiki/File:Feiying_Pagoda_2.jpg" target="_blank" rel="noreferrer">飞英塔内部照片 · 钉钉 / CC BY-SA 4.0 ↗</a>
        {CITY_SCENES.flatMap((scene) => [
          <a key={`${scene.id}-one`} href={scene.sourceUrl} target="_blank" rel="noreferrer">{scene.place.split(' · ')[0]} · {scene.imageCaption} / {scene.sourceLabel} ↗</a>,
          <a key={`${scene.id}-two`} href={scene.secondarySourceUrl} target="_blank" rel="noreferrer">{scene.place.split(' · ')[0]} · {scene.secondaryCaption} / {scene.secondarySourceLabel} ↗</a>,
        ])}
        <a href="https://creativecommons.org/licenses/by-sa/4.0/" target="_blank" rel="noreferrer">城市影像许可说明 · CC BY-SA 4.0 ↗</a>
        <a href="https://creativecommons.org/licenses/by/4.0/" target="_blank" rel="noreferrer">马戏城演出影像许可说明 · CC BY 4.0 ↗</a>
        <small>3D 展品为示意性数字创作，用于说明结构与工艺。</small>
      </div>
    </footer>
    {videoStatus === 'error' && <div className="media-status" role="status">动态影像暂未加载，仍可继续浏览展品。</div>}
  </>;
}
