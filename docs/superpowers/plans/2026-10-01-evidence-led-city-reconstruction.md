# 湖州城市四景证据驱动重建实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 用与实景有可核对关系的 Blender 城市四景替换通用几何微缩场景。

**Architecture:** 保留现有 React/Three.js 交互契约，重建 Blender 模型并更新场景事实与展签。纯数据定义负责可验证的原型特征，Blender 脚本负责几何、材质、分件和预览，网页仅接收 GLB 与文案。

**Tech Stack:** Blender 4.2/bpy, GLB/glTF, TypeScript, React, Three.js, Vitest, Vite.

**Spec:** `docs/superpowers/specs/2026-10-01-evidence-led-city-reconstruction-design.md`

## Global Constraints

- 保留既有四个器物/飞英塔展品以及两份教程的滚动影片与可逆 3D 展开。
- 保留已署名的实景背景与本地预览，不发布公网。
- 无施工图的细部不能宣称测绘级精确复原。
- 模型轮廓、空间逻辑和特征优先于表面纹理复杂度。

---

### Task 1: 教程、原型与建模契约

**Files:** `REFERENCE_TUTORIALS.md`, `REFERENCE_YISHANG.md`, `REFERENCE_CITY_PROTOTYPES.md`, `assets/blender/city_recipes.py`, `src/tests/cityFidelity.test.ts`.

- [ ] 记录两份教程、木塔演示视频与视差技能包的可访问内容及缺失资料；核查四景证据。
- [ ] 先写失败测试：新资产要有标识性构件节点与来源说明，双塔标称高度一致，百间楼与马戏城名称不能泛化。
- [ ] 为每处建立照片锚点、部件、可见/推定特征和拆解向量清单。
- [ ] 运行测试并确认失败点准确。

### Task 2: Blender 四景重建

**Files:** `assets/blender/build_city.py`, `assets/blender/sources/city-*.blend`, `assets/blender/previews/city-*.png`, `public/models/city-*.glb`.

- [ ] 先做真实轮廓白模：逐栋街区、双塔折线幕墙、马戏城多层门廊、百间楼非镜像河岸。
- [ ] 加入有依据的近景细节与 PBR 材质；保留每个可动组的独立节点与初始变换。
- [ ] 分别运行 Blender 生成、预览；对照相应实景照片，一次批量修正明显差异。
- [ ] 验证 GLB 结构、贴图、可动节点、文件大小和源 `.blend`。

### Task 3: 网站接入与视觉验收

**Files:** `src/cityScenes.ts`, `src/CityChapter.tsx`, `src/exhibits.ts`, `src/style.css`, `DESIGN.md`, `REFERENCE_RESEARCH.md`.

- [ ] 更新事实文案与模型展签，区分具体原型和解释性补全；不修改前四展品行为。
- [ ] 跑测试、生产构建和 Impeccable 检测。
- [ ] 在生产本地预览检查桌面、中屏、手机的四景装配/拆解、旋转、回滚、图片与控制台。
- [ ] 对首轮发现的问题作一次集中修复，再确认一次；只交本地链接与仍有资料缺口的说明。
