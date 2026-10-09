# Blender 展品重做实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 用真实 Blender 分件资产替换粗糙的程序化展品，修好毛笔、茶汤、飞英塔拆解，并让四章各有相关背景影像。

**Architecture:** Blender 4.2 的 `bpy` 脚本在 `assets/blender/` 生成四份带独立节点及 custom properties 的 GLB；网页通过 GLTFLoader 加载，并从节点 extras 读取拆解方向和原始位姿。展品背景采用有来源的照片，模型与文字保持前景对比。保留现有 scroll-scrubbed 影片、章节锚点及无障碍回退。

**Tech Stack:** Blender 4.2 Python API、glTF/GLB、Three.js、React、Vite、Vitest、GSAP ScrollTrigger。

**Spec:** `PRODUCT.md`、`DESIGN.md`、`REFERENCE_RESEARCH.md` 和用户本轮对三件展品及背景的逐项反馈。

## Global Constraints

- 飞英塔是外七层、内五层的塔中塔；外塔前开口是解释性剖面，不是史实原貌。
- 湖笔只是一支完整的笔；展示毫层时不得出现多支独立笔头。
- 茶盏参考唐越窑带托盏，但茶汤与整叶冲泡是当代示意；盏身圈足和盏托圈足必须各有归属。
- 每个 movable 节点保留初始变换，拆解能精确归位；桌面与移动视口均不得裁切飞英塔。
- 素材有可追溯来源和许可；不把通用或其他地区影像称为湖州实景。

### Task 1: 建模数据与加载契约

**Files:** Create `assets/blender/build_exhibits.py`; create `src/modelAsset.ts`; modify `src/exhibits.ts`; test `src/tests/modelAsset.test.ts`.

**Interfaces:** `loadExhibitAsset(kind): Promise<ExhibitModel>` 返回 `root` 和从 GLB extras 解析的 `MovablePart[]`；`collectMovableParts(root)` 捕获原始局部位置。Blender 每个可动 Empty 写入 `explodeDirection: [x,y,z]`、`explodeDistance: number`。

- [ ] 先写测试：缺失方向、零长度方向、重复名称应被拒绝；有效节点返回准确原点和单位方向。
- [ ] 运行 `pnpm test -- src/tests/modelAsset.test.ts`，确认因模块或行为缺失而失败。
- [ ] 实现 GLTFLoader 加载、GLB extras 解析和错误回退。
- [ ] 重跑测试，确认通过。

### Task 2: 四个 Blender 展品

**Files:** Modify `assets/blender/build_exhibits.py`; generate `public/models/{brush,loom,tea,tower}.glb`; test `src/tests/modelFiles.test.ts`.

**Interfaces:** 每个 GLB 至少一个可动组件；网页无需猜测网格结构。脚本导出 `.blend` 工作源文件与 `.glb` 交付文件。

- [ ] 先写 GLB 结构测试：四个文件存在、glTF JSON 合法、毛笔只有一个整体笔锋、茶盏/盏托/液体/叶片分层、塔七外五内与斗拱节点齐全。
- [ ] 运行单项测试，确认因资产缺失而失败。
- [ ] Blender 建模并导出：笔的兰蕊式毫束、竹管与刻字；水平织机的独立经纬线；有内壁的瓷盏、可辨液体与芽叶；分层八角塔的梁、柱、檐、瓦脊、斗拱及内石塔。
- [ ] 用 Blender 后台重新打开每个 GLB 并检查节点和边界；重跑结构测试。

### Task 3: 版式、照片与拆解构图

**Files:** Modify `src/site.tsx`, `src/style.css`, `src/tokens.css`, `DESIGN.md`, `README.md`；增加 `public/media/chapter-*.jpg` 与来源记录。

**Interfaces:** `Chapter` 根据 `kind` 显示其对应影像；模型始终在影像上方，展开时相机按全部可动部件包围盒适配视口。

- [ ] 先写相机适配的纯函数测试：给定塔展开高度和窄屏纵横比，计算的相机距离能覆盖完整边界。
- [ ] 运行测试，确认旧固定相机逻辑不满足该契约。
- [ ] 加入四章经核权的影像与影像层；修正文案、模型焦点、响应式布局及展开状态提示。
- [ ] 重跑测试与构建；在桌面和手机视口检查完整塔、茶叶/液面、笔锋轮廓和文字对比。

### Task 4: 验证与交付

**Files:** Modify `README.md`, `REFERENCE_RESEARCH.md`; rebuild `dist/` and候选 ZIP。

**Interfaces:** `pnpm test`、`pnpm build`、Blender GLB 检查均成功；记录实际视觉检查渠道及其限制。

- [ ] 运行全量测试与构建，读完整输出。
- [ ] 检查模型渲染图和网页桌面/移动截图；统一修复观察到的问题后再验证一次。
- [ ] 扫描素材来源、体积与加载错误，更新文档和 ZIP。
- [ ] 只依据实测结果陈述完成范围与未完成事项。
