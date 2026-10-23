import { useCallback } from 'react'
import { recorder } from '../audio/recorder'
import type { RecorderErrorKind } from '../audio/recorder'
import { useSessionStore } from '../store/sessionStore'
import { chunkUploader } from '../lib/chunkUploader'

const ERROR_MESSAGES: Record<RecorderErrorKind, string> = {
  permission_denied: 'Microphone permission denied — allow the mic in your browser and retry.',
  mic_not_found: 'No microphone found — connect one and retry.',
  mic_busy: 'Microphone is in use by another app — close it and retry.',
  insecure_context: 'Microphone capture needs HTTPS or localhost.',
  model_load_failed: 'Speech model (VAD) failed to load — retry; if it persists, restart the dev server.',
  unknown: 'Could not start the microphone.',
}

const onChunkArrived = (chunk: Parameters<typeof chunkUploader.enqueue>[0]): void => {
  useSessionStore.getState().recordChunk(chunk.record)
  chunkUploader.enqueue(chunk)
}

const stamp = (): string => {
  const d = new Date()
  const p = (n: number) => String(n).padStart(2, '0')
  return `${d.getFullYear()}${p(d.getMonth() + 1)}${p(d.getDate())}-${p(d.getHours())}${p(d.getMinutes())}${p(d.getSeconds())}`
}

const triggerDownload = (blob: Blob, filename: string): void => {
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  a.remove()
  window.setTimeout(() => URL.revokeObjectURL(url), 2000)
}

export function useRecorder() {
  const start = useCallback(async (): Promise<void> => {
    const store = useSessionStore.getState()
    if (store.status === 'recording' || store.status === 'processing') return
    store.startRecording()
    try {
      await recorder.start({
        onChunk: onChunkArrived,
        onMisfire: () => undefined,
      })
    } catch (error) {
      const kind =
        error instanceof Error && 'kind' in error
          ? (error.kind as RecorderErrorKind)
          : 'unknown'
      const failed = useSessionStore.getState()
      failed.recorderFailure(kind)
      failed.pushToast('error', ERROR_MESSAGES[kind], {
        label: 'Retry',
        run: () => void useRecorderStart(),
      })
    }
  }, [])

  const stop = useCallback(async (): Promise<void> => {
    await recorder.stop()
    const store = useSessionStore.getState()
    if (store.status === 'recording') store.stopRecording()
  }, [])

  const saveSession = useCallback(async (): Promise<void> => {
    const result = recorder.buildSessionWav()
    if (!result) {
      useSessionStore.getState().pushToast('info', 'No audio captured yet.')
      return
    }
    triggerDownload(result.wav, `mediscript-session-${stamp()}.wav`)
    const transcript = useSessionStore.getState().transcript.trim()
    if (transcript) {
      triggerDownload(
        new Blob([transcript], { type: 'text/plain;charset=utf-8' }),
        `mediscript-session-${stamp()}.txt`,
      )
    }
    const kb = Math.round(result.wav.size / 1024)
    useSessionStore
      .getState()
      .pushToast('success', `Recording saved to downloads (${kb} KB, ${Math.round(result.durationMs / 1000)} s).`)
  }, [])

  const clearSession = useCallback((): void => {
    recorder.reset()
    useSessionStore.getState().clearTranscript()
  }, [])

  return { start, stop, saveSession, clearSession }
}

// Dev-only introspection for automated tests (rejected in production builds).
if (import.meta.env.DEV) {
  ;(window as unknown as { __mediscript: unknown }).__mediscript = { recorder, chunkUploader }
}

/** Retry path used from toast actions (needs the hook-free store API). */
function useRecorderStart(): void {
  void Promise.resolve().then(async () => {
    const store = useSessionStore.getState()
    store.startRecording()
    try {
      await recorder.start({
        onChunk: onChunkArrived,
      })
    } catch (error) {
      const kind =
        error instanceof Error && 'kind' in error
          ? (error.kind as RecorderErrorKind)
          : 'unknown'
      const failed = useSessionStore.getState()
      failed.recorderFailure(kind)
      failed.pushToast('error', ERROR_MESSAGES[kind], {
        label: 'Retry',
        run: () => useRecorderStart(),
      })
    }
  })
}
