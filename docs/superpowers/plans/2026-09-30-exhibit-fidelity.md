# 展品材质与旋转重制 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 修正湖笔双筒误读与旋转反馈，同时提高四件 Blender 展品在网页里的材质真实感。

**Architecture:** Blender 脚本生成有 UV 的分件网格和可嵌入 GLB 的 PBR 图像。Three.js 加载后使用展示环境与可控指针轨道交互。现有 React 章节和爆炸图数据协议不改。

**Tech Stack:** Blender 4.2 `bpy`, glTF 2.0, Three.js r180, React, Vitest, Vite。

**Spec:** `docs/superpowers/specs/2026-09-30-exhibit-fidelity-design.md`

## Global Constraints

- 模型仍为解释性示意，不是文物扫描、测绘或精准复原。
- 四件 GLB 的独立可动节点和反向合拢机制保留。
- 鼠标拖动与手机展开态触摸旋转都应可用；非展开态纵向滚动叙事不受阻。
- 新增纹理需由本项目生成并嵌入 GLB，能在网页而非仅 Blender 预览中看到。
- 每项行为变化先红后绿；最后做桌面与手机实际视觉检查。

### Task 1: 湖笔分件与形体

**Files:** `assets/blender/build_exhibits.py`, `src/tests/modelFiles.test.ts`, `public/models/brush.glb`, `assets/blender/sources/brush.blend`。

**Interfaces:** `brush()` 继续导出 `brush.glb`，保留 `竹笔杆`、`嵌接管口`、`毫根结头`、`笔锋_一整束` 的可动 Empty。

- [ ] 测试中断言 brush GLB 没有 `笔帽` 名称、仅一个 `笔锋` 可动件；运行单测看到旧 GLB 因笔帽断言失败。
- [ ] 删除横置笔帽；增加竹管自然节理与不对称细节，不凭空添加真实文物铭文。
- [ ] 只重建 brush GLB／blend／预览，运行单测并检查装配／展开图。

### Task 2: 可导出的 PBR 材质

**Files:** `assets/blender/build_exhibits.py`, `src/tests/modelFiles.test.ts`, `public/models/*.glb`, `assets/blender/sources/*.blend`。

**Interfaces:** `material()` 为指定材料接入可嵌入的基色、粗糙度、法线图；自建 lathe 网格必须有 UV。GLB 的 glTF JSON 在各展品上包含 image/texture 与 `normalTexture`、`pbrMetallicRoughness` 对应条目。

- [ ] 测试断言四个 GLB 的材质真实引用 image texture、法线与粗糙度；运行单测看到旧模型失败。
- [ ] 在 Blender 生成竹、木、釉、茶汤、瓦、石的受控纹理；连接 Principled 节点并为自建曲面加 UV。
- [ ] 重建全部 GLB；检查 `.blend` 可重开、GLB JSON 纹理实际存在、预览无明显接缝或泛白。

### Task 3: 旋转与网页布光

**Files:** `src/orbitGesture.ts`, `src/tests/orbitGesture.test.ts`, `src/exhibits.ts`, `src/style.css`。

**Interfaces:** `advanceOrbit(state, delta, viewport)` 返回有限俯仰和环绕偏航；`ExhibitScene` 使用指针捕获，处理 up/cancel/lostcapture。展开态 `touch-action: none`。

- [ ] 写轨道手势测试，覆盖桌面／手机相同拖距、反向拖动、俯仰边界；运行确认缺少实现而失败。
- [ ] 实现纯函数和指针事件接线；网页光照加入 PBR 环境反射并压低过曝。
- [ ] 运行测试与构建，实测鼠标、手机触摸与合拢后的滚动。

### Task 4: 视觉与交付

**Files:** `DESIGN.md`, `README.md`, `REFERENCE_RESEARCH.md`, `dist/`, 新交付 ZIP。

- [ ] 一轮批量视觉检查桌面、678×559 和 390×844 的四展品装配／展开，以及实际拖动。
- [ ] 仅针对这一轮发现的缺陷做一次修正和确认；运行 `pnpm test`、`pnpm build` 与最终设计检测。
- [ ] 更新素材／模型说明，建立新的 ZIP 并检查源 `.blend`、GLB、dist 和说明文件都在其中。
