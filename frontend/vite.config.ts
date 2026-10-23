import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'
import { fileURLToPath } from 'node:url'

const repoRoot = fileURLToPath(new URL('..', import.meta.url))

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, repoRoot, '')
  const backendPort = Number(env.BACKEND_PORT || 8000)
  const frontendPort = Number(env.FRONTEND_PORT || 5173)

  return {
    plugins: [react()],
    // Silero VAD + ONNX Runtime assets are copied into public/vad/ by the
    // `predev`/`prebuild` npm scripts (copy-vad-assets.mjs), so the VAD runs
    // fully offline (no CDN) in dev, build and preview.
    envDir: repoRoot,
    server: {
      port: frontendPort,
      strictPort: true,
      proxy: {
        '/api': {
          target: `http://127.0.0.1:${backendPort}`,
          changeOrigin: true,
        },
      },
    },
  }
})
