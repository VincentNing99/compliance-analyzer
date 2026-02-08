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
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', padding: '1rem' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
        <h2 style={{ margin: 0 }}>Chat</h2>
        <button
          onClick={clearChat}
          disabled={isStreaming}
          style={{
            background: '#f3f4f6',
            border: 'none',
            borderRadius: '0.5rem',
            padding: '0.5rem 1rem',
            cursor: 'pointer',
          }}
        >
          Clear
        </button>
      </div>

      {/* Summary indicator */}
      <div style={{ fontSize: '0.875rem', color: '#666', marginBottom: '0.5rem' }}>
        Selected: {selectedCompliance.length} compliance, {selectedInternal.length} internal docs
        {requirements.length > 0 && ` | ${requirements.length} requirements extracted`}
      </div>

      {/* Messages */}
      <div style={{
        flex: 1,
        overflowY: 'auto',
        border: '1px solid #e5e7eb',
        borderRadius: '0.5rem',
        padding: '1rem',
        marginBottom: '1rem',
        background: '#fafafa',
      }}>
        {messages.length === 0 && !isStreaming && (
          <p style={{ color: '#666', textAlign: 'center' }}>
            Select documents and ask about compliance requirements...
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
                maxWidth: '80%',
                padding: '0.75rem 1rem',
                borderRadius: msg.role === 'user' ? '1rem 1rem 0.25rem 1rem' : '1rem 1rem 1rem 0.25rem',
                background: msg.role === 'user' ? '#4f46e5' : 'white',
                color: msg.role === 'user' ? 'white' : 'black',
                border: msg.role === 'user' ? 'none' : '1px solid #e5e7eb',
              }}
              className={msg.role === 'assistant' ? 'markdown-content' : ''}
            >
              {msg.role === 'user' ? msg.content : <ReactMarkdown remarkPlugins={[remarkGfm]}>{msg.content}</ReactMarkdown>}
            </div>
          </div>
        ))}

        {/* Streaming status */}
        {isStreaming && status && (
          <div style={{
            padding: '0.5rem 1rem',
            background: '#e0f2fe',
            borderRadius: '0.5rem',
            marginBottom: '1rem',
            fontSize: '0.875rem',
            color: '#0369a1',
          }}>
            {status}
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
                maxWidth: '80%',
                padding: '0.75rem 1rem',
                borderRadius: '1rem 1rem 1rem 0.25rem',
                background: 'white',
                border: '1px solid #e5e7eb',
              }}
              className="markdown-content"
            >
              <ReactMarkdown remarkPlugins={[remarkGfm]}>{streamingContent}</ReactMarkdown>
              <span style={{ animation: 'blink 1s infinite' }}>|</span>
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
          placeholder="Ask about compliance requirements..."
          disabled={isStreaming}
          style={{
            width: '100%',
            padding: '1rem 3.5rem 1rem 1.25rem',
            borderRadius: '1.5rem',
            border: '2px solid #e5e7eb',
            fontSize: '1rem',
            outline: 'none',
            height: '56px',
          }}
        />
        <button
          onClick={handleSend}
          disabled={isStreaming || !input.trim()}
          style={{
            position: 'absolute',
            right: '8px',
            top: '50%',
            transform: 'translateY(-50%)',
            width: '40px',
            height: '40px',
            borderRadius: '50%',
            border: 'none',
            background: isStreaming || !input.trim() ? '#e5e7eb' : '#4f46e5',
            color: 'white',
            cursor: isStreaming || !input.trim() ? 'not-allowed' : 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: '1.25rem',
          }}
        >
          ↑
        </button>
      </div>
    </div>
  );
}
