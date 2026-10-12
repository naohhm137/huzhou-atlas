# 飞英塔重做进度（2026-10-12 完成）

依据《用 AI 三步创建 3D 视差滚动网站》教程（全文在 tutorial/）。三步全部完成。

## 第 1 步 · 设计稿
- design/01–06 六屏，规范和文案见 design/design-spec.md。

## 第 2 步 · 建模
- Lux3D 标准版 5 件：models/lux3d-std/。塔刹用极速版（标准版失败 2 次，没有扣费）。
- Blender 组装：scripts/assemble.py → models/assembled/feiying.blend。
- 网页模型：scripts/grade_export.py 先把调色写进贴图，再导出两个版本。
  - public/models/feiying/feiying.glb（7.2MB）和 feiying-mobile.glb（5.4MB）
  - 都用 Draco + WebP 压缩，7 层外塔加塔刹都是可动节点
- 资产清单：public/asset-index.json 中的 exhibits.tower 已更新。

## 渲染
- scripts/render_shots.py 输出到 renders/final/，六屏各一张。
- 这些图也做成了网页加载时和 WebGL 失败时的海报：public/media/feiying/poster-0N.webp。

## 第 3 步 · 网站
- 新代码在 src/feiying/：
  - timeline.ts：纯函数的滚动时间线
  - scene.ts：three.js 场景
  - FeiyingChapter.tsx：章节组件
  - screens.ts：逐屏文案
  - feiying.css：样式
- site.tsx 里的飞英塔章节已换成 `<FeiyingChapter>`，其他展品没有改动。
- 主要效果：
  - 六屏和设计稿一一对应
  - 视差分层：天空、模型、雾、树影、文字各自以不同速度移动
  - 03 屏拆层并剖开外塔，04 屏经黑场转到斗栱特写，05 屏用剖切看石塔
  - 标注线跟随 3D 锚点
  - 自由观塔：可拖动、缩放，可手动拆层和剖开
  - 手机版重新排了布局
  - 支持系统的"减少动态效果"设置
- 测试：
  - src/tests/feiying.test.ts 新增 10 项单元测试，全部 54 项通过
  - scripts/verify-feiying.mjs 做了 35 项浏览器检查，全部通过（覆盖教程 5.7 的 8 项）
  - 截图在 artifacts/qa-feiying/

## 可选的后续
- 旧的飞英塔资产已不再使用：public/models/tower*.glb、src/models/tower.ts、src/towerAsset.ts、src/towerScreens.ts，以及 exhibits.ts 里飞英塔相关的分支。相关旧测试还在，可以单独清理。
- 生产包的 JS 约 1MB，可以把 three.js 拆成单独的块。
- 塔刹如果想升级标准版，再试一次大约需要 20 积分。
