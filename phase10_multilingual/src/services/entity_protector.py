import re
from typing import Dict, Tuple

class EntityProtector:
    """
    Protects important legal entities (Act names, Sections, Currency, Dates, Emails, etc.)
    by replacing them with placeholders before translation, and restoring them after.
    """
    def __init__(self):
        # Extremely basic patterns for demonstration. 
        # In a real-world scenario, this might use Spacy or a robust NER model.
        self.patterns = [
            # Acts (e.g., "Consumer Protection Act, 2019")
            re.compile(r'\b[A-Z][a-zA-Z\s]+Act,\s*\d{4}\b'),
            # Sections/Rules/Articles (e.g., "Section 35", "Article 21")
            re.compile(r'\b(?:Section|Rule|Article)\s+\d+[A-Z]?\b', re.IGNORECASE),
            # Currency (e.g., ₹30,000, Rs. 5000)
            re.compile(r'(?:₹|Rs\.?)\s*[\d,]+\b', re.IGNORECASE),
            # Dates (e.g., 15 July 2026, 2026-07-15)
            re.compile(r'\b\d{1,2}\s+[A-Za-z]+\s+\d{4}\b'),
            # Emails
            re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
            # Phone numbers
            re.compile(r'\b(?:\+?\d{1,3}[\s-]?)?(?:\d{10}|\d{3}-\d{3}-\d{4})\b'),
            # URLs
            re.compile(r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+'),
            # Case/Reference Numbers (e.g., Case No. 123/2023, Ref: 456)
            re.compile(r'\b(?:Case No\.|Ref\.?|Reference)\s*[:\-]?\s*[A-Za-z0-9/]+\b', re.IGNORECASE),
            # Companies (Basic match for common suffixes)
            re.compile(r'\b[A-Z][a-zA-Z0-9-]+\s(?:Company|Corp|Inc|Ltd|Private Limited)\b', re.IGNORECASE),
            # Addresses (very basic heuristics starting with numbers)
            re.compile(r'\b\d{1,4}[A-Za-z]?\s[A-Za-z\s]+(?:Road|Street|St|Avenue|Ave|Lane|Marg)\b', re.IGNORECASE),
            # Names (Basic two capitalized words, placed lower priority)
            re.compile(r'\b[A-Z][a-z]+\s[A-Z][a-z]+\b'),
            # Simple numbers (e.g. 2, 3000)
            re.compile(r'\b\d+\b')
        ]

    def protect(self, text: str) -> Tuple[str, Dict[str, str]]:
        if not text:
            return text, {}
            
        protected_text = text
        mapping = {}
        placeholder_idx = 0
        
        for pattern in self.patterns:
            def repl(match):
                nonlocal placeholder_idx
                entity = match.group(0)
                # Check if we already mapped this exact string
                for ph, ent in mapping.items():
                    if ent == entity:
                        return ph
                        
                placeholder = f"__PROTECTED_ENTITY_{placeholder_idx}__"
                mapping[placeholder] = entity
                placeholder_idx += 1
                return placeholder
                
            protected_text = pattern.sub(repl, protected_text)
            
        return protected_text, mapping

    def restore(self, text: str, mapping: Dict[str, str]) -> str:
        if not text:
            return text
            
        restored_text = text
        for placeholder, entity in mapping.items():
            restored_text = restored_text.replace(placeholder, entity)
        return restored_text
