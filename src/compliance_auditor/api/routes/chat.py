"""Chat API routes with SSE streaming."""
import json
import asyncio
import logging

from fastapi import APIRouter
from sse_starlette.sse import EventSourceResponse

from ..schemas import ChatRequest
from ..services import retrieve_document_context_with_status
from compliance_auditor.llama_cloud.index import stream_chat_with_context

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("")
async def chat_stream(request: ChatRequest):
    """
    Process a chat message and stream the response via Server-Sent Events.

    The response includes multiple event types:
    - **status**: Progress updates during document retrieval and analysis
    - **requirements**: Extracted requirements from internal documents
    - **token**: Individual tokens from the LLM response
    - **done**: Signals that streaming is complete
    - **error**: Error messages if something goes wrong

    Example usage with JavaScript EventSource:
    ```javascript
    const eventSource = new EventSource('/api/chat');
    eventSource.addEventListener('status', (e) => console.log('Status:', e.data));
    eventSource.addEventListener('token', (e) => console.log('Token:', e.data));
    eventSource.addEventListener('done', () => eventSource.close());
    ```
    """

    async def event_generator():
        try:
            # Phase 1: Document retrieval with status updates
            retrieval_result = None

            for status_msg, partial_result in retrieve_document_context_with_status(
                request.selected_compliance,
                request.selected_internal,
                user_query=request.message
            ):
                retrieval_result = partial_result

                # Send status update
                yield {
                    "event": "status",
                    "data": json.dumps({
                        "message": status_msg,
                        "requirements_count": len(partial_result.get("requirements", [])),
                        "compliance_results_count": len(partial_result.get("compliance_results", []))
                    })
                }
                await asyncio.sleep(0)  # Yield control to allow other tasks

            # Send extracted requirements
            if retrieval_result and retrieval_result.get("requirements"):
                yield {
                    "event": "requirements",
                    "data": json.dumps({
                        "requirements": retrieval_result["requirements"],
                        "compliance_results": retrieval_result.get("compliance_results", [])
                    })
                }

            # Build context from retrieval results
            compliance_sections = []
            for item in (retrieval_result or {}).get("compliance_results", []):
                compliance_sections.append(
                    f"**Internal Requirement:** {item['requirement']}\n"
                    f"**Compliance Analysis:** {item['compliance_info']}"
                )
            compliance_context = "\n\n---\n\n".join(compliance_sections) if compliance_sections else ""
            internal_context = (retrieval_result or {}).get("internal_content", "")

            # Convert chat history to expected format
            chat_history = [
                {"role": m.role, "content": m.content}
                for m in request.chat_history
            ]

            # Phase 2: Stream LLM response token by token
            for token in stream_chat_with_context(
                message=request.message,
                compliance_context=compliance_context,
                internal_context=internal_context,
                chat_history=chat_history
            ):
                if token:
                    yield {
                        "event": "token",
                        "data": json.dumps({"token": token})
                    }
                    await asyncio.sleep(0)

            # Signal completion
            yield {
                "event": "done",
                "data": json.dumps({"complete": True})
            }

        except Exception as e:
            logger.exception("Error in chat stream")
            yield {
                "event": "error",
                "data": json.dumps({"error": str(e)})
            }

    return EventSourceResponse(event_generator())


@router.post("/clear")
async def clear_chat():
    """
    Clear chat history.

    Note: Chat history is managed client-side in React state,
    so this endpoint just returns success. The client should
    clear its local state.
    """
    return {"success": True, "message": "Chat cleared"}
