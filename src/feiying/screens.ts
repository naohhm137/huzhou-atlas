// Exact per-screen copy from production/feiying/design/design-spec.md (tutorial 7.10: the page
// uses this text, not the text rendered inside the design images).
export type FeiyingScreen = {
  id: string;
  nav: string;
  eyebrow: string;
  title: string[];
  body: string[];
  layout: 'cover' | 'left' | 'left-top' | 'right' | 'right-end';
  points?: string[];
};

export const FEIYING_SCREENS: readonly FeiyingScreen[] = [
  { id: 'cover', nav: '初见', eyebrow: '湖州 · 吴兴', title: ['一座塔', '藏另一座塔'], body: ['外塔七层 · 内塔五层'], layout: 'cover' },
  { id: 'body', nav: '塔身', eyebrow: '02 / 塔身', title: ['七层八面，', '向上生长。'],
    body: ['楼阁式砖木外塔，逐层收分，', '腰檐层层出挑，檐角轻轻起翘。'], layout: 'left',
    points: ['七层 · 外塔', '八面 · 平面', '副阶 · 底层围廊'] },
  { id: 'within', nav: '塔中塔', eyebrow: '03 / 塔中塔', title: ['外塔展开，', '内塔显现。'],
    body: ['七层砖木外塔之中，', '立着一座五层仿木石塔。'], layout: 'left-top' },
  { id: 'dougong', nav: '斗栱', eyebrow: '04 / 斗栱', title: ['一木承一木。'],
    body: ['层层出挑，托起深远的腰檐。'], layout: 'left-top' },
  { id: 'stone', nav: '石塔', eyebrow: '05 / 石塔', title: ['石上千佛，', '静立塔心。'],
    body: ['内塔为仿木楼阁式石塔，', '塔身遍刻佛龛，', '被外塔木构层层守护。'], layout: 'right',
    points: ['塔中有塔的独特形制', '石与木的双重营造', '宋代江南的工艺见证'] },
  { id: 'guard', nav: '守护', eyebrow: '06 / 守护', title: ['塔中有塔，', '岁月有痕。'],
    body: ['理解，是守护的开始。'], layout: 'right-end' },
] as const;

// [full, short] — the short form is used on narrow screens where the leader line has less room.
export const FEIYING_LABELS = {
  spire: ['塔刹', '塔刹'], outer: ['外塔 · 七层木构', '外塔'], inner: ['内塔 · 五层石塔', '内塔'], base: ['须弥座', '须弥座'],
  dou: ['斗', '斗'], gong: ['栱', '栱'], ang: ['昂', '昂'],
} as const;
