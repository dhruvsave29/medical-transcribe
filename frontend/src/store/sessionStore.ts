import { create } from 'zustand'
import { mockSummary } from '../data/mockSummary'
import { mockTranscript } from '../data/mockTranscript'
import type { ClinicalSummary } from '../types/clinical'

export type SessionStatus = 'idle' | 'recording' | 'stopped' | 'processing'
export type BackendStatus = 'checking' | 'online' | 'offline'
export type ToastKind = 'info' | 'success' | 'error'

export interface ToastAction {
  label: string
  run: () => void
}

export interface ToastItem {
  id: number
  kind: ToastKind
  message: string
  action?: ToastAction
}

const countWords = (text: string): number => {
  const trimmed = text.trim()
  if (!trimmed) return 0
  return trimmed.split(/\s+/).length
}

interface SessionState {
  status: SessionStatus
  transcript: string
  chunkCount: number
  liveLabel: string | null
  summary: ClinicalSummary | null
  summaryEditedText: string | null
  mock: boolean
  backend: BackendStatus
  toasts: ToastItem[]

  startRecording: () => void
  stopRecording: () => void
  clearTranscript: () => void
  clearSummary: () => void
  beginProcessing: () => void
  endProcessing: () => void
  setLiveLabel: (v: string | null) => void
  setMock: (v: boolean) => void
  setBackendStatus: (v: BackendStatus) => void
  refreshBackendStatus: () => Promise<void>
  setEditedSummary: (v: string) => void
  pushToast: (kind: ToastKind, message: string, action?: ToastAction) => void
  dismissToast: (id: number) => void
}

let toastSeq = 0

export const useSessionStore = create<SessionState>((set, get) => ({
  status: 'idle',
  transcript: '',
  chunkCount: 0,
  liveLabel: null,
  summary: null,
  summaryEditedText: null,
  mock: false,
  backend: 'checking',
  toasts: [],

  startRecording: () => {
    if (get().status === 'processing') return
    set({ status: 'recording', liveLabel: 'Listening…' })
  },

  stopRecording: () => {
    if (get().status !== 'recording') return
    set({ status: 'stopped', liveLabel: null })
  },

  clearTranscript: () => {
    set({
      status: 'idle',
      transcript: '',
      chunkCount: 0,
      liveLabel: null,
    })
  },

  clearSummary: () => {
    set({ summary: null, summaryEditedText: null })
  },

  beginProcessing: () => {
    set({ status: 'processing', liveLabel: 'Analysing…' })
  },

  endProcessing: () => {
    set({ status: 'stopped', liveLabel: null })
  },

  setLiveLabel: (v) => set({ liveLabel: v }),

  setMock: (v) => {
    if (v) {
      set({
        mock: true,
        transcript: mockTranscript,
        chunkCount: 15,
        status: 'stopped',
        liveLabel: null,
        summary: mockSummary,
        summaryEditedText: null,
      })
      return
    }
    set({
      mock: false,
      transcript: '',
      chunkCount: 0,
      status: 'idle',
      liveLabel: null,
      summary: null,
      summaryEditedText: null,
    })
  },

  setBackendStatus: (v) => set({ backend: v }),

  setEditedSummary: (v) => set({ summaryEditedText: v }),

  pushToast: (kind, message, action) => {
    const id = ++toastSeq
    set((s) => ({ toasts: [...s.toasts, { id, kind, message, action }] }))
  },

  dismissToast: (id) => {
    set((s) => ({ toasts: s.toasts.filter((t) => t.id !== id) }))
  },

  refreshBackendStatus: async () => {
    if (get().backend === 'online') return
    try {
      const res = await fetch('/api/health')
      const body = (await res.json()) as { status?: string }
      set({ backend: body.status === 'ok' ? 'online' : 'offline' })
    } catch {
      set({ backend: 'offline' })
    }
  },
}))

export const wordCountOf = countWords
