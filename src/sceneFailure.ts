export type SceneFailureKind = 'graphics' | 'asset' | 'context-lost' | 'initialization';

export class SceneFailure extends Error {
  constructor(public readonly kind: SceneFailureKind, message: string, cause?: unknown) {
    super(message, { cause });
    this.name = 'SceneFailure';
  }
}

export function sceneFailureMessage(kind: SceneFailureKind): string {
  switch (kind) {
    case 'graphics': return '当前应用内预览禁用了 WebGL（不是模型文件损坏）。已切换为 Blender 渲染图；请用 Edge 或 Chrome 打开本地链接体验实时旋转。';
    case 'asset': return '三维模型文件加载失败。已展示模型渲染图，可重试加载。';
    case 'context-lost': return '浏览器中断了 3D 渲染。已保留当前视图，可重试恢复。';
    case 'initialization': return '三维场景初始化失败。已展示模型渲染图，可重试打开。';
  }
}
