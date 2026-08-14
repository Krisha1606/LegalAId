from phase10_multilingual.src.adapters.translation_provider import TranslationProvider
from phase10_multilingual.src.schemas.language import LanguageCode
from phase10_multilingual.src.services.entity_protector import EntityProtector

class Translator:
    def __init__(self, provider: TranslationProvider, entity_protector: EntityProtector):
        self.provider = provider
        self.entity_protector = entity_protector

    async def translate_safe(self, text: str, source_language: LanguageCode, target_language: LanguageCode) -> str:
        if source_language == target_language:
            return text
            
        # 1. Protect entities
        protected_text, mapping = self.entity_protector.protect(text)
        
        # 2. Translate
        translated_text = await self.provider.translate(protected_text, source_language, target_language)
        
        # 3. Restore entities
        final_text = self.entity_protector.restore(translated_text, mapping)
        
        return final_text
