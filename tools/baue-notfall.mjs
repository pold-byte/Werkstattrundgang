// Baut die Notfall-Single-File-Fassung:
// 1. szene.glb und die Folienabbildungen als Base64 nach src/generiert/ schreiben
// 2. vite build mit Notfall-Konfiguration (VITE_NOTFALL=1)
// 3. Stubs wiederherstellen, Ergebnis nach dist-notfall/notfall.html benennen
// Aufruf aus der Projektwurzel: node tools/baue-notfall.mjs
import { readFileSync, writeFileSync, renameSync, existsSync, readdirSync } from 'node:fs';
import { execSync } from 'node:child_process';
import { fileURLToPath, URL } from 'node:url';

const wurzel = fileURLToPath(new URL('..', import.meta.url));
const appDir = `${wurzel}app`;
const glbPfad = `${appDir}/public/szene.glb`;
const stubPfad = `${appDir}/src/generiert/szene-glb.js`;
const stubInhalt = readFileSync(stubPfad, 'utf8');
const bilderStubPfad = `${appDir}/src/generiert/folien-bilder.js`;
const bilderStubInhalt = readFileSync(bilderStubPfad, 'utf8');
const bilderDir = `${appDir}/public/folien`;

if (!existsSync(glbPfad)) {
  console.error('Abbruch: app/public/szene.glb fehlt (erst Task 11 ausführen).');
  process.exit(1);
}

const b64 = readFileSync(glbPfad).toString('base64');
writeFileSync(
  stubPfad,
  `// GENERIERT von tools/baue-notfall.mjs — nicht committen.\nexport const szeneGlbBase64 = '${b64}';\n`,
);

// Die Abbildungen der Folien laegen sonst als Nachbardateien neben der HTML und
// fehlten in der Single-File-Fassung; deshalb wandern sie als data:-URL hinein.
const TYPEN = { png: 'image/png', jpg: 'image/jpeg', jpeg: 'image/jpeg', svg: 'image/svg+xml', webp: 'image/webp' };
const bilder = {};
if (existsSync(bilderDir)) {
  for (const name of readdirSync(bilderDir)) {
    const typ = TYPEN[name.split('.').pop().toLowerCase()];
    if (!typ) continue;
    bilder[`./folien/${name}`] = `data:${typ};base64,${readFileSync(`${bilderDir}/${name}`).toString('base64')}`;
  }
}
writeFileSync(
  bilderStubPfad,
  `// GENERIERT von tools/baue-notfall.mjs — nicht committen.
export const bilderBase64 = ${JSON.stringify(bilder)};
`,
);
console.log(`Folienabbildungen eingebettet: ${Object.keys(bilder).length}`);

try {
  execSync('npx vite build --config vite.notfall.config.js', {
    cwd: appDir,
    stdio: 'inherit',
    env: { ...process.env, VITE_NOTFALL: '1' },
  });
  renameSync(`${appDir}/dist-notfall/index.html`, `${appDir}/dist-notfall/notfall.html`);
  console.log('Fertig: app/dist-notfall/notfall.html');
} finally {
  // Stubs immer wiederherstellen
  writeFileSync(stubPfad, stubInhalt);
  writeFileSync(bilderStubPfad, bilderStubInhalt);
}
