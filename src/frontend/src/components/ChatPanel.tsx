/**
 * Chat panel with message history and streaming input.
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
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', padding: '0.75rem' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
        <h2 style={{ margin: 0, fontSize: '11px', color: '#2dd4bf', textTransform: 'uppercase' }}>
          [ TERMINAL ]
        </h2>
        <button
          onClick={clearChat}
          disabled={isStreaming}
          style={{
            background: '#134e4a',
            border: '2px solid #14b8a6',
            padding: '0.4rem 0.75rem',
            cursor: 'pointer',
            color: '#ffffff',
            fontSize: '8px',
          }}
        >
          CLEAR
        </button>
      </div>

      {/* Summary indicator */}
      <div style={{ fontSize: '8px', color: '#5eead4', marginBottom: '0.5rem' }}>
        &gt; SELECTED: {selectedCompliance.length} REGS, {selectedInternal.length} DOCS
        {requirements.length > 0 && ` | ${requirements.length} REQS`}
      </div>

      {/* Messages */}
      <div style={{
        flex: 1,
        overflowY: 'auto',
        padding: '0.75rem',
        marginBottom: '0.75rem',
        background: '#0a0a0f',
      }}>
        {messages.length === 0 && !isStreaming && (
          <p style={{ color: '#5eead4', textAlign: 'center', fontSize: '8px' }}>
            SELECT DOCS AND ASK ABOUT COMPLIANCE...
          </p>
        )}

        {messages.map((msg, index) => (
          <div
            key={index}
            style={{
              marginBottom: '0.75rem',
              display: 'flex',
              justifyContent: msg.role === 'user' ? 'flex-end' : 'flex-start',
            }}
          >
            <div
              style={{
                maxWidth: '85%',
                padding: '0.5rem 0.75rem',
                background: msg.role === 'user' ? '#14b8a6' : '#134e4a',
                color: '#ffffff',
                border: `2px solid ${msg.role === 'user' ? '#14b8a6' : '#0d9488'}`,
                borderRadius: '8px',
              }}
              className={msg.role === 'assistant' ? 'markdown-content' : ''}
            >
              {msg.role === 'user' ? (
                <span style={{ fontSize: '9px' }}>&gt; {msg.content}</span>
              ) : (
                <ReactMarkdown remarkPlugins={[remarkGfm]}>{msg.content}</ReactMarkdown>
              )}
            </div>
          </div>
        ))}

        {/* Streaming status */}
        {isStreaming && status && (
          <div style={{
            padding: '0.5rem 0.75rem',
            background: '#134e4a',
            border: '2px solid #5eead4',
            borderRadius: '8px',
            marginBottom: '0.75rem',
            fontSize: '8px',
            color: '#5eead4',
          }}>
            &gt;&gt; {status.toUpperCase()}
          </div>
        )}

        {/* Streaming content */}
        {isStreaming && streamingContent && (
          <div
            style={{
              marginBottom: '0.75rem',
              display: 'flex',
              justifyContent: 'flex-start',
            }}
          >
            <div
              style={{
                maxWidth: '85%',
                padding: '0.5rem 0.75rem',
                background: '#134e4a',
                border: '2px solid #0d9488',
                borderRadius: '8px',
              }}
              className="markdown-content"
            >
              <ReactMarkdown remarkPlugins={[remarkGfm]}>{streamingContent}</ReactMarkdown>
              <span style={{ color: '#2dd4bf', animation: 'blink 0.5s infinite' }}>_</span>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div style={{ position: 'relative' }}>
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="ENTER QUERY..."
          disabled={isStreaming}
          style={{
            width: '100%',
            padding: '1rem 3rem 1rem 1rem',
            border: '2px solid #14b8a6',
            borderRadius: '24px',
            fontSize: '11px',
            outline: 'none',
            background: '#0a0a0f',
            color: '#ffffff',
            height: '48px',
            fontFamily: 'inherit',
          }}
        />
        <button
          onClick={handleSend}
          disabled={isStreaming || !input.trim()}
          style={{
            position: 'absolute',
            right: '6px',
            top: '50%',
            transform: 'translateY(-50%)',
            width: '36px',
            height: '36px',
            border: 'none',
            borderRadius: '50%',
            background: isStreaming || !input.trim() ? '#134e4a' : '#14b8a6',
            color: '#ffffff',
            cursor: isStreaming || !input.trim() ? 'not-allowed' : 'pointer',
            fontSize: '14px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          ▲
        </button>
      </div>
    </div>
  );
}
