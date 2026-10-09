import { describe, expect, it } from 'vitest';
import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import { CITY_SCENES } from '../cityScenes';
import { Box3, Matrix4, Quaternion, Vector3 } from 'three';

type GlbNode = { name?: string; mesh?: number; children?: number[]; translation?: number[]; extras?: Record<string, unknown> };

function nodesFor(scene: string): GlbNode[] {
  const bytes = readFileSync(join(process.cwd(), 'public', 'models', `city-${scene}.glb`));
  const jsonLength = bytes.readUInt32LE(12);
  const gltf = JSON.parse(bytes.toString('utf8', 20, 20 + jsonLength));
  return gltf.nodes;
}

function names(nodes: GlbNode[]): string[] { return nodes.map(node => node.name ?? ''); }

describe('city models carry their reference-specific landmarks', () => {
  it('Yishang has individually identified and non-identical street-front buildings', () => {
    const nodes = nodesFor('yishang');
    const buildings = nodes.filter(node => node.extras?.referenceBuildingId);
    expect(new Set(buildings.map(node => node.extras?.referenceBuildingId)).size).toBeGreaterThanOrEqual(8);
    expect(new Set(buildings.map(node => node.extras?.facadeWidth)).size).toBeGreaterThanOrEqual(4);
    expect(names(nodes)).toEqual(expect.arrayContaining([
      expect.stringContaining('圆角近代楼'), expect.stringContaining('深木檐廊'),
      expect.stringContaining('折线石板街'), expect.stringContaining('青莲桥'),
      expect.stringContaining('门头暖白线性灯'), expect.stringContaining('橱窗内透光层'),
    ]));
    expect(nodes.filter(node => node.extras?.photographicSurface === true).length).toBeGreaterThanOrEqual(3);
  });

  it('Dongwu has twin equal-height main volumes and the photographed facade marks', () => {
    const nodes = nodesFor('dongwu');
    const towers = nodes.filter(node => node.extras?.officialHeightMetres === 288);
    expect(towers).toHaveLength(2);
    expect(names(nodes)).toEqual(expect.arrayContaining([
      expect.stringContaining('幕墙折线斜纹'), expect.stringContaining('深色设备层'),
      expect.stringContaining('退台塔冠'), expect.stringContaining('六层商业裙楼'),
      expect.stringContaining('裙楼弧形转角'), expect.stringContaining('塔间开敞通道'),
    ]));
  });

  it('Dongwu places one tower farther back as in the near photographic view', () => {
    const shafts = nodesFor('dongwu').filter(node => node.name?.startsWith('双塔蓝玻璃锥台主楼'));
    expect(shafts).toHaveLength(2);
    expect(Math.abs(shafts[0].translation![2] - shafts[1].translation![2])).toBeGreaterThan(0.7);
  });

  it('Longemont includes the entrance identity, not just an abstract arch', () => {
    const namesInModel = names(nodesFor('longemont'));
    for (const feature of ['中文弧形招牌', '英文弧形招牌', '狮徽', '左骑马雕塑', '右骑马雕塑', '紫金曲面屋盖']) {
      expect(namesInModel.some(name => name.includes(feature)), feature).toBe(true);
    }
    expect(namesInModel.some(name => name.includes('完整场馆地坪')), 'the venue must sit on one continuous ground plane').toBe(true);
  });

  it('Longemont ground contains the complete assembled hall footprint', () => {
    const bytes = readFileSync(join(process.cwd(), 'public/models/city-longemont.glb'));
    const gltf = JSON.parse(bytes.toString('utf8', 20, 20 + bytes.readUInt32LE(12)));
    const bounds = new Map<string, Box3>();
    const visit = (index: number, parent: Matrix4) => {
      const node = gltf.nodes[index];
      const local = node.matrix ? new Matrix4().fromArray(node.matrix) : new Matrix4().compose(
        new Vector3().fromArray(node.translation ?? [0, 0, 0]),
        new Quaternion().fromArray(node.rotation ?? [0, 0, 0, 1]),
        new Vector3().fromArray(node.scale ?? [1, 1, 1]));
      const world = parent.clone().multiply(local);
      const box = new Box3();
      if (node.mesh !== undefined) for (const primitive of gltf.meshes[node.mesh].primitives) {
        const positions = gltf.accessors[primitive.attributes.POSITION];
        box.union(new Box3(new Vector3().fromArray(positions.min), new Vector3().fromArray(positions.max)).applyMatrix4(world));
      }
      for (const child of node.children ?? []) box.union(visit(child, world));
      bounds.set(node.name, box);
      return box;
    };
    for (const index of gltf.scenes[gltf.scene].nodes) visit(index, new Matrix4());
    const ground = [...bounds].find(([name]) => /彩绘前场|完整场馆地坪/.test(name))![1];
    const hall = bounds.get('宽椭圆场馆外墙与窗带')!;
    // GLB uses Y-up: ground must cover X/Z, regardless of vertical separation.
    expect(ground.min.x).toBeLessThanOrEqual(hall.min.x);
    expect(ground.max.x).toBeGreaterThanOrEqual(hall.max.x);
    expect(ground.min.z).toBeLessThanOrEqual(hall.min.z);
    expect(ground.max.z).toBeGreaterThanOrEqual(hall.max.z);
    const shell = nodesFor('longemont').find(node => node.name === '宽椭圆场馆外墙与窗带')!;
    expect(shell.extras?.explodeDirection).toEqual([0, 1, 0]);
  });

  it('the Nanxun riverfront is specifically Baijianlou and asymmetric', () => {
    const nodes = nodesFor('nanxun');
    const houseIds = nodes.filter(node => node.extras?.referenceBuildingId);
    expect(new Set(houseIds.map(node => node.extras?.referenceBuildingId)).size).toBeGreaterThanOrEqual(8);
    for (const feature of ['百间楼', '三叠马头墙', '琵琶山墙', '沿河券门', '下河埠石阶']) {
      expect(names(nodes).some(name => name.includes(feature)), feature).toBe(true);
    }
  });

  it('city labels identify their precise photographed subjects', () => {
    expect(CITY_SCENES.find(scene => scene.id === 'longemont')?.place).toContain('国际马戏城');
    expect(CITY_SCENES.find(scene => scene.id === 'nanxun-city')?.place).toContain('百间楼');
    expect(CITY_SCENES.find(scene => scene.id === 'dongwu')?.place).toContain('东吴国际广场');
  });
});
