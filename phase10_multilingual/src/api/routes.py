from fastapi import APIRouter, Depends, HTTPException

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
