import json
import logging
from abc import ABC, abstractmethod
from typing import Optional

from phase10_multilingual.src.schemas.language import LanguageCode

logger = logging.getLogger(__name__)


class TranslationProvider(ABC):
    @abstractmethod
    async def translate(self, text: str, source_language: LanguageCode, target_language: LanguageCode) -> str:
        pass
    
    @abstractmethod
    async def detect_language(self, text: str) -> dict:
        """Returns {"detected_language": LanguageCode, "confidence": float}"""
        pass
    
    @abstractmethod
    async def normalize_to_english(self, text: str) -> str:
        pass


class MockTranslationProvider(TranslationProvider):
    async def translate(self, text: str, source_language: LanguageCode, target_language: LanguageCode) -> str:
        if target_language == LanguageCode.HI:
            return f"[Hindi Translation of: {text}]"
        return text

    async def detect_language(self, text: str) -> dict:
        text_lower = text.lower()
        if "mere" in text_lower or "nahi" in text_lower or "kiya" in text_lower:
            # Assume roman hindi if typical words exist
            return {"detected_language": LanguageCode.ROMAN_HI, "confidence": 0.95}
        if any(char in text for char in 'अआइईउऊएऐओऔकखगघचछजझटठडढतथदधनपफबभमयरलवशषसह'):
            return {"detected_language": LanguageCode.HI, "confidence": 0.99}
        return {"detected_language": LanguageCode.EN, "confidence": 0.95}

    async def normalize_to_english(self, text: str) -> str:
        text_lower = text.lower()
        if "salary" in text_lower or "वेतन" in text_lower or "सैलरी" in text_lower:
            return "My employer has not paid my salary."
        if "deposit" in text_lower or "डिपॉजिट" in text_lower or "मकान मालिक" in text_lower:
            return "My landlord has not returned my security deposit."
        if "defective" in text_lower or "refund" in text_lower or "खराब" in text_lower:
            return "The seller refused to refund me for a defective phone."
        return text


class LLMTranslationProvider(TranslationProvider):
    def __init__(self, api_key: str):
        try:
            from openai import AsyncOpenAI
            self.client = AsyncOpenAI(api_key=api_key)
        except ImportError as e:
            raise RuntimeError("openai package is required for LLMTranslationProvider") from e
        self.model = "gpt-4o-mini"
        
    async def translate(self, text: str, source_language: LanguageCode, target_language: LanguageCode) -> str:
        prompt = f"Translate the following legal text accurately from {source_language.value} to {target_language.value}. Preserve formatting, context, and any specific placeholders directly. Only return the translated text.\n\nText:\n{text}"
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Translation failed: {e}")
            raise Exception("Translation service unavailable")

    async def detect_language(self, text: str) -> dict:
        prompt = """Detect the language of the following text. It can be one of: "en" (English), "hi" (Hindi), "roman_hi" (Roman Hindi), or "hinglish" (Mixed Hindi-English).
        Return ONLY a JSON object with "detected_language" (string) and "confidence" (float between 0 and 1).
        
        Text: """ + text
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                response_format={ "type": "json_object" },
                temperature=0.0
            )
            result = json.loads(response.choices[0].message.content)
            # map to enum
            lang_str = result.get("detected_language", "en")
            # fallback mapping
            try:
                lang = LanguageCode(lang_str)
            except ValueError:
                lang = LanguageCode.EN
            return {"detected_language": lang, "confidence": result.get("confidence", 0.9)}
        except Exception as e:
            logger.error(f"Language detection failed: {e}")
            return {"detected_language": LanguageCode.EN, "confidence": 0.5}

    async def normalize_to_english(self, text: str) -> str:
        prompt = f"Normalize the following legal problem statement into standard English. Preserve names, dates, amounts, addresses, numbers, and legal terms exactly as intended. Do NOT add legal interpretations, just translate the user's factual statement to standard English.\n\nStatement:\n{text}"
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Normalization failed: {e}")
            raise Exception("Normalization service unavailable")
