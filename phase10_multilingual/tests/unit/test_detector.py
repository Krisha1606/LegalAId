import pytest
from src.adapters.translation_provider import MockTranslationProvider
from src.services.language_detector import LanguageDetector
from src.schemas.language import LanguageCode

@pytest.mark.asyncio
async def test_detect_english():
    detector = LanguageDetector(MockTranslationProvider())
    res = await detector.detect("My employer has not paid my salary.")
    assert res["detected_language"] == LanguageCode.EN

@pytest.mark.asyncio
async def test_detect_hindi():
    detector = LanguageDetector(MockTranslationProvider())
    res = await detector.detect("मेरे नियोक्ता ने मेरा वेतन नहीं दिया है।")
    assert res["detected_language"] == LanguageCode.HI

@pytest.mark.asyncio
async def test_detect_roman_hindi():
    detector = LanguageDetector(MockTranslationProvider())
    res = await detector.detect("Mere employer ne salary nahi di.")
    assert res["detected_language"] == LanguageCode.ROMAN_HI

@pytest.mark.asyncio
async def test_detect_empty_raises():
    detector = LanguageDetector(MockTranslationProvider())
    with pytest.raises(ValueError):
        await detector.detect("   ")
