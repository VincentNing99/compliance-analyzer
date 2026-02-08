/**
 * API client for Compliance Auditor backend.
 *
 * Handles document CRUD and chat streaming via Server-Sent Events.
 */

// Types
export type DocType = 'regulation' | 'company_doc';

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
}

export interface ChatRequest {
  message: string;
  chat_history: ChatMessage[];
  selected_compliance: string[];
  selected_internal: string[];
}

export interface StreamCallbacks {
  onStatus: (message: string) => void;
  onRequirements: (requirements: string[], results: Array<{ requirement: string; compliance_info: string }>) => void;
  onToken: (token: string) => void;
  onDone: () => void;
  onError: (error: string) => void;
}

// =============================================================================
// Document API
// =============================================================================

/**
 * List documents of a given type.
 */
export async function listDocuments(type: DocType): Promise<string[]> {
  const response = await fetch(`/api/documents?type=${type}`);
  if (!response.ok) {
    throw new Error(`Failed to list documents: ${response.statusText}`);
  }
  const data = await response.json();
  return data.documents;
}

/**
 * Upload a document.
 */
export async function uploadDocument(file: File, type: DocType): Promise<{ success: boolean; message: string; doc_id?: string }> {
  const formData = new FormData();
  formData.append('file', file);

  const response = await fetch(`/api/documents?type=${type}`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Upload failed');
  }

  return response.json();
}

/**
 * Delete a document.
 */
export async function deleteDocument(docId: string, type: DocType): Promise<{ success: boolean; message: string }> {
  const response = await fetch(`/api/documents/${encodeURIComponent(docId)}?type=${type}`, {
    method: 'DELETE',
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Delete failed');
  }

  return response.json();
}

// =============================================================================
// Chat API with SSE Streaming
// =============================================================================

/**
 * Send a chat message and stream the response via Server-Sent Events.
 *
 * The backend sends these event types:
 * - status: Progress updates during retrieval
 * - requirements: Extracted requirements from internal docs
 * - token: Individual tokens from the LLM
 * - done: Streaming complete
 * - error: Error occurred
 */
export async function streamChat(request: ChatRequest, callbacks: StreamCallbacks): Promise<void> {
  const response = await fetch('/api/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    throw new Error(`Chat request failed: ${response.statusText}`);
  }

  const reader = response.body?.getReader();
  const decoder = new TextDecoder();

  if (!reader) {
    throw new Error('No response body');
  }

  let currentEvent = '';
  let buffer = '';

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split('\n');
    buffer = lines.pop() || ''; // Keep incomplete line in buffer

    for (const line of lines) {
      if (line.startsWith('event:')) {
        currentEvent = line.slice(6).trim();
      } else if (line.startsWith('data:')) {
        const dataStr = line.slice(5).trim();
        if (!dataStr) continue;

        try {
          const data = JSON.parse(dataStr);

          switch (currentEvent) {
            case 'status':
              callbacks.onStatus(data.message);
              break;
            case 'requirements':
              callbacks.onRequirements(data.requirements, data.compliance_results);
              break;
            case 'token':
              callbacks.onToken(data.token);
              break;
            case 'done':
              callbacks.onDone();
              break;
            case 'error':
              callbacks.onError(data.error);
              break;
          }
        } catch (e) {
          console.error('Failed to parse SSE data:', e, dataStr);
        }
      }
    }
  }
}
