/// <reference types="vitest" />
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5174,
    host: true,
    fs: {
      allow: ['..', '/home/cidquei/CDKTECK']
    }
  },
  optimizeDeps: {
    exclude: ['@cidqueiroz/cdkteck-ui']
  },
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: './src/__tests__/setup.ts'
  }
});

