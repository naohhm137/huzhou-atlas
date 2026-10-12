# 层见湖州高保真重制 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 将现有文化漫游网站升级为具有 Lux3D 局部细节、Blender 可解释分件和统一滚动时间轴的高保真数字展览。

**Architecture:** 保留现有 React/Three.js/GSAP 页面和数据来源；新增资产索引、分层模型导出和统一故事配置。模型升级先在 Blender 源文件中完成，再导出桌面与移动 GLB，网页只消费已验收资产。

**Tech Stack:** Blender 4.2 Python, GLB/glTF, Three.js, React, TypeScript, GSAP, Vitest, Vite.

**Spec:** `docs/superpowers/specs/2026-10-11-high-fidelity-redesign.md`

## Global Constraints

- 保留现有来源、许可、WebGL 回退和 reduced-motion 支持。
- 复杂局部使用 Lux3D，规则结构使用 Blender；不得把未经清理的 AI 网格直接作为最终网页资产。
- 每个可拆部件保留独立 GLB 节点和初始变换。
- 任何完成声明都必须附带新鲜构建、测试和显示回归证据。

---

### Task 1: 资产审计与资产索引

**Files:**
- Create: `public/asset-index.json`
- Create: `docs/asset-audit-2026-10-11.md`
- Modify: `src/modelAsset.ts`
- Test: `src/modelAsset.test.ts`

- [ ] 扫描现有 `.blend`、`.glb`、贴图和节点名，建立 tea/brush/tower/loom 的来源、版本、节点和体积记录。
- [ ] 给每个可拆节点补齐 `builder`, `lux3dMode`, `explodeDirection`, `explodeDistance` 和 `quality` 字段。
- [ ] 写测试验证 JSON 中四件展品存在、节点名非默认名、网页路径可解析。
- [ ] 运行 `pnpm test -- src/modelAsset.test.ts`，再运行 `pnpm build`。

### Task 2: 统一故事时间轴

**Files:**
- Create: `src/storyChapters.ts`
- Modify: `src/storyTiming.ts`, `src/site.tsx`, `src/exhibits.ts`
- Test: `src/storyChapters.test.ts`

- [ ] 定义六段章节类型，包含 `start`, `end`, `title`, `focusPart`, `camera`, `rotation`, `explode`, `textPosition`。
- [ ] 让视频、相机、模型、拆解、文字和进度条都从同一配置读取。
- [ ] 测试边界、反向滚动、最后一段和 reduced-motion 映射。
- [ ] 运行相关测试和构建。

### Task 3: 第一批高保真资产

**Files:**
- Modify: `assets/blender/build_exhibits.py`
- Create: `assets/blender/build_high_fidelity.py`
- Create: `assets/blender/quality_report.py`
- Create: `assets/blender/README_HIGH_FIDELITY.md`
- Outputs: `public/models/brush-hifi.glb`, `public/models/tea-hifi.glb`, `public/models/tower-hifi.glb`

- [ ] 先用现有 Blender 几何确定比例和分件边界。
- [ ] 对湖笔笔锋、茶器釉面与茶叶、飞英塔瓦片/斗拱建立 Lux3D 输入参考和版本记录。
- [ ] 将 Lux3D 输出导入 Blender，修正比例、法线、非流形面、材质槽和父子关系。
- [ ] 生成高模、移动模和回退预览，运行质量脚本检查节点、贴图、轴心和体积。
- [ ] 仅在质量报告通过后替换网页资产。

### Task 4: 展览级材质与灯光

**Files:**
- Modify: `src/exhibits.ts`, `src/style.css`
- Modify: `assets/blender/build_high_fidelity.py`
- Test: `src/exhibits.test.ts`

- [ ] 为木、竹、丝、釉、石、瓦建立独立 roughness/normal/AO 参数。
- [ ] 增加接触阴影、边缘高光和局部研究灯光。
- [ ] 让焦点部件选中时只提高亮度和轮廓，不使用大面积发光覆盖材质。
- [ ] 测试材质回退和 WebGL 禁用状态。

### Task 5: 六屏网页叙事和交互

**Files:**
- Modify: `src/ExhibitChapter.tsx`, `src/CityChapter.tsx`, `src/site.tsx`, `src/style.css`
- Create: `src/PartAnnotation.tsx`
- Test: `src/storyChapters.test.ts`, `scripts/verify-display.mjs`

- [ ] 将每件展品改为初见/整体/结构/细节/价值/收尾六段。
- [ ] 增加部件标签、结构连线、局部镜头和材质/结构模式切换。
- [ ] 确保拖动旋转与滚动拆解不抢同一输入；移动端使用触摸友好的入口。
- [ ] 更新显示回归，覆盖桌面、手机、快速滚动、反向滚动和 WebGL 回退。

### Task 6: 性能与最终验收

**Files:**
- Modify: `README.md`, `QUALITY_REQUIREMENTS_2026-10-09.md`
- Create: `docs/FINAL_AUDIT_2026-10-11.md`

- [ ] 运行 `pnpm test`、`pnpm build`、`node scripts/verify-display.mjs`。
- [ ] 检查首屏加载、GLB 体积、材质贴图、移动端内存和慢网络回退。
- [ ] 生成桌面/移动端截图并逐屏对照设计基准。
- [ ] 记录已通过项目、剩余限制、来源和最终资产版本；只有全部通过后通知用户。
