import { useEffect } from 'react'
import { AppShell } from './components/AppShell'
import { TranscriptionCard } from './components/TranscriptionCard'
import { SummaryCard } from './components/SummaryCard'
import { FloatingChatButton } from './components/FloatingChatButton'
import { Toaster } from './components/Toaster'
import { useSessionStore } from './store/sessionStore'

export default function App() {
  const refreshBackendStatus = useSessionStore((s) => s.refreshBackendStatus)

  useEffect(() => {
    void refreshBackendStatus()
  }, [refreshBackendStatus])

  return (
    <div className="page">
      <AppShell />
      <main className="board" id="main">
        <div className="card-shell">
          <TranscriptionCard />
          <SummaryCard />
        </div>
      </main>
      <FloatingChatButton />
      <Toaster />
    </div>
  )
}
