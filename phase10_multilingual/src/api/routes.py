from fastapi import APIRouter, HTTPException, Depends
from src.schemas.legal_response import MultilingualProcessRequest, MultilingualProcessResponse
from src.schemas.document import DocumentTranslationRequest, DocumentTranslationResponse

# Dependable instances (In a real app, use dependency injection properly)
from src.config.settings import settings
from src.adapters.translation_provider import MockTranslationProvider, LLMTranslationProvider
from src.adapters.mock_legal_engine import MockLegalEngine
from src.services.entity_protector import EntityProtector
from src.services.glossary import GlossaryService
from src.services.language_detector import LanguageDetector
from src.services.normalizer import Normalizer
from src.services.translator import Translator
from src.services.multilingual_processor import MultilingualProcessor
from src.services.document_language_service import DocumentLanguageService

router = APIRouter()

def get_processor():
    if settings.translation_provider == "llm" and settings.openai_api_key:
        provider = LLMTranslationProvider(api_key=settings.openai_api_key)
    else:
        provider = MockTranslationProvider()
        
    entity_protector = EntityProtector()
    glossary = GlossaryService()
    legal_engine = MockLegalEngine()
    
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
