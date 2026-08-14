from pydantic import BaseModel, Field
from typing import Optional
from phase10_multilingual.src.schemas.language import LanguageCode
from phase10_multilingual.src.schemas.legal_response import DocumentSchema

class DocumentTranslationRequest(BaseModel):
    document_type: str = Field(..., max_length=100, description="Type of document, e.g., legal_notice")
    source_language: LanguageCode = Field(..., description="Original language")
    target_language: LanguageCode = Field(..., description="Language to translate to")
    content: str = Field(..., min_length=1, max_length=50000, description="Raw document content")

class DocumentTranslationResponse(BaseModel):
    document: DocumentSchema
