from phase10_multilingual.src.adapters.translation_provider import TranslationProvider

class Normalizer:
    def __init__(self, provider: TranslationProvider):
        self.provider = provider

    async def normalize(self, text: str) -> str:
        if not text.strip():
            raise ValueError("Input text cannot be empty")
        return await self.provider.normalize_to_english(text)
