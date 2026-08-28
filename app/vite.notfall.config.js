import { defineConfig } from 'vite';
import { viteSingleFile } from 'vite-plugin-singlefile';
import { fileURLToPath, URL } from 'node:url';

// Notfall-Fassung (Spec §7, Stufe 1): eine einzige HTML-Datei, laeuft per Doppelklick
// ohne Webserver. Das glb kommt als Base64 aus src/generiert/szene-glb.js.
export default defineConfig({
  base: './',
  plugins: [viteSingleFile()],
  build: {
    outDir: 'dist-notfall',
    rollupOptions: {
      input: fileURLToPath(new URL('./index.html', import.meta.url)),
    },
  },
});
