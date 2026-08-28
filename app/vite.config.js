import { defineConfig } from 'vite';
import { fileURLToPath, URL } from 'node:url';

export default defineConfig({
  base: './',
  build: {
    rollupOptions: {
      input: {
        index: fileURLToPath(new URL('./index.html', import.meta.url)),
        druck: fileURLToPath(new URL('./druck.html', import.meta.url)),
      },
    },
  },
  test: {
    environment: 'happy-dom',
  },
});
