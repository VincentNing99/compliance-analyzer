/**
 * Chat panel with message history and streaming input.
 * Medieval Parchment Theme
 */
import { useState, useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { useChat } from '../hooks/useChat';

interface ChatPanelProps {
  selectedCompliance: string[];
  selectedInternal: string[];
}

export function ChatPanel({ selectedCompliance, selectedInternal }: ChatPanelProps) {
  const {
    messages,
    isStreaming,
    streamingContent,
    status,
    requirements,
    sendMessage,
    clearChat,
  } = useChat();

  const [input, setInput] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, streamingContent]);

  const handleSend = async () => {
    if (!input.trim() || isStreaming) return;

    const message = input.trim();
    setInput('');
    await sendMessage(message, selectedCompliance, selectedInternal);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', padding: '1rem' }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
        <h2 style={{
          margin: 0,
          fontFamily: "'Cinzel', serif",
          fontSize: '1.1rem',
          color: '#ffd700',
          display: 'flex',
          alignItems: 'center',
          gap: '0.5rem',
          textShadow: '0 0 8px rgba(255,215,0,0.3), 1px 1px 2px rgba(0,0,0,0.8)',
        }}>
          <span style={{ color: '#c9a227' }}>&#9733;</span> Adjudgement
        </h2>
        <button
          onClick={clearChat}
          disabled={isStreaming}
          style={{
            background: 'linear-gradient(180deg, #2a2018 0%, #1a1410 100%)',
            border: '2px solid #4a3828',
            padding: '0.5rem 0.85rem',
            cursor: isStreaming ? 'not-allowed' : 'pointer',
            color: '#c9a227',
            fontFamily: "'Cinzel', serif",
            fontSize: '0.8rem',
            borderRadius: '4px',
            boxShadow: '0 2px 6px rgba(0,0,0,0.5)',
            textShadow: '0 1px 2px rgba(0,0,0,0.5)',
          }}
        >
          Clear
        </button>
      </div>

      {/* Summary indicator */}
      <div style={{
        fontSize: '0.85rem',
        color: '#a89070',
        marginBottom: '0.75rem',
        fontStyle: 'italic',
        fontFamily: "'Cinzel', serif",
        borderBottom: '2px solid #4a3828',
        paddingBottom: '0.5rem',
      }}>
        <span style={{ color: '#c9a227' }}>&#9670;</span> {selectedCompliance.length} decrees and {selectedInternal.length} scrolls selected
        {requirements.length > 0 && ` | ${requirements.length} requirements found`}
      </div>

      {/* Messages */}
      <div style={{
        flex: 1,
        overflowY: 'auto',
        padding: '1rem',
        marginBottom: '1rem',
        background: 'linear-gradient(180deg, #0d0a08 0%, #1a1410 50%, #0d0a08 100%)',
        border: '2px solid #4a3828',
        borderRadius: '6px',
        boxShadow: 'inset 0 2px 12px rgba(0,0,0,0.5), 0 2px 4px rgba(0,0,0,0.3)',
      }}>
        {messages.length === 0 && !isStreaming && (
          <p style={{ color: '#a89070', textAlign: 'center', fontStyle: 'italic', fontFamily: "'Cinzel', serif" }}>
            Select thy documents and pose thy question to the Oracle...
          </p>
        )}

        {messages.map((msg, index) => (
          <div
            key={index}
            style={{
              marginBottom: '1rem',
              display: 'flex',
              justifyContent: msg.role === 'user' ? 'flex-end' : 'flex-start',
            }}
          >
            <div
              style={{
                maxWidth: '85%',
                padding: '0.75rem 1rem',
                background: msg.role === 'user'
                  ? 'linear-gradient(180deg, #2a2018 0%, #1a1410 100%)'
                  : 'linear-gradient(180deg, #1a1410 0%, #12100c 100%)',
                color: msg.role === 'user' ? '#ffd700' : '#d4c4a8',
                border: msg.role === 'user' ? '2px solid #4a3828' : '2px solid #c9a227',
                borderRadius: msg.role === 'user' ? '12px 12px 2px 12px' : '12px 12px 12px 2px',
                boxShadow: msg.role === 'user'
                  ? '0 2px 8px rgba(0,0,0,0.5)'
                  : '0 0 12px rgba(201,162,39,0.2), 0 2px 8px rgba(0,0,0,0.4)',
                textShadow: msg.role === 'user' ? '0 1px 2px rgba(0,0,0,0.5)' : 'none',
              }}
              className={msg.role === 'assistant' ? 'markdown-content' : ''}
            >
              {msg.role === 'user' ? (
                <span style={{ fontStyle: 'italic' }}>"{msg.content}"</span>
              ) : (
                <ReactMarkdown remarkPlugins={[remarkGfm]}>{msg.content}</ReactMarkdown>
              )}
            </div>
          </div>
        ))}

        {/* Streaming status */}
        {isStreaming && status && (
          <div style={{
            padding: '0.6rem 1rem',
            background: 'rgba(201,162,39,0.1)',
            border: '2px dashed #4a3828',
            borderRadius: '6px',
            marginBottom: '1rem',
            fontSize: '0.9rem',
            color: '#c9a227',
            fontStyle: 'italic',
            fontFamily: "'Cinzel', serif",
          }}>
            &#8987; {status}...
          </div>
        )}

        {/* Streaming content */}
        {isStreaming && streamingContent && (
          <div
            style={{
              marginBottom: '1rem',
              display: 'flex',
              justifyContent: 'flex-start',
            }}
          >
            <div
              style={{
                maxWidth: '85%',
                padding: '0.75rem 1rem',
                background: 'linear-gradient(180deg, #1a1410 0%, #12100c 100%)',
                border: '2px solid #c9a227',
                borderRadius: '12px 12px 12px 2px',
                boxShadow: '0 0 12px rgba(201,162,39,0.2), 0 2px 8px rgba(0,0,0,0.4)',
              }}
              className="markdown-content"
            >
              <ReactMarkdown remarkPlugins={[remarkGfm]}>{streamingContent}</ReactMarkdown>
              <span style={{ color: '#c9a227', animation: 'blink 0.7s infinite' }}>&#9618;</span>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input - Dark scroll style with send button */}
      <div style={{ position: 'relative' }}>
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Inscribe thy query..."
          disabled={isStreaming}
          style={{
            width: '100%',
            padding: '1rem 3.5rem 1rem 1.25rem',
            border: '2px solid #4a3828',
            borderRadius: '24px',
            fontSize: '1rem',
            outline: 'none',
            background: 'linear-gradient(180deg, #1a1410 0%, #12100c 100%)',
            color: '#d4c4a8',
            height: '56px',
            fontFamily: "'Crimson Text', Georgia, serif",
            boxShadow: 'inset 0 2px 8px rgba(0,0,0,0.4), 0 2px 4px rgba(0,0,0,0.3)',
          }}
        />
        <button
          onClick={handleSend}
          disabled={isStreaming || !input.trim()}
          title="Send thy message"
          style={{
            position: 'absolute',
            right: '8px',
            top: '50%',
            transform: 'translateY(-50%)',
            width: '42px',
            height: '42px',
            border: '2px solid #4a3828',
            borderRadius: '50%',
            background: isStreaming || !input.trim()
              ? 'linear-gradient(180deg, #2a2018 0%, #1a1410 100%)'
              : 'linear-gradient(180deg, #722f37 0%, #4a1c24 100%)',
            color: isStreaming || !input.trim() ? '#5a4a38' : '#ffd700',
            cursor: isStreaming || !input.trim() ? 'not-allowed' : 'pointer',
            fontSize: '1.3rem',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: isStreaming || !input.trim()
              ? '0 2px 6px rgba(0,0,0,0.4)'
              : '0 0 12px rgba(139,0,0,0.5), 0 2px 6px rgba(0,0,0,0.5)',
            textShadow: isStreaming || !input.trim() ? 'none' : '0 0 6px rgba(255,215,0,0.4)',
          }}
        >
          &#10148;
        </button>
      </div>
    </div>
  );
}
