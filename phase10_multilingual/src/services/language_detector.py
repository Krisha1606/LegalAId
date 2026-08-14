from phase10_multilingual.src.adapters.translation_provider import TranslationProvider
from phase10_multilingual.src.schemas.language import LanguageCode

class LanguageDetector:
    def __init__(self, provider: TranslationProvider):
        self.provider = provider

    async def detect(self, text: str) -> dict:
        if not text.strip():
            raise ValueError("Input text cannot be empty")
        return await self.provider.detect_language(text)
