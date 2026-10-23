/**
 * ChunkUploader — serial /api/transcribe upload queue (PRD Step 3).
 *
 * VAD closes speech segments while the mic keeps recording; uploads run
 * one-at-a-time so transcript order matches chunk order exactly. A failed
 * chunk surfaces a toast with a Retry action that re-posts the held WAV.
 */

import type { ChunkWithWav } from '../audio/recorder'
import { useSessionStore } from '../store/sessionStore'
import { ApiError, transcribeChunk } from './api'

const BACKEND_MESSAGE: Partial<Record<number, string>> = {
  0: 'Backend not reachable — start it and retry the chunk.',
  413: 'Chunk too large to transcribe.',
  415: 'Chunk audio was not decodable — it was skipped by the recogniser.',
  503: 'Transcription service unavailable — retry.',
}

export class ChunkUploader {
  private queue: ChunkWithWav[] = []
  private pumping = false

  get pending(): number {
    return this.queue.length
  }

  enqueue(chunk: ChunkWithWav): void {
    this.queue.push(chunk)
    void this.pump()
  }

  private retry(chunk: ChunkWithWav): void {
    this.queue.unshift(chunk)
    void this.pump()
  }

  private async pump(): Promise<void> {
    if (this.pumping) return
    this.pumping = true
    try {
      while (this.queue.length > 0) {
        const chunk = this.queue[0]
        const store = useSessionStore.getState()
        const wasRecording = store.status === 'recording'
        store.setLiveLabel('Transcribing…')
        try {
          const result = await transcribeChunk(chunk.wav, chunk.record.index)
          if (result.text) useSessionStore.getState().appendTranscript(result.text)
        } catch (error) {
          const message =
            error instanceof ApiError
              ? (BACKEND_MESSAGE[error.status] ?? error.message)
              : 'Transcription failed — network error.'
          useSessionStore.getState().pushToast('error', `Chunk ${chunk.record.index}: ${message}`, {
            label: 'Retry',
            run: () => this.retry(chunk),
          })
        } finally {
          this.queue.shift()
        }
        if (wasRecording && this.queue.length === 0 && useSessionStore.getState().status === 'recording') {
          useSessionStore.getState().setLiveLabel('Listening…')
        }
      }
    } finally {
      this.pumping = false
    }
  }
}

export const chunkUploader = new ChunkUploader()
