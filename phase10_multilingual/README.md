# LegalAId - Phase 10 Multilingual Module

This is the standalone Multilingual NLP module for **LegalAId**. 
It is responsible for parsing English, Hindi, and Hinglish/Roman Hindi input, translating legal documents, normalizing input to pass to the Legal Engine, and formatting structured legal responses back into the user's selected language.

## Architecture
The module is built as an independent microservice using **FastAPI** to easily integrate with the rest of the project.
The internal pipeline follows a robust execution path:
`Detect -> Protect Entities -> Normalize -> Legal Engine -> Translate -> Restore Entities -> Validate`

## Installation
1. Navigate to this directory.
2. Ensure you have Python 3.10+ installed.
3. Install the dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Copy the environment variables:
   ```bash
   cp .env.example .env
   ```
   Add your OpenAI API Key if you want to test the LLM-based robust Hinglish parser and translator. Otherwise, you can use the `mock` TRANSLATION_PROVIDER.

## Running the API
To start the FastAPI development server:
```bash
uvicorn src.main:app --reload
```
You can then visit `http://127.0.0.1:8000/docs` to see the interactive Swagger UI API documentation.

## Running Tests
To run all unit and integration tests (they default to using the Mock Translation Provider and Mock Legal Engine):
```bash
pytest tests/ -v
```

## Supported Languages
- **Input**: English (`en`), Hindi (`hi`), Roman Hindi (`roman_hi`), Hinglish (`hinglish`)
- **Output**: English (`en`), Hindi (`hi`)

## API Endpoints
- `POST /api/language/process`: Main endpoint. Takes user text and desired output language, handles detection, normalization, legal engine processing, and output formatting.
- `POST /api/language/document`: Handles document generation translation, protecting legal placeholders.

## Error Handling, Privacy, and Security
- Protected legal entities (Section numbers, exact dates, amounts) are converted to secure placeholders and strictly restored after translation.
- Empty or unsupported language inputs gracefully fail with structured HTTP 400 responses.
- Translation or Legal Engine failures return HTTP 503 rather than guessing legal content.
- User input is NOT permanently logged to protect privacy.

## Mock Engine
A `MockLegalEngine` is included in `src/adapters/mock_legal_engine.py` for testing scenarios related to Consumers, Tenants, and Labour disputes. This can be easily replaced by implementing a new adapter that calls the real LegalAId API once it's ready.
