import { useEffect, useRef, useState } from 'react'
import { Icon } from './Icon'
import { useSessionStore } from '../store/sessionStore'
import { ApiError, chatWithAssistant } from '../lib/api'

/**
 * Floating assistant chat (PRD 2.3): /api/chat answers strictly from the
 * current transcript + summary. Errors toast with a Retry that re-sends the
 * last message. The drawer keeps its messages in the store until Clear.
 */
export function FloatingChatButton() {
  const [open, setOpen] = useState(false)
  const [draft, setDraft] = useState('')
  const messages = useSessionStore((s) => s.chatMessages)
  const busy = useSessionStore((s) => s.chatBusy)
  const transcript = useSessionStore((s) => s.transcript)

  const bodyRef = useRef<HTMLDivElement>(null)
  const hasTranscript = transcript.trim().length > 0

  useEffect(() => {
    const el = bodyRef.current
    if (el) el.scrollTop = el.scrollHeight
  }, [messages.length, busy, open])

  const send = async (text: string): Promise<void> => {
    const message = text.trim()
    if (!message || busy || !hasTranscript) return
    const store = useSessionStore.getState()
    store.addChatMessage('user', message)
    store.setChatBusy(true)
    setDraft('')
    try {
      const reply = await chatWithAssistant(
        useSessionStore.getState().transcript,
        useSessionStore.getState().summary,
        message,
      )
      useSessionStore.getState().addChatMessage('assistant', reply)
    } catch (error) {
      const detail =
        error instanceof ApiError ? error.message : 'Chat request failed.'
      useSessionStore.getState().pushToast('error', detail, {
        label: 'Retry',
        run: () => void send(message),
      })
      setDraft(message)
    } finally {
      useSessionStore.getState().setChatBusy(false)
    }
  }

  const onKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      void send(draft)
    }
  }

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
          <div className="chat-drawer__body" ref={bodyRef}>
            {messages.length === 0 && (
              <p className="chat-drawer__hint">
                {hasTranscript
                  ? 'Ask anything from this consultation — answers come only from the transcript and the current summary.'
                  : 'Record a consultation (or load the demo transcript) first, then ask questions here.'}
              </p>
            )}
            {messages.map((m, i) => (
              <div key={i} className={`chat-msg chat-msg--${m.role}`}>
                {m.content}
              </div>
            ))}
            {busy && <div className="chat-msg chat-msg--assistant is-typing">Thinking…</div>}
          </div>
          <div className="chat-drawer__input">
            <button
              type="button"
              className="chat-drawer__input icon-button icon-button--micro"
              aria-label="Clear assistant chat"
              title="Clear chat"
              onClick={() => useSessionStore.getState().clearChat()}
            >
              <Icon name="trash" size={14} />
            </button>
            <textarea
              rows={1}
              value={draft}
              placeholder={
                hasTranscript ? 'Ask about the consultation…' : 'Transcript is empty…'
              }
              disabled={!hasTranscript || busy}
              aria-label="Message for the assistant"
              onChange={(e) => setDraft(e.target.value)}
              onKeyDown={onKeyDown}
            />
            <button
              type="button"
              className="btn btn--primary chat-drawer__send"
              disabled={!draft.trim() || busy || !hasTranscript}
              aria-label="Send message to the assistant"
              onClick={() => void send(draft)}
            >
              <Icon name="zap" size={16} className="btn__icon" />
              Send
            </button>
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
