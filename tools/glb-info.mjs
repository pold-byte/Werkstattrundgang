// tools/glb-info.mjs — Materialien, Texturen und Erweiterungen einer .glb ohne Abhaengigkeiten.
// Aufruf: node tools/glb-info.mjs app/public/szene.glb [--json]
import { readFileSync } from 'node:fs';

const TEXTURFELDER = {
  baseColor: (m) => m.pbrMetallicRoughness?.baseColorTexture?.index,
  metallicRoughness: (m) => m.pbrMetallicRoughness?.metallicRoughnessTexture?.index,
  normal: (m) => m.normalTexture?.index,
  emissive: (m) => m.emissiveTexture?.index,
};

export function liesGlbInfo(buffer) {
  const b = Buffer.isBuffer(buffer) ? buffer : Buffer.from(buffer);
  if (b.readUInt32LE(0) !== 0x46546c67) throw new Error('keine glb-Datei (Magic fehlt)');
  const jsonLaenge = b.readUInt32LE(12);
  const json = JSON.parse(b.subarray(20, 20 + jsonLaenge).toString('utf8'));
  const bin = b.subarray(20 + jsonLaenge + 8);
  const views = json.bufferViews || [];
  const images = (json.images || []).map((img, i) => {
    const v = views[img.bufferView];
    return { name: img.name || `image_${i}`, mimeType: img.mimeType, bytes: v ? v.byteLength : 0 };
  });
  const textures = json.textures || [];
  const materials = (json.materials || []).map((m) => {
    const pbr = m.pbrMetallicRoughness || {};
    const tex = {};
    for (const [feld, lies] of Object.entries(TEXTURFELDER)) {
      const idx = lies(m);
      tex[feld] = idx === undefined ? null : textures[idx]?.source ?? null;
    }
    return {
      name: m.name,
      baseColorFactor: pbr.baseColorFactor || [1, 1, 1, 1],
      metallicFactor: pbr.metallicFactor ?? 1,
      roughnessFactor: pbr.roughnessFactor ?? 1,
      textures: tex,
      extensions: Object.keys(m.extensions || {}),
      alphaMode: m.alphaMode || 'OPAQUE',
    };
  });
  void bin;
  return { materials, images, extensionsUsed: json.extensionsUsed || [], size: b.length };
}

function formatiere(info) {
  const zeilen = info.materials.map((m) => {
    const base = m.baseColorFactor.slice(0, 3).map((c) => c.toFixed(2)).join(',');
    const tex = Object.entries(m.textures).filter(([, v]) => v !== null).map(([k]) => k).join(',') || '-';
    return `${m.name} | base=${base} | metal=${m.metallicFactor.toFixed(2)} rough=${m.roughnessFactor.toFixed(2)} | tex=${tex} | alpha=${m.alphaMode} | ext=${m.extensions.join(',') || '-'}`;
  });
  const bildBytes = info.images.reduce((s, i) => s + i.bytes, 0);
  zeilen.push(`images: ${info.images.length} (${bildBytes} bytes)`);
  zeilen.push(`extensionsUsed: ${info.extensionsUsed.join(', ') || '-'}`);
  zeilen.push(`size: ${info.size} bytes`);
  return zeilen.join('\n');
}

if (process.argv[1] && import.meta.url === `file:///${process.argv[1].replace(/\\/g, '/')}`) {
  const [pfad, flag] = process.argv.slice(2);
  if (!pfad) { console.error('Aufruf: node tools/glb-info.mjs <datei.glb> [--json]'); process.exit(2); }
  const info = liesGlbInfo(readFileSync(pfad));
  console.log(flag === '--json' ? JSON.stringify(info, null, 2) : formatiere(info));
}
