from phase10_multilingual.src.schemas.document import (
    DocumentSchema,
    DocumentTranslationRequest,
    DocumentTranslationResponse,
)
from phase10_multilingual.src.services.translator import Translator

class DocumentLanguageService:
    def __init__(self, translator: Translator):
        self.translator = translator

    async def translate_document(self, request: DocumentTranslationRequest) -> DocumentTranslationResponse:
        translated_content = await self.translator.translate_safe(
            request.content,
            request.source_language,
            request.target_language
        )
        
        return DocumentTranslationResponse(
            document=DocumentSchema(
                type=request.document_type,
                language=request.target_language,
                content=translated_content
            )
        )
