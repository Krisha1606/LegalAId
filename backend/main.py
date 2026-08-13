"""
main.py — FastAPI backend for LegalAId Phase 9: Legal Document Generator

Routes:
    GET  /api/document/dummy/{doc_type}   → Return dummy JSON for a document type
    POST /api/document/generate           → Generate editable document from legal JSON
    POST /api/document/pdf                → Generate and download PDF from document fields
"""

import json
import os
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel
from typing import Any, Optional
import io

from document_generator import generate as generate_document
from pdf_generator import generate_pdf

# -------------------------------------------------------------------------
# App setup
# -------------------------------------------------------------------------

app = FastAPI(
    title="LegalAId — Document Generator API",
    version="1.0.0",
    description="Phase 9: Legal Document Generator. Independent of RAG system.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Path to dummy data directory (relative to this file)
DUMMY_DATA_DIR = Path(__file__).parent.parent / "dummy_data"

VALID_DOC_TYPES = ["labour_notice", "consumer_notice", "tenant_notice"]


# -------------------------------------------------------------------------
# Pydantic Models
# -------------------------------------------------------------------------

class GenerateRequest(BaseModel):
    """Request body for /api/document/generate — any structured legal JSON."""
    legal_json: dict[str, Any]


class PDFRequest(BaseModel):
    """Request body for /api/document/pdf — the edited document fields from the frontend."""
    document_fields: dict[str, Any]


# -------------------------------------------------------------------------
# Routes
# -------------------------------------------------------------------------

@app.get("/")
async def root():
    return {"message": "LegalAId Document Generator API", "version": "1.0.0", "phase": 9}


@app.get("/api/document/dummy/{doc_type}")
async def get_dummy_json(doc_type: str):
    """
    Return the dummy JSON for the given document type.
    This simulates what the RAG system would return in the future.
    """
    if doc_type not in VALID_DOC_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid doc_type '{doc_type}'. Valid types: {VALID_DOC_TYPES}"
        )

    json_file = DUMMY_DATA_DIR / f"{doc_type}.json"
    if not json_file.exists():
        raise HTTPException(status_code=404, detail=f"Dummy data file not found: {json_file}")

    with open(json_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    return JSONResponse(content=data)


@app.post("/api/document/generate")
async def generate_document_route(request: GenerateRequest):
    """
    Generate an editable document from any structured legal JSON.
    
    Input:  { "legal_json": { ...structured legal json... } }
    Output: { "document_fields": { ...editable fields... } }
    
    The document_generator is completely independent — same endpoint
    works for dummy data or future RAG system output.
    """
    try:
        doc_fields = generate_document(request.legal_json)
        return JSONResponse(content={"document_fields": doc_fields})
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Document generation failed: {str(e)}")


@app.post("/api/document/pdf")
async def download_pdf(request: PDFRequest):
    """
    Generate and return a PDF from the (possibly user-edited) document fields.
    
    Input:  { "document_fields": { ...fields from /generate or user edits... } }
    Output: application/pdf binary stream
    """
    try:
        pdf_bytes = generate_pdf(request.document_fields)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {str(e)}")

    doc_type  = request.document_fields.get("document_type", "legal_notice")
    filename  = f"legalaid_{doc_type}.pdf"

    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@app.get("/api/document/types")
async def list_document_types():
    """Return the list of supported document types."""
    return {
        "types": [
            {"id": "labour_notice",   "label": "Labour / Employment Notice"},
            {"id": "consumer_notice", "label": "Consumer Complaint Notice"},
            {"id": "tenant_notice",   "label": "Tenant / Rental Notice"},
        ]
    }
