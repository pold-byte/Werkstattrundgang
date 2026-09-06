import { describe, it, expect } from 'vitest';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';
import { liesGlbInfo } from '../../tools/glb-info.mjs';

const hier = dirname(fileURLToPath(import.meta.url));
const glb = readFileSync(join(hier, '..', 'public', 'szene.glb'));

describe('glb-info', () => {
  it('liest Materialien, Bilder und Erweiterungen aus der Szene', () => {
    const info = liesGlbInfo(glb);
    expect(info.size).toBe(glb.length);
    expect(info.materials.length).toBeGreaterThan(30);
    const leuchte = info.materials.find((m) => m.name === 'Leuchte');
    expect(leuchte).toBeDefined();
    expect(leuchte.extensions).toContain('KHR_materials_emissive_strength');
    expect(info.images.length).toBeGreaterThanOrEqual(4);
    expect(info.images.every((b) => b.bytes > 0)).toBe(true);
  });
  it('weist einem texturierten Material seine Bildreferenz zu', () => {
    const info = liesGlbInfo(glb);
    const boden = info.materials.find((m) => m.name === 'Boden');
    expect(boden.textures.baseColor).toBeTypeOf('number');
  });
});
