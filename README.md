# Compliance Auditor

A web application for analyzing internal documents against compliance regulations using AI-powered document processing and chat.

## Features

- **Document Management**: Upload and manage two types of documents:
  - **Compliance Documents**: Regulatory standards (GDPR, HIPAA, FAA Part 450, etc.)
  - **Internal Documents**: Company policies and procedures to check for compliance

- **AI-Powered Analysis**: Chat interface powered by Google Gemini 2.5 Flash that:
  - Compares internal documents against compliance regulations
  - Identifies compliance gaps and issues
  - Provides specific recommendations for achieving compliance

- **Vector Search**: Uses LlamaCloud for semantic search and document retrieval

## Tech Stack

- **Frontend**: Gradio (Python web UI framework)
- **Document Parsing**: LlamaParse (via LlamaCloud API)
- **Vector Storage**: LlamaCloud Managed Index
- **LLM**: Google Gemini 3 Pro
- **Language**: Python 3.11+

## Setup

### 1. Clone and Install Dependencies

```bash
cd compliance-auditor
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Create a `.env` file in the project root:

```env
# LlamaCloud API Configuration
LLAMA_CLOUD_API_KEY=your_llama_cloud_api_key

# LlamaCloud Index Configuration
LLAMA_CLOUD_INDEX_NAME=compliance-auditor
LLAMA_CLOUD_PROJECT_NAME=Default

# LlamaParse Configuration
LLAMA_PARSE_RESULT_TYPE=markdown
LLAMA_PARSE_LANGUAGE=en

# Gemini API Configuration
GOOGLE_API_KEY=your_google_api_key

# Document Chunking (fallback)
CHUNK_SIZE=2000
CHUNK_OVERLAP=200

# Logging
LOG_LEVEL=INFO
```
## Running the Application (in src folder)

```bash
python -m compliance_auditor.main
```

The application will start at `http://localhost:7860`

## Usage

1. **Upload Documents**:
   - Select document type (Compliance or Internal)
   - Choose a file (PDF, DOCX, PPTX, TXT supported)
   - Click "Upload & Index"

2. **Select Documents for Analysis**:
   - Check the documents you want to include in the analysis
   - Select from both Compliance and Internal tabs

3. **Chat**:
   - Ask questions about compliance
   - The AI will analyze selected documents and provide compliance assessments

## Project Structure

```
compliance-auditor/
├── src/
│   └── compliance_auditor/
│       ├── __init__.py
│       ├── app.py              # Gradio UI and main application logic
│       ├── config.py           # Configuration management with Pydantic
│       ├── main.py             # Application entry point
│       └── llama_cloud/
│           ├── __init__.py
│           ├── index.py        # LlamaCloud index management and Gemini chat
│           └── parser.py       # LlamaParse document parsing
├── requirements.txt
├── .env                        # Environment variables (not in git)
└── README.md
```