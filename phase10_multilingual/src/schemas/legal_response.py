from pydantic import BaseModel, Field
from typing import List, Optional
from src.schemas.language import LanguageCode

class ApplicableLaw(BaseModel):
    act: str = Field(..., description="Name of the Act")
    section: str = Field(..., description="Section identifier")
    explanation: str = Field(..., description="Explanation of the law")
    source: Optional[str] = Field(None, description="URL or citation string")

class DocumentSchema(BaseModel):
    type: str = Field(..., description="Document type, e.g., legal_notice")
    language: Optional[LanguageCode] = Field(None, description="Output language of the document")
    content: str = Field(..., description="Document content string")

class LanguageInfo(BaseModel):
    input: LanguageCode
    output: LanguageCode

class LegalEngineResponse(BaseModel):
    rights_explanation: str
    applicable_laws: List[ApplicableLaw]
    recommended_actions: List[str]
    document: Optional[DocumentSchema] = None
    citations: List[str] = []

class MultilingualProcessRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=5000, description="The user's legal problem statement")
    output_language: LanguageCode = Field(LanguageCode.EN, description="The desired output language")

class MultilingualProcessResponse(BaseModel):
    language: LanguageInfo
    normalized_text: str
    rights_explanation: str
    applicable_laws: List[ApplicableLaw]
    recommended_actions: List[str]
    document: Optional[DocumentSchema] = None
    disclaimer: str
