# Compliance Auditor

AI-powered tool for analyzing internal documents against compliance regulations.

## Tech Stack

- **Frontend**: React + TypeScript + Vite
- **Backend**: FastAPI + SSE streaming
- **AI**: Google Gemini, LlamaCloud (parsing & vector search)

## Setup

```bash
pip install -r requirements.txt
```

Create `.env`:
```env
LLAMA_CLOUD_API_KEY=your_key
LLAMA_CLOUD_INDEX_NAME=compliance-auditor
GOOGLE_API_KEY=your_key
```

## Run

```bash
# Backend
PYTHONPATH=src uvicorn compliance_auditor.api.main:app --reload

# Frontend
cd src/frontend && npm install && npm run dev
```

- Backend: http://localhost:8000
- Frontend: http://localhost:5173
