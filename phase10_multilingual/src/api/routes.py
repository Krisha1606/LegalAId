import io
import uuid
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from backend.document_generator import generate as generate_doc_fields, SUPPORTED_DOCUMENT_TYPES
from backend.pdf_generator import generate_pdf
from phase10_multilingual.src.adapters.document_adapter import LegalDocumentAdapter, detect_document_type
from phase10_multilingual.src.adapters.real_legal_engine import RealLegalEngineAdapter
from phase10_multilingual.src.adapters.translation_provider import (
    LLMTranslationProvider,
    MockTranslationProvider,
)
from phase10_multilingual.src.config.settings import settings
from phase10_multilingual.src.schemas.document import (
    DocumentTranslationRequest,
    DocumentTranslationResponse,
)
from phase10_multilingual.src.schemas.legal_response import (
    MultilingualProcessRequest,
    MultilingualProcessResponse,
)
from phase10_multilingual.src.services.document_language_service import DocumentLanguageService
from phase10_multilingual.src.services.entity_protector import EntityProtector
from phase10_multilingual.src.services.glossary import GlossaryService
from phase10_multilingual.src.services.language_detector import LanguageDetector
from phase10_multilingual.src.services.multilingual_processor import MultilingualProcessor
from phase10_multilingual.src.services.normalizer import Normalizer
from phase10_multilingual.src.services.translator import Translator

router = APIRouter()

# In-memory document storage for session management & editing
DOCUMENTS_STORE: Dict[str, Dict[str, Any]] = {}


class DocumentGeneratePayload(BaseModel):
    query: Optional[str] = Field(None, description="User's query/problem statement")
    analysis: Optional[Dict[str, Any]] = Field(None, description="RAG legal analysis response")
    document_type: Optional[str] = Field("auto", description="Template type: labour_notice, consumer_notice, tenant_notice, auto")
    user_info: Optional[Dict[str, str]] = Field(None, description="User/Sender details (name, address)")
    opposite_party: Optional[Dict[str, str]] = Field(None, description="Opposite party details (name, address)")
    amount: Optional[str] = Field(None, description="Dispute amount")
    facts: Optional[List[str]] = Field(None, description="Custom factual statements")
    relief_requested: Optional[List[str]] = Field(None, description="Specific relief requested")
    notice_period: Optional[str] = Field(None, description="Notice period (e.g. 15 days)")
    date: Optional[str] = Field(None, description="Document date")
    language: Optional[str] = Field("en", description="Document language")


class DocumentUpdateRequest(BaseModel):
    content: str = Field(..., description="Updated text content of the document")


def get_processor():
    if settings.translation_provider == "llm" and settings.openai_api_key:
        provider = LLMTranslationProvider(api_key=settings.openai_api_key)
    else:
        provider = MockTranslationProvider()

    entity_protector = EntityProtector()
    glossary = GlossaryService()
    legal_engine = RealLegalEngineAdapter()

    detector = LanguageDetector(provider)
    normalizer = Normalizer(provider)
    translator = Translator(provider, entity_protector)

    return MultilingualProcessor(detector, normalizer, translator, glossary, legal_engine)


def get_document_service():
    if settings.translation_provider == "llm" and settings.openai_api_key:
        provider = LLMTranslationProvider(api_key=settings.openai_api_key)
    else:
        provider = MockTranslationProvider()
    entity_protector = EntityProtector()
    translator = Translator(provider, entity_protector)
    return DocumentLanguageService(translator)


@router.post("/process", response_model=MultilingualProcessResponse)
async def process_language(request: MultilingualProcessRequest, processor: MultilingualProcessor = Depends(get_processor)):
    try:
        if not request.text.strip():
            raise HTTPException(status_code=400, detail="Input text cannot be empty")
        return await processor.process(request)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))


@router.post("/document", response_model=DocumentTranslationResponse)
async def translate_document(request: DocumentTranslationRequest, doc_service: DocumentLanguageService = Depends(get_document_service)):
    try:
        if not request.content.strip():
            raise HTTPException(status_code=400, detail="Document content cannot be empty")
        return await doc_service.translate_document(request)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))


@router.post("/generate", summary="Generate structured legal notice document from RAG analysis")
async def generate_legal_document(payload: DocumentGeneratePayload):
    try:
        analysis_data = payload.analysis or {}
        query_text = payload.query or analysis_data.get("normalized_text", "")

        # 1. Adapt RAG analysis to Phase 9 legal_json schema
        legal_json = LegalDocumentAdapter.to_legal_json(
            analysis_data=analysis_data,
            query_text=query_text,
            document_type=payload.document_type if payload.document_type != "auto" else None,
            user_info=payload.user_info,
            opposite_party=payload.opposite_party,
            amount=payload.amount,
            facts=payload.facts,
            relief_requested=payload.relief_requested,
            notice_period=payload.notice_period,
            date_str=payload.date
        )

        # 2. Generate structured document fields
        doc_fields = generate_doc_fields(legal_json)

        # 3. Generate PDF bytes via ReportLab
        pdf_bytes = generate_pdf(doc_fields)

        # 4. Generate formatted text representation for DocumentEditorPage
        text_lines = [
            f"=== {doc_fields.get('template_title', 'LEGAL NOTICE')} ===",
            f"Date: {doc_fields.get('date', '')}",
            f"From: {doc_fields.get('sender_name', '')}, {doc_fields.get('sender_address', '')}",
            f"To: {doc_fields.get('recipient_name', '')}, {doc_fields.get('recipient_address', '')}",
            f"\nSubject: {doc_fields.get('subject', '')}\n",
            "Sir/Madam,",
            doc_fields.get('opening', ''),
            "\nSTATEMENT OF FACTS:"
        ]
        for f in doc_fields.get("facts", []):
            text_lines.append(f"• {f}")

        if doc_fields.get("laws"):
            text_lines.append("\nLEGAL BASIS & STATUTORY PROVISIONS:")
            for l in doc_fields.get("laws", []):
                text_lines.append(f"• {l.get('act', '')} - {l.get('section', '')}: {l.get('explanation', '')}")

        if doc_fields.get("relief_requested"):
            text_lines.append("\nRELIEF SOUGHT / DEMANDS:")
            for r in doc_fields.get("relief_requested", []):
                text_lines.append(f"• {r}")

        text_lines.append(f"\n{doc_fields.get('closing', '')}")
        text_lines.append(f"\nYours faithfully,\n{doc_fields.get('sender_name', '')}")
        formatted_content = "\n".join(text_lines)

        doc_id = str(uuid.uuid4())
        record = {
            "id": doc_id,
            "type": doc_fields.get("document_type", "legal_notice"),
            "template_title": doc_fields.get("template_title", "Legal Notice"),
            "language": payload.language or "en",
            "content": formatted_content,
            "fields": doc_fields,
            "pdf_bytes": pdf_bytes,
            "pdf_download_url": f"/api/documents/download/{doc_id}"
        }
        DOCUMENTS_STORE[doc_id] = record

        return {
            "id": doc_id,
            "type": record["type"],
            "template_title": record["template_title"],
            "language": record["language"],
            "content": record["content"],
            "fields": record["fields"],
            "pdf_download_url": record["pdf_download_url"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Document generation failed: {e}")


@router.get("/download/{doc_id}", summary="Download generated PDF by document ID")
async def download_pdf_by_id(doc_id: str):
    record = DOCUMENTS_STORE.get(doc_id)
    if not record or not record.get("pdf_bytes"):
        raise HTTPException(status_code=404, detail="Document PDF not found or expired.")

    doc_type = record.get("type", "legal_notice")
    return Response(
        content=record["pdf_bytes"],
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={doc_type}_{doc_id[:8]}.pdf"}
    )


@router.post("/generate-pdf", summary="Generate and return PDF binary stream directly")
async def generate_direct_pdf(payload: Dict[str, Any]):
    try:
        if "content" in payload and payload["content"]:
            title = payload.get("template_title", "Legal Notice")
            pdf_bytes = generate_pdf_from_text_content(title, payload["content"])
            doc_type = payload.get("document_type") or payload.get("type", "legal_notice")
            return Response(
                content=pdf_bytes,
                media_type="application/pdf",
                headers={"Content-Disposition": f"attachment; filename={doc_type}.pdf"}
            )

        # Check if fields dictionary is directly passed
        if "template_title" in payload or "opening" in payload:
            doc_fields = payload
        elif "document_type" in payload and "user" in payload:
            doc_fields = generate_doc_fields(payload)
        else:
            # Adapt using default/analysis dictionary
            legal_json = LegalDocumentAdapter.to_legal_json(payload)
            doc_fields = generate_doc_fields(legal_json)

        pdf_bytes = generate_pdf(doc_fields)
        doc_type = doc_fields.get("document_type", "legal_notice")
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={doc_type}.pdf"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {e}")


@router.get("/{doc_id}", summary="Retrieve stored document content by ID")
async def get_document_by_id(doc_id: str):
    record = DOCUMENTS_STORE.get(doc_id)
    if not record:
        raise HTTPException(status_code=404, detail="Document not found.")
    return {
        "id": record["id"],
        "type": record["type"],
        "template_title": record.get("template_title", "Legal Notice"),
        "language": record.get("language", "en"),
        "content": record["content"],
        "pdf_download_url": record.get("pdf_download_url", f"/api/documents/download/{doc_id}")
    }


def generate_pdf_from_text_content(title: str, text: str) -> bytes:
    import io
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable
    from backend.pdf_generator import _build_styles, _header_footer, ACCENT_BLUE

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=50,
        rightMargin=50,
        topMargin=50,
        bottomMargin=50,
        title=title
    )
    styles = _build_styles()
    story = []
    story.append(Paragraph(title, styles['doc_title']))
    story.append(HRFlowable(width='100%', thickness=2, color=ACCENT_BLUE, spaceAfter=12))

    for line in text.split('\n'):
        line = line.strip()
        if not line:
            story.append(Spacer(1, 6))
        elif line.startswith('==='):
            continue
        elif line.isupper() and len(line) < 40:
            story.append(Paragraph(line, styles['section_label']))
        elif line.startswith('•') or line.startswith('-'):
            story.append(Paragraph(line, styles['bullet']))
        elif line.startswith('Date:') or line.startswith('From:') or line.startswith('To:'):
            story.append(Paragraph(f'<b>{line}</b>', styles['body']))
        elif line.startswith('Subject:'):
            story.append(Paragraph(f'<b>{line}</b>', styles['body_bold']))
        else:
            story.append(Paragraph(line, styles['body']))

    doc.build(story, onFirstPage=_header_footer, onLaterPages=_header_footer)
    buffer.seek(0)
    return buffer.read()


@router.put("/{doc_id}", summary="Update document content by ID")
async def update_document_content(doc_id: str, request: DocumentUpdateRequest):
    record = DOCUMENTS_STORE.get(doc_id)
    if not record:
        raise HTTPException(status_code=404, detail="Document not found.")

    record["content"] = request.content
    # Regenerate PDF with updated content
    try:
        title = record.get("template_title", "Legal Notice")
        record["pdf_bytes"] = generate_pdf_from_text_content(title, request.content)
    except Exception:
        try:
            fields = record.get("fields", {}).copy()
            record["pdf_bytes"] = generate_pdf(fields)
        except Exception:
            pass

    return {
        "id": doc_id,
        "content": record["content"],
        "message": "Document updated successfully."
    }


