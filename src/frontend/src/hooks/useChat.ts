/**
 * Custom hook for chat functionality with SSE streaming.
 */
import { useState, useCallback, useRef } from 'react';
import { streamChat } from '../api/client';
import type { ChatMessage } from '../api/client';

interface RequirementResult {
  requirement: string;
  compliance_info: string;
}

interface UseChatReturn {
  messages: ChatMessage[];
  isStreaming: boolean;
  streamingContent: string;
  status: string;
  requirements: string[];
  complianceResults: RequirementResult[];
  sendMessage: (message: string, selectedCompliance: string[], selectedInternal: string[]) => Promise<void>;
  clearChat: () => void;
}

export function useChat(): UseChatReturn {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [streamingContent, setStreamingContent] = useState('');
  const [status, setStatus] = useState('');
  const [requirements, setRequirements] = useState<string[]>([]);
  const [complianceResults, setComplianceResults] = useState<RequirementResult[]>([]);

  // Use ref to accumulate streaming content (avoids stale closure issues)
  const contentRef = useRef('');

  const sendMessage = useCallback(async (
    message: string,
    selectedCompliance: string[],
    selectedInternal: string[]
  ) => {
    // Add user message to history
    const userMessage: ChatMessage = { role: 'user', content: message };
    setMessages(prev => [...prev, userMessage]);

    // Reset streaming state
    setIsStreaming(true);
    setStreamingContent('');
    setStatus('');
    setRequirements([]);
    setComplianceResults([]);
    contentRef.current = '';

    try {
      await streamChat(
        {
          message,
          chat_history: messages,
          selected_compliance: selectedCompliance,
          selected_internal: selectedInternal,
        },
        {
          onStatus: (statusMsg) => {
            setStatus(statusMsg);
          },
          onRequirements: (reqs, results) => {
            setRequirements(reqs);
            setComplianceResults(results);
          },
          onToken: (token) => {
            contentRef.current += token;
            setStreamingContent(contentRef.current);
          },
          onDone: () => {
            // Add assistant message to history
            if (contentRef.current) {
              const assistantMessage: ChatMessage = {
                role: 'assistant',
                content: contentRef.current
              };
              setMessages(prev => [...prev, assistantMessage]);
            }
            setIsStreaming(false);
            setStreamingContent('');
            setStatus('');
          },
          onError: (error) => {
            console.error('Chat error:', error);
            setStatus(`Error: ${error}`);
            setIsStreaming(false);
          }
        }
      );
    } catch (e) {
      console.error('Chat failed:', e);
      setStatus(`Error: ${e instanceof Error ? e.message : 'Unknown error'}`);
      setIsStreaming(false);
    }
  }, [messages]);

  const clearChat = useCallback(() => {
    setMessages([]);
    setStreamingContent('');
    setStatus('');
    setRequirements([]);
    setComplianceResults([]);
  }, []);

  return {
    messages,
    isStreaming,
    streamingContent,
    status,
    requirements,
    complianceResults,
    sendMessage,
    clearChat
  };
}
