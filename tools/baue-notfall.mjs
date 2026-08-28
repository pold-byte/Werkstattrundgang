// Baut die Notfall-Single-File-Fassung:
// 1. szene.glb als Base64 in src/generiert/szene-glb.js schreiben
// 2. vite build mit Notfall-Konfiguration (VITE_NOTFALL=1)
// 3. Stub wiederherstellen, Ergebnis nach dist-notfall/notfall.html benennen
// Aufruf aus der Projektwurzel: node tools/baue-notfall.mjs
import { readFileSync, writeFileSync, renameSync, existsSync } from 'node:fs';
import { execSync } from 'node:child_process';
import { fileURLToPath, URL } from 'node:url';

const wurzel = fileURLToPath(new URL('..', import.meta.url));
const appDir = `${wurzel}app`;
const glbPfad = `${appDir}/public/szene.glb`;
const stubPfad = `${appDir}/src/generiert/szene-glb.js`;
const stubInhalt = readFileSync(stubPfad, 'utf8');

if (!existsSync(glbPfad)) {
  console.error('Abbruch: app/public/szene.glb fehlt (erst Task 11 ausführen).');
  process.exit(1);
}

const b64 = readFileSync(glbPfad).toString('base64');
writeFileSync(
  stubPfad,
  `// GENERIERT von tools/baue-notfall.mjs — nicht committen.\nexport const szeneGlbBase64 = '${b64}';\n`,
);

try {
  execSync('npx vite build --config vite.notfall.config.js', {
    cwd: appDir,
    stdio: 'inherit',
    env: { ...process.env, VITE_NOTFALL: '1' },
  });
  renameSync(`${appDir}/dist-notfall/index.html`, `${appDir}/dist-notfall/notfall.html`);
  console.log('Fertig: app/dist-notfall/notfall.html');
} finally {
  writeFileSync(stubPfad, stubInhalt); // Stub immer wiederherstellen
}
