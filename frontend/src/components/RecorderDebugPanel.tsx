import { useSessionStore } from '../store/sessionStore'
import { Icon } from './Icon'

/**
 * Dev-only recorder debug surface (PRD Step 2: "log chunk events to a debug
 * panel and increment CHUNKS only" until Step 3 wires ASR). Renders nothing
 * in production builds.
 */
export function RecorderDebugPanel() {
  const events = useSessionStore((s) => s.recorderEvents)
  const status = useSessionStore((s) => s.status)

  const micLabel =
    status === 'recording' ? ' · mic live' : status === 'idle' ? ' · mic idle' : ''

  return (
    <details className="debug-panel">
      <summary>
        <Icon name="history" size={13} />
        Recorder debug · {events.length} chunk event{events.length === 1 ? '' : 's'}
        {micLabel}
      </summary>
      <p className="debug-hint">
        Step 3 will send each chunk below to Whisper. VAD events appear here in real time.
      </p>
      {events.length === 0 ? (
        <p className="empty">No chunk events yet — speak to create chunks.</p>
      ) : (
        <ul className="debug-list">
          {events.map((e) => (
            <li key={e.index}>
              <span className="debug-idx">#{e.index}</span>
              <span>{(e.durationMs / 1000).toFixed(2)} s</span>
              <span>{Math.round(e.sizeBytes / 1024)} KB</span>
              <span>{new Date(e.finishedAt).toLocaleTimeString()}</span>
            </li>
          ))}
        </ul>
      )}
    </details>
  )
}
