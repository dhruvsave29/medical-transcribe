import { useSessionStore } from '../store/sessionStore'
import { Icon } from './Icon'

const HOST = 'MediScript Demo Clinic'

export function AppShell() {
  const backend = useSessionStore((s) => s.backend)
  const mock = useSessionStore((s) => s.mock)
  const setMock = useSessionStore((s) => s.setMock)

  const dotClass =
    backend === 'checking' ? 'is-checking' : backend === 'online' ? 'is-online' : 'is-offline'
  const statusText =
    backend === 'online'
      ? 'Local services online'
      : backend === 'checking'
        ? 'Checking local services'
        : 'Local services offline'

  return (
    <header className="topbar">
      <div className="topbar__left">
        <span className="brand-badge" aria-hidden="true">
          <Icon name="pulse" size={18} />
        </span>
        <span className="brand-name">MediScript</span>
      </div>
      <div className="topbar__right">
        {import.meta.env.DEV && (
          <button
            type="button"
            className={`demo-toggle${mock ? ' is-on' : ''}`}
            aria-pressed={mock}
            onClick={() => setMock(!mock)}
            title="Fill the app with a sample consultation (dev builds only)"
          >
            Demo data
          </button>
        )}
        <span className={`status-pill ${dotClass}`} role="status">
          <span className="status-dot" aria-hidden="true" />
          {statusText}
        </span>
        <span className="hospital-name">{HOST}</span>
      </div>
    </header>
  )
}
