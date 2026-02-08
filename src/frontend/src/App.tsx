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
      fontFamily: 'system-ui, -apple-system, sans-serif',
    }}>
      {/* Header */}
      <header style={{
        padding: '1rem 2rem',
        background: '#f8fafc',
      }}>
        <h1 style={{
          margin: 0,
          fontSize: '1.5rem',
          color: '#4f46e5',
        }}>
          Compliance Auditor
        </h1>
        <p style={{ margin: '0.25rem 0 0 0', color: '#64748b', fontSize: '0.875rem' }}>
          Analyze documents against regulatory requirements with AI
        </p>
      </header>

      {/* Main content - split panel */}
      <main style={{
        flex: 1,
        display: 'flex',
        overflow: 'hidden',
      }}>
        {/* Left Panel - Documents */}
        <div style={{
          width: '350px',
          overflow: 'auto',
          background: '#f8fafc',
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
