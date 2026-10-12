export type CitySceneId = 'yishang' | 'dongwu' | 'nanxun-city';
export type CityMotion = 'street' | 'towers' | 'water';

export type CitySceneData = {
  id: CitySceneId;
  motion: CityMotion;
  place: string;
  title: string;
  body: string;
  modelParts: string;
  imageCaption: string;
  primaryImage: string;
  primaryAlt: string;
  sourceLabel: string;
  sourceUrl: string;
  secondaryImage: string;
  secondaryAlt: string;
  secondaryCaption: string;
  secondarySourceLabel: string;
  secondarySourceUrl: string;
};

export const CITY_SCENES: readonly CitySceneData[] = [
  {
    id: 'yishang', motion: 'street', place: '衣裳街 · 吴兴', title: '街巷有了灯，\n故事便走进人群。',
    body: '从屋檐下的店铺走向青莲桥，衣裳街的夜色与河埠仍在同一条街巷里相遇。',
    modelParts: '弯折石板街 · 两层木构店铺与红灯笼 · 近代圆角转角楼',
    imageCaption: '街心 · 衣裳街夜色', primaryImage: 'media/city-yishang-street.jpg', primaryAlt: '衣裳街夜晚的石板路、店铺和行人',
    sourceLabel: '源義信 · CC BY-SA 4.0', sourceUrl: 'https://commons.wikimedia.org/wiki/File:2023-07-08_Yishang_Street,_Huzhou_%E6%B9%96%E5%B7%9E%E8%A1%A3%E8%A3%B3%E8%A1%97.jpg',
    secondaryImage: 'media/city-yishang-bridge.jpg', secondaryAlt: '衣裳街青莲桥跨过水道，桥上悬挂红灯笼', secondaryCaption: '水边 · 青莲桥',
    secondarySourceLabel: '源義信 · CC BY-SA 4.0', secondarySourceUrl: 'https://commons.wikimedia.org/wiki/File:2023-07-09_Qinglian_Bridge,_Yishang_Street,_Huzhou_%E6%B9%96%E5%B7%9E%E8%A1%A3%E8%A3%B3%E8%A1%97%E9%9D%92%E8%8E%B2%E6%A1%A5.jpg',
  },
  {
    id: 'dongwu', motion: 'towers', place: '东吴国际广场双塔 · 东吴银泰城', title: '抬头，\n是今日湖州。',
    body: '两幢标称 288 米的塔楼与东塔下方的银泰商业裙楼相连。玻璃幕墙上的折线纹样，是从真实照片里辨认它们的一把钥匙。',
    modelParts: '双塔玻璃幕墙与折线斜纹 · 退台塔冠 · 弧形转角商业裙楼',
    imageCaption: '近看 · 双塔立面', primaryImage: 'media/city-dongwu-near.jpg', primaryAlt: '湖州东吴国际广场双子塔和下方街道的白日实景',
    sourceLabel: '钉钉 · CC BY-SA 4.0', sourceUrl: 'https://commons.wikimedia.org/wiki/File:%E6%B9%96%E5%B7%9E%E4%B8%9C%E5%90%B4%E5%9B%BD%E9%99%85%E5%B9%BF%E5%9C%BA%E5%8F%8C%E5%AD%90%E5%A1%94.jpg',
    secondaryImage: 'media/city-dongwu-far.jpg', secondaryAlt: '从水岸远望湖州东吴双塔的实景', secondaryCaption: '远望 · 城市水岸',
    secondarySourceLabel: 'Mathewstory · CC BY-SA 4.0', secondarySourceUrl: 'https://commons.wikimedia.org/wiki/File:Two_towers,_central_Huzhou.JPG',
  },
  {
    id: 'nanxun-city', motion: 'water', place: '南浔古镇百间楼 · 河巷', title: '走了一圈，\n还是回到水边。',
    body: '百间楼河段的长排临水屋舍，靠骑楼、披檐和石护岸连成一幅水乡街景。另一张照片摄于南浔别处河巷，可作风貌对照。',
    modelParts: '百间楼河 · 临水屋舍与骑楼长廊 · 马头墙 · 石护岸与垂柳',
    imageCaption: '河巷 · 临水屋舍', primaryImage: 'media/city-nanxun-water.jpg', primaryAlt: '南浔古镇黄昏的河道与两岸屋舍',
    sourceLabel: 'Stefan Fussan · CC BY-SA 3.0', sourceUrl: 'https://commons.wikimedia.org/wiki/File:Nanxun_-_Ancient_water_town_-_0153.jpg',
    secondaryImage: 'media/city-nanxun-bank.jpg', secondaryAlt: '南浔古镇另一处临水民居与河上游船', secondaryCaption: '岸边 · 临水民居',
    secondarySourceLabel: 'Stefan Fussan · CC BY-SA 3.0', secondarySourceUrl: 'https://commons.wikimedia.org/wiki/File:Nanxun_-_Ancient_water_town_-_0020.jpg',
  },
];
