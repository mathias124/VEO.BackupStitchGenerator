import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
    plugins: [react()],
    build: {
        assetsInlineLimit: 0, // Ensure large files are not inlined
    },
    optimizeDeps: {
        include: ['@ffmpeg/ffmpeg'], // Include the FFmpeg package
    },
    server: {
        headers: {
          'Cross-Origin-Opener-Policy': 'same-origin',
          'Cross-Origin-Embedder-Policy': 'require-corp',
        },
      },
});