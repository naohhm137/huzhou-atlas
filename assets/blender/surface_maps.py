"""Deterministic, seamless material-scale PBR maps, shared by Blender assets.

These are authored microstructures, not measured scans. Photographic facade
patches remain separate so lighting baked into a photo is never used as relief.
"""
import numpy as np


def surface_maps(kind, rgb, roughness, size=1024):
    axis = np.linspace(0, 1, size, dtype=np.float64)
    u, v = np.meshgrid(axis, axis)
    tau = 2 * np.pi

    def relief(x, y):
        broad = np.sin(tau * (3*x + 2*y)) * np.cos(tau * (2*x - 3*y))
        fine = np.sin(tau * (47*x + 31*y)) * np.cos(tau * (29*x - 43*y))
        if kind in ('wood', 'bamboo', 'hair', 'silk'):
            frequency = 54 if kind in ('hair', 'silk') else 28
            return 0.55*np.sin(tau*frequency*x + 0.28*np.sin(tau*3*y)) + 0.08*fine
        if kind == 'glass': return 0.008*broad
        if kind == 'glaze': return 0.035*broad + 0.002*fine
        if kind == 'water': return 0.15*np.sin(tau*(4*x + 12*y)) + 0.015*fine
        if kind == 'tile': return 0.18*broad + 0.07*fine
        return 0.22*broad + 0.13*fine

    height = relief(u, v)
    delta = 1/size
    strength = 0.025 if kind in ('glass', 'glaze') else 0.6
    dx = (relief(u+delta, v)-relief(u-delta, v))*strength
    dy = (relief(u, v+delta)-relief(u, v-delta))*strength
    normals = np.stack((-dx, -dy, np.ones_like(dx)), axis=-1)
    normals /= np.linalg.norm(normals, axis=-1, keepdims=True)
    contrast = 0.05 if kind in ('glass', 'glaze') else 0.22
    color = np.clip(np.asarray(rgb)[None, None, :]*(1+contrast*height[..., None]), 0, 1)
    rough = np.clip(roughness*(1+0.16*height), 0.035, 0.98)
    alpha = np.ones((size, size, 1))
    return {
        'color': np.concatenate((color, alpha), axis=-1).astype(np.float32),
        'roughness': np.concatenate((np.repeat(rough[..., None], 3, axis=-1), alpha), axis=-1).astype(np.float32),
        'normal': np.concatenate((normals*0.5+0.5, alpha), axis=-1).astype(np.float32),
    }
