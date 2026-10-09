export type CitySceneId = 'yishang' | 'dongwu' | 'longemont' | 'nanxun-city';
export type CityMotion = 'street' | 'towers' | 'theatre' | 'water';

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
    modelParts: '折线石板街 · 逐栋商铺与近代圆角楼 · 深木檐廊 · 街区水巷节点',
    imageCaption: '街心 · 衣裳街夜色', primaryImage: 'media/city-yishang-street.jpg', primaryAlt: '衣裳街夜晚的石板路、店铺和行人',
    sourceLabel: '源義信 · CC BY-SA 4.0', sourceUrl: 'https://commons.wikimedia.org/wiki/File:2023-07-08_Yishang_Street,_Huzhou_%E6%B9%96%E5%B7%9E%E8%A1%A3%E8%A3%B3%E8%A1%97.jpg',
    secondaryImage: 'media/city-yishang-bridge.jpg', secondaryAlt: '衣裳街青莲桥跨过水道，桥上悬挂红灯笼', secondaryCaption: '水边 · 青莲桥',
    secondarySourceLabel: '源義信 · CC BY-SA 4.0', secondarySourceUrl: 'https://commons.wikimedia.org/wiki/File:2023-07-09_Qinglian_Bridge,_Yishang_Street,_Huzhou_%E6%B9%96%E5%B7%9E%E8%A1%A3%E8%A3%B3%E8%A1%97%E9%9D%92%E8%8E%B2%E6%A1%A5.jpg',
  },
  {
    id: 'dongwu', motion: 'towers', place: '东吴国际广场双塔 · 东吴银泰城', title: '抬头，\n是今日湖州。',
    body: '两幢标称 288 米的塔楼与东塔下方的银泰商业裙楼相连。玻璃幕墙上的折线纹样，是从真实照片里辨认它们的一把钥匙。',
    modelParts: '六层商业裙楼 · 双塔幕墙 · 折线斜纹与设备层 · 退台塔冠',
    imageCaption: '近看 · 双塔立面', primaryImage: 'media/city-dongwu-near.jpg', primaryAlt: '湖州东吴国际广场双子塔和下方街道的白日实景',
    sourceLabel: '钉钉 · CC BY-SA 4.0', sourceUrl: 'https://commons.wikimedia.org/wiki/File:%E6%B9%96%E5%B7%9E%E4%B8%9C%E5%90%B4%E5%9B%BD%E9%99%85%E5%B9%BF%E5%9C%BA%E5%8F%8C%E5%AD%90%E5%A1%94.jpg',
    secondaryImage: 'media/city-dongwu-far.jpg', secondaryAlt: '从水岸远望湖州东吴双塔的实景', secondaryCaption: '远望 · 城市水岸',
    secondarySourceLabel: 'Mathewstory · CC BY-SA 4.0', secondarySourceUrl: 'https://commons.wikimedia.org/wiki/File:Two_towers,_central_Huzhou.JPG',
  },
  {
    id: 'longemont', motion: 'theatre', place: '太湖龙之梦国际马戏城 · 湖岸', title: '湖岸之外，\n灯火正盛。',
    body: '这里展示的是龙之梦园区内的国际马戏城正门：放射状彩拱、密密的灯珠和两侧骑马雕塑，把入口变成一场预告。',
    modelParts: '多层彩拱 · 双语招牌与狮徽 · 左右骑马雕塑 · 紫金屋盖',
    imageCaption: '园区一隅 · 国际马戏城入口', primaryImage: 'media/city-longemont-gate.jpg', primaryAlt: '湖州龙之梦国际马戏城彩色拱门的实景',
    sourceLabel: '源義信 · CC BY-SA 4.0', sourceUrl: 'https://commons.wikimedia.org/wiki/File:2023-06-19_%E6%B9%96%E5%B7%9E%E9%BE%99%E4%B9%8B%E6%A2%A6%E5%9B%BD%E9%99%85%E9%A9%AC%E6%88%8F%E5%9F%8E.jpg',
    secondaryImage: 'media/city-longemont-show.jpg', secondaryAlt: '龙之梦国际马戏城内的舞台与演出现场', secondaryCaption: '进入 · 马戏城舞台',
    secondarySourceLabel: '源義信 · CC BY 4.0', secondarySourceUrl: 'https://commons.wikimedia.org/wiki/File:2023-06-19_%E6%B9%96%E5%B7%9E%E9%BE%99%E4%B9%8B%E6%A2%A6%E5%9B%BD%E9%99%85%E9%A9%AC%E6%88%8F%E5%9F%8E%E8%A1%A8%E6%BC%94_01.jpg',
  },
  {
    id: 'nanxun-city', motion: 'water', place: '南浔古镇百间楼 · 河巷', title: '走了一圈，\n还是回到水边。',
    body: '百间楼河段的长排临水屋舍，靠骑楼、披檐和石护岸连成一幅水乡街景。另一张照片摄于南浔别处河巷，可作风貌对照。',
    modelParts: '百间楼河 · 逐栋临水屋舍 · 马头墙与券门 · 石护岸与下河埠',
    imageCaption: '河巷 · 临水屋舍', primaryImage: 'media/city-nanxun-water.jpg', primaryAlt: '南浔古镇黄昏的河道与两岸屋舍',
    sourceLabel: 'Stefan Fussan · CC BY-SA 3.0', sourceUrl: 'https://commons.wikimedia.org/wiki/File:Nanxun_-_Ancient_water_town_-_0153.jpg',
    secondaryImage: 'media/city-nanxun-bank.jpg', secondaryAlt: '南浔古镇另一处临水民居与河上游船', secondaryCaption: '岸边 · 临水民居',
    secondarySourceLabel: 'Stefan Fussan · CC BY-SA 3.0', secondarySourceUrl: 'https://commons.wikimedia.org/wiki/File:Nanxun_-_Ancient_water_town_-_0020.jpg',
  },
];
