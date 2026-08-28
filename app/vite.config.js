import { defineConfig } from 'vite';
import { fileURLToPath, URL } from 'node:url';

export default defineConfig({
  base: './',
  build: {
    rollupOptions: {
      input: {
        index: fileURLToPath(new URL('./index.html', import.meta.url)),
        // druck: aktiviert in Task 12
      },
    },
  },
  test: {
    environment: 'happy-dom',
  },
});
