import { useEffect } from 'react'
import { useSessionStore, type ToastItem } from '../store/sessionStore'
import { Icon } from './Icon'

function Toast({ item }: { item: ToastItem }) {
  const dismissToast = useSessionStore((s) => s.dismissToast)

  useEffect(() => {
    const timer = window.setTimeout(() => dismissToast(item.id), 6500)
    return () => window.clearTimeout(timer)
  }, [item.id, dismissToast])

  return (
    <div className={`toast toast--${item.kind}`} role="status">
      <Icon
        name={item.kind === 'error' ? 'alert' : item.kind === 'success' ? 'check' : 'info'}
        size={16}
      />
      <span>{item.message}</span>
      {item.action && (
        <button
          type="button"
          className="toast__action"
          onClick={() => {
            item.action?.run()
            dismissToast(item.id)
          }}
        >
          {item.action.label}
        </button>
      )}
      <button
        type="button"
        className="toast__close"
        aria-label="Dismiss notification"
        onClick={() => dismissToast(item.id)}
      >
        <Icon name="x" size={14} />
      </button>
    </div>
  )
}

export function Toaster() {
  const toasts = useSessionStore((s) => s.toasts)

  return (
    <div className="toaster" aria-live="polite">
      {toasts.map((t) => (
        <Toast key={t.id} item={t} />
      ))}
    </div>
  )
}
