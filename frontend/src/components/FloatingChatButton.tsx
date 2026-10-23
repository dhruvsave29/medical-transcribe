import { useState } from 'react'
import { Icon } from './Icon'

/**
 * Floating assistant entry point. The working chat drawer itself is built in
 * Step 5; until then the drawer opens and states that clearly. This is a
 * documented known gap for Step 1, not a hidden dead button.
 */
export function FloatingChatButton() {
  const [open, setOpen] = useState(false)

  return (
    <>
      {open && (
        <aside
          className="chat-drawer"
          role="dialog"
          aria-label="Assistant chat drawer"
          onKeyDown={(e) => {
            if (e.key === 'Escape') setOpen(false)
          }}
        >
          <div className="chat-drawer__header">
            <Icon name="chat" size={18} />
            Ask about this consultation
            <span className="spacer" style={{ flex: 1 }} />
            <button
              type="button"
              className="toast__close"
              style={{ color: 'var(--text-secondary)', opacity: 1 }}
              aria-label="Close assistant drawer"
              onClick={() => setOpen(false)}
            >
              <Icon name="x" size={16} />
            </button>
          </div>
          <div className="chat-drawer__body">
            The transcript-aware assistant chat is activated in Step 5 of the
            build plan. Questions will be answered strictly from the current
            transcript and summary.
          </div>
          <div className="chat-drawer__input">
            <textarea
              rows={1}
              disabled
              placeholder="Assistant chat comes online in Step 5…"
              aria-label="Message for the assistant (disabled until Step 5)"
            />
          </div>
        </aside>
      )}
      <button
        type="button"
        className="fab"
        aria-label={open ? 'Close assistant drawer' : 'Open assistant drawer'}
        aria-expanded={open}
        onClick={() => setOpen((v) => !v)}
      >
        <Icon name={open ? 'x' : 'chat'} size={24} />
      </button>
    </>
  )
}
