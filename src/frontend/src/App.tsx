/**
 * Compliance Auditor - React Frontend
 *
 * Two-panel layout: Documents (left) and Chat (right)
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
    }}>
      {/* Header */}
      <header style={{
        padding: '1rem 1.5rem',
        background: '#0a1a1a',
      }}>
        <h1 style={{
          margin: 0,
          fontSize: '14px',
          color: '#2dd4bf',
          textShadow: '2px 2px 0 #0d9488',
        }}>
          COMPLIANCE AUDITOR
        </h1>
        <p style={{ margin: '0.5rem 0 0 0', color: '#5eead4', fontSize: '8px' }}>
          ANALYZE DOCS VS REGULATIONS WITH AI
        </p>
      </header>

      {/* Main content - split panel */}
      <main style={{
        flex: 1,
        display: 'flex',
        overflow: 'hidden',
        background: '#0a0a0f',
      }}>
        {/* Left Panel - Documents */}
        <div style={{
          width: '320px',
          overflow: 'auto',
          background: '#0a1a1a',
        }}>
          <DocumentPanel
            selectedCompliance={selectedCompliance}
            setSelectedCompliance={setSelectedCompliance}
            selectedInternal={selectedInternal}
            setSelectedInternal={setSelectedInternal}
          />
        </div>

        {/* Right Panel - Chat */}
        <div style={{
          flex: 1,
          overflow: 'auto',
          background: '#0a0a0f',
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
