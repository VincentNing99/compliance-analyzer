/**
 * Compliance Auditor - React Frontend
 *
 * Two-panel layout: Documents (left) and Chat (right)
 * Medieval Parchment Theme
 */
import { useState } from 'react';
import { DocumentPanel } from './components/DocumentPanel';
import { ChatPanel } from './components/ChatPanel';

function App() {
  // Document selection state (shared between panels)
  const [selectedCompliance, setSelectedCompliance] = useState<string[]>([]);
  const [selectedInternal, setSelectedInternal] = useState<string[]>([]);

  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      height: '100vh',
      fontFamily: "'Crimson Text', Georgia, serif",
      background: '#0d0a08',
    }}>
      {/* Header - Dark Elder Scrolls Banner */}
      <header style={{
        padding: '1.25rem 2rem',
        background: 'linear-gradient(180deg, #1a1410 0%, #0d0a08 100%)',
        borderBottom: '3px solid #c9a227',
        boxShadow: '0 4px 16px rgba(0,0,0,0.6)',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          {/* Crystal ball */}
          <span style={{ fontSize: '1.8rem' }}>&#128302;</span>
          <h1 style={{
            margin: 0,
            fontFamily: "'Cinzel', serif",
            fontSize: '1.75rem',
            fontWeight: 700,
            color: '#ffd700',
            letterSpacing: '0.08em',
            textShadow: '0 0 10px rgba(255,215,0,0.4), 2px 2px 4px rgba(0,0,0,0.8)',
          }}>
            Compliance Auditor
          </h1>
        </div>
        <p style={{
          margin: '0.5rem 0 0 0',
          color: '#a89070',
          fontSize: '0.95rem',
          fontStyle: 'italic',
          textShadow: '1px 1px 2px rgba(0,0,0,0.5)',
        }}>
          Analyze thy documents against the decrees of the realm
        </p>
      </header>

      {/* Main content - split panel */}
      <main style={{
        flex: 1,
        display: 'flex',
        overflow: 'hidden',
        background: '#0d0a08',
      }}>
        {/* Left Panel - Documents (Dark aged leather) */}
        <div style={{
          width: '340px',
          overflow: 'auto',
          background: 'linear-gradient(180deg, #1a1410 0%, #12100c 100%)',
          borderRight: '2px solid #4a3828',
          boxShadow: '2px 0 12px rgba(0,0,0,0.5)',
        }}>
          <DocumentPanel
            selectedCompliance={selectedCompliance}
            setSelectedCompliance={setSelectedCompliance}
            selectedInternal={selectedInternal}
            setSelectedInternal={setSelectedInternal}
          />
        </div>

        {/* Right Panel - Chat (Dark parchment) */}
        <div style={{
          flex: 1,
          overflow: 'auto',
          background: 'linear-gradient(180deg, #1a1410 0%, #12100c 100%)',
        }}>
          <ChatPanel
            selectedCompliance={selectedCompliance}
            selectedInternal={selectedInternal}
          />
        </div>
      </main>
    </div>
  );
}

export default App;
