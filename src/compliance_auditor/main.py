"""
Compliance Auditor - Main Entry Point

Run with: python -m compliance_auditor.main

This launches the FastAPI backend server.
For development with React, also run: cd src/frontend && npm run dev
"""

import uvicorn


def main():
    """Launch the FastAPI server."""
    uvicorn.run(
        "compliance_auditor.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Auto-reload on code changes
    )


if __name__ == "__main__":
    main()
