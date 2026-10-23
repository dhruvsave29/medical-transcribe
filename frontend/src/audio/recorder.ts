/**
 * RecorderService — mic capture + Silero VAD chunking (PRD Step 2).
 *
 * Adds a growing session buffer so Save Recording can emit a single WAV of the
 * whole session. Every completed speech segment is emitted as
 * { record, wav } where wav is 16 kHz mono PCM used by Step 3's uploader.
 */

import { MicVAD } from '@ricky0123/vad-web'
import { MIC_CONSTRAINTS, TARGET_SAMPLE_RATE, VAD_OPTIONS } from './vadConfig'
import { encodeWavPcm16, mergeFloat32 } from './wav'

export type RecorderErrorKind =
  | 'permission_denied'
  | 'mic_not_found'
  | 'mic_busy'
  | 'insecure_context'
  | 'model_load_failed'
  | 'unknown'

export interface ChunkRecord {
  index: number
  durationMs: number
  sizeBytes: number
  /** performance.now() when VAD opened the segment. */
  startedAt: number
  finishedAt: number
}

export interface ChunkWithWav {
  record: ChunkRecord
  wav: Blob
}

export interface RecorderCallbacks {
  onChunk?: (chunk: ChunkWithWav) => void
  onMisfire?: () => void
}

export class RecorderInitError extends Error {
  constructor(
    readonly kind: RecorderErrorKind,
    cause: unknown,
  ) {
    super(`Recorder init failed: ${kind}`, { cause: cause as Error })
    this.name = 'RecorderInitError'
  }
}

const toKind = (error: unknown): RecorderErrorKind => {
  const name = error instanceof DOMException || error instanceof Error ? error.name : ''
  const message = error instanceof Error ? error.message : String(error)
  if (name === 'NotAllowedError' || name === 'SecurityError') return 'permission_denied'
  if (name === 'NotFoundError' || name === 'OverconstrainedError') return 'mic_not_found'
  if (name === 'NotReadableError' || name === 'AbortError') return 'mic_busy'
  if (!navigator.mediaDevices || !window.isSecureContext) return 'insecure_context'
  if (message.includes('model') || message.includes('onnx')) return 'model_load_failed'
  return 'unknown'
}

class RecorderService {
  private vad: MicVAD | null = null
  private stream: MediaStream | null = null
  private lastReleasedTrackStates: string[] = []
  private sessionFrames: Float32Array[] = []
  private chunkSeq = 0
  private chunkWavs = new Map<number, Blob>()
  private speechOpenedAt = 0

  get isRecording(): boolean {
    return this.vad?.listening ?? false
  }

  get sessionAudioMs(): number {
    return this.sessionFrames.length * 32 // 512-sample frames @16k = 32 ms
  }

  get chunkCount(): number {
    return this.chunkSeq
  }

  /** MediaStreamTrack readyStates — "mic released" acceptance check uses this. */
  trackStates(): string[] {
    if (this.stream) return this.stream.getTracks().map((t) => t.readyState)
    return this.lastReleasedTrackStates
  }

  async start(callbacks: RecorderCallbacks): Promise<void> {
    if (this.isRecording) return
    try {
      this.vad = await MicVAD.new({
        model: 'v5',
        startOnLoad: true,
        baseAssetPath: '/vad/',
        onnxWASMBasePath: '/vad/',
        /**
         * Point ORT at locally-served wasm glue + binary (no CDN, PRD 2).
         * Dev: /src/vendor/ (Vite serves project files as modules/fetches).
         * Build: /vad/ort/ (copied by copy-vad-assets.mjs into the dist via
         * public/). numThreads=1 avoids SharedArrayBuffer/COOP-COEP needs.
         */
        ortConfig: (ort) => {
          ort.env.wasm.wasmPaths = import.meta.env.DEV ? '/src/vendor/' : '/vad/ort/'
          ort.env.wasm.numThreads = 1
          ort.env.wasm.proxy = false
        },
        getStream: () =>
          navigator.mediaDevices
            .getUserMedia({ audio: { ...MIC_CONSTRAINTS } })
            .then((stream) => {
              this.stream = stream
              return stream
            }),
        pauseStream: (stream) => {
          stream.getTracks().forEach((t) => t.stop())
          return Promise.resolve()
        },
        resumeStream: () =>
          navigator.mediaDevices.getUserMedia({ audio: { ...MIC_CONSTRAINTS } }),
        ...VAD_OPTIONS,
        onSpeechStart: () => {
          this.speechOpenedAt = performance.now()
        },
        onFrameProcessed: (_probability, frame) => {
          // Defensive copy: worklet frames can be reused; 2 KB per copy is fine.
          this.sessionFrames.push(frame.slice())
        },
        onSpeechEnd: (audio) => {
          const finishedAt = performance.now()
          const durationMs = (audio.length / TARGET_SAMPLE_RATE) * 1000
          if (durationMs < VAD_OPTIONS.minSpeechMs || audio.length < 512) return
          const wav = encodeWavPcm16(audio, TARGET_SAMPLE_RATE)
          const index = ++this.chunkSeq
          this.chunkWavs.set(index, wav)
          callbacks.onChunk?.({
            record: {
              index,
              durationMs,
              sizeBytes: wav.size,
              startedAt: this.speechOpenedAt,
              finishedAt,
            },
            wav,
          })
        },
        onVADMisfire: () => {
          callbacks.onMisfire?.()
        },
      })
    } catch (error) {
      this.vad = null
      throw new RecorderInitError(toKind(error), error)
    }
  }

  async stop(): Promise<void> {
    const vad = this.vad
    this.vad = null
    if (!vad) return
    try {
      await vad.destroy()
    } catch {
      // best-effort; tracks get force-stopped below as a guarantee
    } finally {
      // Guarantee mic release (PRD acceptance: browser recording indicator
      // disappears) even if destroy() partially failed.
      const tracks = this.stream?.getTracks() ?? []
      tracks.forEach((t) => t.stop())
      this.lastReleasedTrackStates = tracks.map((t) => t.readyState)
      this.stream = null
    }
  }

  buildSessionWav(): { wav: Blob; durationMs: number } | null {
    if (this.sessionFrames.length === 0) return null
    const samples = mergeFloat32(this.sessionFrames)
    return {
      wav: encodeWavPcm16(samples, TARGET_SAMPLE_RATE),
      durationMs: (samples.length / TARGET_SAMPLE_RATE) * 1000,
    }
  }

  takeChunk(index: number): Blob | undefined {
    return this.chunkWavs.get(index)
  }

  reset(): void {
    this.sessionFrames = []
    this.chunkSeq = 0
    this.chunkWavs.clear()
    this.speechOpenedAt = 0
  }
}

export const recorder = new RecorderService()
