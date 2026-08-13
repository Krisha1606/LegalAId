# PHASE 10 INTEGRATION CONTRACT

This document outlines the interfaces and expected contracts between the Multilingual module (Phase 10) and the rest of the LegalAId system (Phases 1-9).

## Required Input from Legal Engine (Phases 1-9)
When Phase 10 calls the Legal Engine, it expects a structured JSON response to format and translate. 

**Expected Schema from Legal Engine:**
```json
{
  "rights_explanation": "String explaining the core rights.",
  "applicable_laws": [
    {
      "act": "Name of the Act (e.g., Consumer Protection Act, 2019)",
      "section": "Section identifier (e.g., Section 35)",
      "explanation": "Explanation of the law.",
      "source": "URL or citation string"
    }
  ],
  "recommended_actions": [
    "String of action 1",
    "String of action 2"
  ],
  "document": {
    "type": "legal_notice",
    "content": "Raw document content string."
  },
  "citations": ["String of citation 1"]
}
```

## Expected Output from Phase 10
When the frontend or main backend API calls Phase 10's `/api/language/process` endpoint, Phase 10 will return the fully localized, structured data.

**Phase 10 Output Schema:**
```json
{
  "language": {
    "input": "roman_hi",
    "output": "hi"
  },
  "rights_explanation": "उपभोक्ता को दोषपूर्ण वस्तुओं के संबंध में कुछ कानूनी अधिकार प्राप्त हो सकते हैं।",
  "applicable_laws": [
    {
      "act": "Consumer Protection Act, 2019",
      "section": "Section 35",
      "explanation": "...",
      "source": "..."
    }
  ],
  "recommended_actions": [
    "..."
  ],
  "document": {
    "type": "legal_notice",
    "language": "hi",
    "content": "..."
  },
  "disclaimer": "यह जानकारी केवल सामान्य सूचना और शैक्षिक उद्देश्यों के लिए प्रदान की गई है और इसे कानूनी सलाह नहीं माना जाना चाहिए। अपनी विशेष परिस्थितियों के संबंध में सलाह के लिए योग्य कानूनी पेशेवर से परामर्श करें।"
}
```

## How to replace the Mock Engine with the Real Engine
1. Go to `src/services/multilingual_processor.py`.
2. Find where the `MockLegalEngine` is instantiated or injected.
3. Replace it with a new class (e.g., `RealLegalEngineAdapter`) that makes HTTP requests to your actual Phase 1-9 backend API.
4. Ensure your actual backend API returns the exact JSON structure defined above.
