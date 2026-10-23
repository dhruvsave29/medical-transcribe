/**
 * Copies VAD/ORT assets from node_modules into locations Vite can serve
 * correctly (PRD Step 2 known pitfall: never a CDN):
 *
 * - frontend/public/vad/            → Silero ONNX model + AudioWorklet glue
 *                                     (fetch-based assets; also land in dist
 *                                     on build)
 * - frontend/src/vendor/            → ORT wasm glue (.mjs, must be *importable*
 *                                     as a module) + .wasm binary, referenced
 *                                     as '/src/vendor/' by the dev server
 * - ORT .wasm + .mjs also land in   → public/vad/ort/ for production builds,
 *                                     where wasmPaths switches to '/vad/ort/'
 *
 * Wired as `predev`/`prebuild` npm scripts; outputs are git-ignored.
 */

import { cpSync, existsSync, mkdirSync, statSync } from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const here = path.dirname(fileURLToPath(import.meta.url))
const frontend = path.resolve(here, '..')
const nodeModules = path.resolve(frontend, 'node_modules')
const publicVad = path.resolve(frontend, 'public', 'vad')
const srcVendor = path.resolve(frontend, 'src', 'vendor')

const ortDir = path.resolve(nodeModules, 'onnxruntime-web/dist')
const ortFiles = ['ort-wasm-simd-threaded.wasm', 'ort-wasm-simd-threaded.mjs']

const copies = [
  {
    from: path.resolve(nodeModules, '@ricky0123/vad-web/dist/silero_vad_v5.onnx'),
    to: publicVad,
  },
  {
    from: path.resolve(nodeModules, '@ricky0123/vad-web/dist/vad.worklet.bundle.min.js'),
    to: publicVad,
  },
  ...ortFiles.map((name) => ({ from: path.resolve(ortDir, name), to: srcVendor })),
  ...ortFiles.map((name) => ({
    from: path.resolve(ortDir, name),
    to: path.join(publicVad, 'ort'),
  })),
]

for (const { from, to } of copies) {
  const srcName = path.basename(from)
  if (!existsSync(from)) {
    throw new Error(`Missing asset: ${from} — run "npm install" first.`)
  }
  const target = path.join(to, srcName)
  if (existsSync(target) && statSync(target).size === statSync(from).size) {
    continue
  }
  mkdirSync(to, { recursive: true })
  cpSync(from, target)
}

console.log('[MediScript] VAD assets synced to public/vad/')
