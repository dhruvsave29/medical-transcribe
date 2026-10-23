import { useEffect, useRef, useState } from 'react'
import { useSessionStore, wordCountOf } from '../store/sessionStore'
import { useRecorder } from '../hooks/useRecorder'
import { analyzeTranscript, ApiError } from '../lib/api'
import { RecorderDebugPanel } from './RecorderDebugPanel'
import { Icon } from './Icon'

export function TranscriptionCard() {
  const status = useSessionStore((s) => s.status)
  const transcript = useSessionStore((s) => s.transcript)
  const chunkCount = useSessionStore((s) => s.chunkCount)
  const liveLabel = useSessionStore((s) => s.liveLabel)
  const audioCaptured = useSessionStore((s) => s.audioCaptured)
  const beginProcessing = useSessionStore((s) => s.beginProcessing)
  const endProcessing = useSessionStore((s) => s.endProcessing)
  const pushToast = useSessionStore((s) => s.pushToast)

  const { start, stop, saveSession, clearSession } = useRecorder()

  const boxRef = useRef<HTMLDivElement>(null)
  const [confirmingClear, setConfirmingClear] = useState(false)

  const words = wordCountOf(transcript)
  const hasText = transcript.trim().length > 0

  useEffect(() => {
    const el = boxRef.current
    if (el) el.scrollTop = el.scrollHeight
  }, [transcript])

  const onClear = () => {
    if (status === 'recording') return
    const willWipe = hasText || chunkCount > 0
    if (!willWipe) {
      clearSession()
      return
    }
    if (!confirmingClear) {
      setConfirmingClear(true)
      window.setTimeout(() => setConfirmingClear(false), 4000)
      return
    }
    setConfirmingClear(false)
    clearSession()
    pushToast('success', 'Transcript and recording cleared.')
  }

  const onProcess = async () => {
    if (!hasText) return
    beginProcessing()
    try {
      const summary = await analyzeTranscript(useSessionStore.getState().transcript)
      useSessionStore.setState({ summary, summaryEditedText: null })
      endProcessing()
      pushToast('success', 'Clinical summary ready.')
    } catch (error) {
      endProcessing()
      const message = error instanceof ApiError ? error.message : 'Analysis failed.'
      const offline = error instanceof ApiError && error.status === 0
      pushToast(
        'error',
        offline ? 'Backend not reachable. Start it with run.bat (Windows) or run.sh.' : message,
        {
          label: 'Retry',
          run: () => void onProcess(),
        },
      )
    }
  }

  const stripVisible = status === 'recording' || status === 'processing'
  const liveStrip = status === 'processing' ? 'Analysing…' : liveLabel
  const canProcess = (status === 'stopped' || status === 'error') && hasText

  return (
    <section className="card" aria-labelledby="transcription-title">
      <div className="card__title">
        <Icon name="mic" size={22} />
        <h2 id="transcription-title">Live Medical Transcription</h2>
      </div>

      <div className="controls">
        <button
          type="button"
          className={`btn btn--primary${status === 'recording' ? ' btn--recording' : ''}`}
          onClick={() => void start()}
          disabled={status === 'recording' || status === 'processing'}
          aria-label="Start microphone recording"
        >
          <Icon name="mic" size={16} className="btn__icon" />
          {status === 'recording' ? 'Recording…' : 'Start Mic'}
        </button>
        <button
          type="button"
          className="btn btn--danger"
          onClick={() => void stop()}
          disabled={status !== 'recording'}
          aria-label="Stop recording"
        >
          <Icon name="stop" size={16} className="btn__icon" />
          Stop
        </button>
        <button
          type="button"
          className="btn btn--muted"
          onClick={onClear}
          disabled={status === 'recording' || status === 'processing'}
          aria-label="Clear transcript and counters"
          title={confirmingClear ? 'Click again to confirm' : 'Clear transcript and counters'}
        >
          <Icon name="trash" size={16} className="btn__icon" />
          {confirmingClear ? 'Confirm clear?' : 'Clear'}
        </button>
        <button
          type="button"
          className="btn btn--success"
          onClick={() => void saveSession()}
          disabled={!audioCaptured || status === 'recording' || status === 'processing'}
          aria-label="Save recording as WAV"
          title="Downloads the full session as a 16 kHz WAV (plus transcript .txt when available)"
        >
          <Icon name="download" size={16} className="btn__icon" />
          Save Recording
        </button>
      </div>

      <div className="chips">
        <span className="chip">Words: {words}</span>
        <span className="chip">Chunks: {chunkCount}</span>
      </div>

      {stripVisible && (
        <div className={`live-strip${liveStrip === 'Listening…' ? '' : ' is-quiet'}`} role="status">
          <span className="live-strip__dot" aria-hidden="true" />
          {liveStrip ?? 'Listening…'}
        </div>
      )}

      <div
        ref={boxRef}
        className="transcript-box"
        aria-live="polite"
        aria-label="Live transcript"
      >
        {hasText ? (
          transcript
        ) : (
          <div className="transcript-placeholder">
            <Icon name="wand" size={16} />
            <span>
              Ready — click Start Mic and speak naturally. VAD will auto-chunk your speech.
            </span>
          </div>
        )}
      </div>

      {import.meta.env.DEV && <RecorderDebugPanel />}

      <button
        type="button"
        className={`btn btn--primary btn--block${status === 'processing' ? ' btn--busy' : ''}`}
        onClick={() => void onProcess()}
        disabled={!canProcess}
        aria-label="Process transcript with AI"
      >
        {status === 'processing' ? (
          <>
            <span className="spinner" aria-hidden="true" />
            Analysing…
          </>
        ) : (
          <>
            <Icon name="zap" size={16} className="btn__icon" />
            Process Transcript with AI
          </>
        )}
      </button>
    </section>
  )
}
