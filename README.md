# Compliance Auditor

A web application for analyzing internal documents against compliance regulations using AI-powered document processing and chat.

## Features

- **Document Management**: Upload and manage two types of documents:
  - **Compliance Documents**: Regulatory standards (GDPR, HIPAA, FAA Part 450, etc.)
  - **Internal Documents**: Company policies and procedures to check for compliance

- **AI-Powered Analysis**: Chat interface powered by Google Gemini that:
  - Compares internal documents against compliance regulations
  - Identifies compliance gaps and issues
  - Provides specific recommendations for achieving compliance

- **Vector Search**: Uses LlamaCloud for semantic search and document retrieval

## Tech Stack

- **Frontend**: React + TypeScript (Vite)
- **Backend**: FastAPI with SSE streaming
- **Document Parsing**: LlamaParse (via LlamaCloud API)
- **Vector Storage**: LlamaCloud Managed Index
- **LLM**: Google Gemini 3 Pro
- **Language**: Python 3.11+, TypeScript

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
## Running the Application

### Backend (FastAPI)

```bash
cd compliance-auditor
PYTHONPATH=src uvicorn compliance_auditor.api.main:app --reload
```

The API will be available at `http://localhost:8000`

### Frontend (React)

```bash
cd src/frontend
npm install
npm run dev
```

The app will be available at `http://localhost:5173`

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
│   ├── compliance_auditor/          # Python backend
│   │   ├── __init__.py
│   │   ├── config.py                # Configuration with Pydantic
│   │   ├── main.py                  # FastAPI launcher
│   │   ├── llama_cloud/             # LlamaCloud integration
│   │   │   ├── __init__.py
│   │   │   ├── index.py             # Vector index & retrieval
│   │   │   └── parser.py            # Document parsing
│   │   └── api/                     # FastAPI routes
│   │       ├── main.py              # FastAPI app with CORS
│   │       ├── services.py          # Core business logic
│   │       ├── routes/
│   │       │   ├── documents.py     # Document CRUD
│   │       │   └── chat.py          # SSE streaming chat
│   │       └── schemas/
│   │           ├── documents.py
│   │           └── chat.py
│   │
│   └── frontend/                    # React frontend
│       ├── src/
│       │   ├── App.tsx
│       │   ├── components/
│       │   │   ├── DocumentPanel.tsx
│       │   │   └── ChatPanel.tsx
│       │   ├── hooks/
│       │   │   └── useChat.ts
│       │   └── api/
│       │       └── client.ts
│       └── package.json
│
├── requirements.txt
├── .env                             # Environment variables (not in git)
└── README.md
```