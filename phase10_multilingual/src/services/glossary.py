import json
from pathlib import Path
from phase10_multilingual.src.schemas.language import LanguageCode

class GlossaryService:
    def __init__(self):
        data_file = Path(__file__).parent.parent.parent / "data" / "glossary.json"
        with open(data_file, 'r', encoding='utf-8') as f:
            self.glossary = json.load(f)

    def get_term(self, key: str, language: LanguageCode) -> str:
        """Returns the translated term for the requested language. Falls back to English."""
        if key in self.glossary:
            return self.glossary[key].get(language.value, self.glossary[key].get("en", key))
        return key

    def get_disclaimer(self, language: LanguageCode) -> str:
        return self.get_term("disclaimer", language)
