from src.adapters.mock_legal_engine import MockLegalEngine
from src.services.language_detector import LanguageDetector
from src.services.normalizer import Normalizer
from src.services.translator import Translator
from src.services.glossary import GlossaryService
from src.schemas.legal_response import MultilingualProcessRequest, MultilingualProcessResponse, LanguageInfo
from src.schemas.language import LanguageCode
import logging

logger = logging.getLogger(__name__)

class MultilingualProcessor:
    def __init__(self, 
                 detector: LanguageDetector,
                 normalizer: Normalizer,
                 translator: Translator,
                 glossary: GlossaryService,
                 legal_engine: MockLegalEngine):
        self.detector = detector
        self.normalizer = normalizer
        self.translator = translator
        self.glossary = glossary
        self.legal_engine = legal_engine

    async def process(self, request: MultilingualProcessRequest) -> MultilingualProcessResponse:
        logger.info(f"Processing request for output language: {request.output_language}")
        
        # 1. Detect Language
        detection_result = await self.detector.detect(request.text)
        input_lang = detection_result["detected_language"]
        confidence = detection_result["confidence"]
        
        if confidence < 0.3:
            # In a real app we might return a specific error requesting clarification
            logger.warning("Low confidence language detection.")
            
        # 2. Normalize to English (if not already English)
        if input_lang != LanguageCode.EN:
            normalized_text = await self.normalizer.normalize(request.text)
        else:
            normalized_text = request.text
            
        # 3. Call Legal Engine (Always using normalized English text)
        engine_response = await self.legal_engine.get_response(normalized_text)
        
        # 4. Translate Outputs if necessary
        out_lang = request.output_language
        
        if out_lang == LanguageCode.EN:
            translated_rights = engine_response.rights_explanation
            translated_actions = engine_response.recommended_actions
        else:
            translated_rights = await self.translator.translate_safe(
                engine_response.rights_explanation, LanguageCode.EN, out_lang
            )
            translated_actions = []
            for action in engine_response.recommended_actions:
                trans_action = await self.translator.translate_safe(
                    action, LanguageCode.EN, out_lang
                )
                translated_actions.append(trans_action)
                
        # For applicable laws, we preserve the "act" and "section" strictly
        # We only translate the explanation.
        translated_laws = []
        for law in engine_response.applicable_laws:
            # Ensure "act" and "section" are protected manually or let EntityProtector handle it
            if out_lang != LanguageCode.EN:
                trans_explanation = await self.translator.translate_safe(law.explanation, LanguageCode.EN, out_lang)
            else:
                trans_explanation = law.explanation
                
            # Copy law but update explanation
            law_copy = law.model_copy()
            law_copy.explanation = trans_explanation
            translated_laws.append(law_copy)
            
        disclaimer = self.glossary.get_disclaimer(out_lang)
        
        return MultilingualProcessResponse(
            language=LanguageInfo(input=input_lang, output=out_lang),
            normalized_text=normalized_text,
            rights_explanation=translated_rights,
            applicable_laws=translated_laws,
            recommended_actions=translated_actions,
            document=engine_response.document, # Document translation is handled separately or passed as is
            disclaimer=disclaimer
        )
