"""
Compliance Auditor - Gradio UI

A web interface with split-panel layout:
- Left panel: Document management with tabs for compliance/internal documents
- Right panel: Chat interface for conversational compliance analysis
"""

import logging
from pathlib import Path
from typing import Generator
import gradio as gr
import os
from llama_index.llms.gemini import Gemini
from llama_index.core.llms import ChatMessage, MessageRole
from llama_index.core.vector_stores import MetadataFilters, MetadataFilter, FilterOperator
from compliance_auditor.config import get_settings

from compliance_auditor.llama_cloud import LlamaCloudParser, LlamaCloudIndex
from compliance_auditor.llama_cloud.index import stream_chat_with_context

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global instances
parser: LlamaCloudParser | None = None
index: LlamaCloudIndex | None = None

# Document type mappings (internal name -> display name)
DOC_TYPE_LABELS = {
    "company_doc": "Internal Document",
    "regulation": "Compliance Document",
}

DOC_TYPE_FROM_LABEL = {v: k for k, v in DOC_TYPE_LABELS.items()}
settings = get_settings()

def get_parser() -> LlamaCloudParser:
    """Get or create the parser instance."""
    global parser
    if parser is None:
        parser = LlamaCloudParser()
    return parser


def get_index() -> LlamaCloudIndex:
    """Get or create the index instance."""
    global index
    if index is None:
        index = LlamaCloudIndex()
    return index


def get_document_choices(doc_type: str) -> list[str]:
    """Get list of documents for dropdown."""
    try:
        llama_index = get_index()
        docs = llama_index.get_all_documents(doc_type)
        return docs if docs else []
    except Exception:
        return []


def upload_document(file, doc_type_label: str) -> str:
    """
    Upload and index a document.

    Args:
        file: Uploaded file object
        doc_type_label: Display label for document type

    Returns:
        Status message
    """
    logger.info(f"upload_document called with file={file}, doc_type_label={doc_type_label}")

    if file is None:
        return "Please upload a file."

    doc_type = DOC_TYPE_FROM_LABEL.get(doc_type_label, "regulation")
    logger.info(f"doc_type resolved to: {doc_type}")

    try:
        # In Gradio, file can be a string path or have a .name attribute
        if isinstance(file, str):
            file_path = Path(file)
        else:
            file_path = Path(file.name) if hasattr(file, 'name') else Path(str(file))

        logger.info(f"file_path: {file_path}, exists: {file_path.exists()}")

        # Use filename (without extension) as document ID
        doc_id = file_path.stem
        logger.info(f"doc_id: {doc_id}")

        # Add to index
        logger.info("Adding to index...")
        llama_index = get_index()
        llama_index.add_document_from_file(file_path, doc_id, doc_type)
        logger.info("Document added to index")

        return f"Uploaded '{doc_id}' successfully."

    except Exception as e:
        logger.exception("Error uploading document")
        return f"Error: {str(e)}"


def delete_document(doc_id: str, doc_type_label: str) -> str:
    """Delete a document from the index."""
    if not doc_id.strip():
        return "Please enter a document ID."

    doc_type = DOC_TYPE_FROM_LABEL.get(doc_type_label, "regulation")
    
    try:
        llama_index = get_index()
        
        llama_index.delete_document(doc_id.strip(), doc_type)
        return f"Deleted '{doc_id}'"

    except Exception as e:
        logger.exception("Error deleting document")
        return f"Error: {str(e)}"


def retrieve_document_context(
    selected_compliance: list[str] | None,
    selected_internal: list[str] | None,
    user_query: str | None = None
) -> tuple[str, str]:
    """
    Retrieve content from both indexes using appropriate queries.

    Uses context-appropriate queries for each document type:
    - Compliance docs: queries about regulations, requirements, standards
    - Internal docs: queries about company policies, procedures, implementation

    Args:
        selected_compliance: List of selected compliance document IDs
        selected_internal: List of selected internal document IDs
        user_query: Optional user query to include in retrieval

    Returns:
        Tuple of (compliance_content, internal_content)
    """
    llama_index = get_index()
    regulations_index, _ = llama_index._get_or_create_index("regulation")
    company_docs_index, _ = llama_index._get_or_create_index("company_doc")
    logger.info(f"Retrieving context: compliance={selected_compliance}, internal={selected_internal}")

    # Build queries appropriate for each document type
    # Include user query if provided to retrieve relevant sections
    llm = Gemini(model="gemini-3-flash-preview", api_key=settings.google_api_key)
    compliance_content = ""
    if selected_compliance:
        system_prompt = f"""You are a document assistant. Your role is to:
        1. Turn user's query into a prompt for another LLM that is an expert on compliance documents relavent to this query
        2. Make sure to carefully review the user's query include all relevant details in the prompt you produce.
        """
        messages = [ChatMessage(role=MessageRole.SYSTEM, content=system_prompt)]
        messages.append(ChatMessage(role=MessageRole.USER, content=user_query))
        response = llm.chat(messages)
        compliance_query = response.message.content 

        # Retrieve content from compliance documents
        filters = MetadataFilters(
            filters=[
                MetadataFilter(
                    key="doc_id",
                    operator=FilterOperator.IN,
                    value=selected_compliance
                )
            ]
        )
        query_engine = regulations_index.as_query_engine(llm=llm, filters=filters)
        response = query_engine.query(compliance_query)
        compliance_content = str(response)

    # Retrieve content from internal documents
    internal_content = ""
    if selected_internal:
        system_prompt = f"""You are a document assistant. Your role is to:

        1. Turn user's query into a prompt for another LLM that is an expert on company internal documents relavent to this query
        2. Make sure to carefully review the user's query include all relevant details in the prompt you produce, 
        The user has selected the following documents to search: {selected_internal}
        """
        messages = [ChatMessage(role=MessageRole.SYSTEM, content=system_prompt)]
        messages.append(ChatMessage(role=MessageRole.USER, content=user_query))
        response = llm.chat(messages)
        internal_query = response.message.content
        

        filters = MetadataFilters(
            filters=[
                MetadataFilter(
                    key="doc_id",
                    operator=FilterOperator.IN,
                    value=selected_internal
                )
            ]
        )
        query_engine = company_docs_index.as_query_engine(llm=llm, filters=filters)
        response = query_engine.query(internal_query)
        internal_content = str(response)

    return compliance_content, internal_content


def handle_chat_message(
    message: str,
    chat_history: list,
    context_state: dict | None,
    selected_compliance: list[str] | None,
    selected_internal: list[str] | None
) -> Generator:
    """
    Process chat message with streaming response using direct Gemini API.

    This approach:
    1. Queries BOTH indexes to retrieve relevant content
    2. Calls Gemini directly with the combined context
    3. Streams the response back

    Args:
        message: User's message
        chat_history: Current chat history
        context_state: Cached document context (compliance_content, internal_content)
        selected_compliance: Selected compliance documents
        selected_internal: Selected internal documents

    Yields:
        Updated chat history, chat history state, context state
    """
    if not message or not message.strip():
        yield chat_history, chat_history, context_state
        return

    # Add user message to history
    chat_history = chat_history + [{"role": "user", "content": message}]
    yield chat_history, chat_history, context_state

    try:
        # Always retrieve fresh document context based on current selections
        compliance_content, internal_content = retrieve_document_context(
            selected_compliance or [],
            selected_internal or [],
            user_query=message  # Include user's message in retrieval
        )
        context_state = {
            "compliance": compliance_content,
            "internal": internal_content
        }

        # Stream response directly from Gemini with both document contexts
        chat_history = chat_history + [{"role": "assistant", "content": ""}]

        # Get previous messages for context (excluding the one we just added)
        previous_messages = chat_history[:-1]

        for token in stream_chat_with_context(
            message=message,
            compliance_context=context_state["compliance"],
            internal_context=context_state["internal"],
            chat_history=previous_messages
        ):
            if token:
                chat_history[-1]["content"] += token
                yield chat_history, chat_history, context_state

    except Exception as e:
        logger.exception("Error generating response")
        chat_history = chat_history + [{"role": "assistant", "content": f"Error: {str(e)}"}]
        yield chat_history, chat_history, context_state


def handle_upload_and_refresh(file, doc_type_label: str):
    """Upload document and refresh document lists."""
    if file is None:
        compliance_docs = get_document_choices("regulation")
        internal_docs = get_document_choices("company_doc")
        return (
            "Please select a file.",
            gr.CheckboxGroup(choices=compliance_docs),
            gr.CheckboxGroup(choices=internal_docs)
        )

    result = upload_document(file, doc_type_label)
    compliance_docs = get_document_choices("regulation")
    internal_docs = get_document_choices("company_doc")

    return (
        result,
        gr.CheckboxGroup(choices=compliance_docs),
        gr.CheckboxGroup(choices=internal_docs)
    )


def handle_delete_compliance(selected_docs: list[str] | None):
    """Delete selected compliance documents."""
    if not selected_docs:
        compliance_docs = get_document_choices("regulation")
        return "No documents selected.", gr.CheckboxGroup(choices=compliance_docs, value=[]), None

    results = []
    for doc_id in selected_docs:
        result = delete_document(doc_id, "Compliance Document")
        results.append(result)

    compliance_docs = get_document_choices("regulation")
    return "\n".join(results), gr.CheckboxGroup(choices=compliance_docs, value=[]), None


def handle_delete_internal(selected_docs: list[str] | None):
    """Delete selected internal documents."""
    if not selected_docs:
        internal_docs = get_document_choices("company_doc")
        return "No documents selected.", gr.CheckboxGroup(choices=internal_docs, value=[]), None

    results = []
    for doc_id in selected_docs:
        result = delete_document(doc_id, "Internal Document")
        results.append(result)

    internal_docs = get_document_choices("company_doc")
    return "\n".join(results), gr.CheckboxGroup(choices=internal_docs, value=[]), None


def refresh_document_lists():
    """Refresh both document lists."""
    compliance_docs = get_document_choices("regulation")
    internal_docs = get_document_choices("company_doc")
    return (
        gr.CheckboxGroup(choices=compliance_docs, value=[]),
        gr.CheckboxGroup(choices=internal_docs, value=[])
    )


def clear_chat():
    """Clear chat history and reset engine."""
    return [], [], None


# Custom CSS for split-panel layout
CUSTOM_CSS = """
.left-panel {
    border-right: 2px solid #e5e7eb;
    padding-right: 1rem;
}
.doc-list {
    max-height: 200px;
    overflow-y: auto;
}
.upload-section {
    background: #f9fafb;
    border-radius: 8px;
    padding: 12px;
    margin-top: 12px;
}
.chat-container {
    display: flex;
    flex-direction: column;
}
footer {
    display: none !important;
}
"""


def create_app() -> gr.Blocks:
    """Create the Gradio application with split-panel layout."""

    with gr.Blocks(title="Compliance Auditor", analytics_enabled=False, css=CUSTOM_CSS) as app:
        gr.Markdown("# Compliance Auditor")
        gr.Markdown("Manage documents on the left, chat about compliance on the right.")

        # State variables
        chat_history = gr.State([])
        context_state = gr.State(None)

        with gr.Row():
            # ============ LEFT PANEL - Document Management ============
            with gr.Column(scale=2, min_width=300, elem_classes=["left-panel"]):
                # Document type tabs
                with gr.Tabs() as doc_tabs:
                    with gr.TabItem("Compliance Docs", id="compliance"):
                        gr.Markdown("*Select documents to include in analysis context*")
                        compliance_doc_list = gr.CheckboxGroup(
                            choices=get_document_choices("regulation"),
                            label="Documents",
                            elem_classes=["doc-list"]
                        )
                        delete_compliance_btn = gr.Button(
                            "Delete Selected",
                            variant="stop",
                            size="sm"
                        )

                    with gr.TabItem("Internal Docs", id="internal"):
                        gr.Markdown("*Select documents to include in analysis context*")
                        internal_doc_list = gr.CheckboxGroup(
                            choices=get_document_choices("company_doc"),
                            label="Documents",
                            elem_classes=["doc-list"]
                        )
                        delete_internal_btn = gr.Button(
                            "Delete Selected",
                            variant="stop",
                            size="sm"
                        )

                # Upload section
                with gr.Group(elem_classes=["upload-section"]):
                    gr.Markdown("### Upload Document")
                    upload_doc_type = gr.Radio(
                        choices=["Compliance Document", "Internal Document"],
                        value="Compliance Document",
                        label="Document Type",
                        scale=1
                    )
                    upload_file = gr.File(
                        label="Select or drag file",
                        file_types=[".pdf", ".docx", ".doc", ".txt", ".pptx"]
                    )
                    upload_btn = gr.Button("Upload & Index", variant="primary")
                    upload_status = gr.Markdown("")

            # ============ RIGHT PANEL - Chat Interface ============
            with gr.Column(scale=3, min_width=400, elem_classes=["chat-container"]):
                chatbot = gr.Chatbot(
                    value=[],
                    height=450,
                    show_label=False
                )

                with gr.Row():
                    chat_input = gr.Textbox(
                        placeholder="Ask about compliance requirements...",
                        show_label=False,
                        scale=4,
                        container=False
                    )
                    send_btn = gr.Button("Send", variant="primary", scale=1)

                with gr.Row():
                    clear_btn = gr.Button("Clear Chat", size="sm")
                    refresh_btn = gr.Button("Refresh Documents", size="sm")

        # ============ EVENT HANDLERS ============

        # Upload events
        upload_btn.click(
            fn=handle_upload_and_refresh,
            inputs=[upload_file, upload_doc_type],
            outputs=[upload_status, compliance_doc_list, internal_doc_list]
        )

        # Delete events
        delete_compliance_btn.click(
            fn=handle_delete_compliance,
            inputs=[compliance_doc_list],
            outputs=[upload_status, compliance_doc_list, context_state]
        )

        delete_internal_btn.click(
            fn=handle_delete_internal,
            inputs=[internal_doc_list],
            outputs=[upload_status, internal_doc_list, context_state]
        )

        # Invalidate chat engine when document selection changes
        compliance_doc_list.change(
            fn=lambda: None,
            outputs=[context_state]
        )

        internal_doc_list.change(
            fn=lambda: None,
            outputs=[context_state]
        )

        # Chat events - both button click and enter key
        chat_input.submit(
            fn=handle_chat_message,
            inputs=[chat_input, chat_history, context_state,
                    compliance_doc_list, internal_doc_list],
            outputs=[chatbot, chat_history, context_state]
        ).then(
            fn=lambda: "",
            outputs=[chat_input]
        )

        send_btn.click(
            fn=handle_chat_message,
            inputs=[chat_input, chat_history, context_state,
                    compliance_doc_list, internal_doc_list],
            outputs=[chatbot, chat_history, context_state]
        ).then(
            fn=lambda: "",
            outputs=[chat_input]
        )

        # Clear chat
        clear_btn.click(
            fn=clear_chat,
            outputs=[chatbot, chat_history, context_state]
        )

        # Refresh document lists
        refresh_btn.click(
            fn=refresh_document_lists,
            outputs=[compliance_doc_list, internal_doc_list]
        )

    return app


def main():
    """Launch the application."""
    app = create_app()
    app.queue()  # Enable queueing for long-running tasks
    app.launch(share=False)


if __name__ == "__main__":
    main()
