import json
from pathlib import Path
from phase10_multilingual.src.schemas.legal_response import LegalEngineResponse

class MockLegalEngine:
    def __init__(self):
        data_file = Path(__file__).parent.parent.parent / "data" / "mock_responses.json"
        with open(data_file, 'r', encoding='utf-8') as f:
            self.data = json.load(f)

    async def get_response(self, text: str) -> LegalEngineResponse:
        text_lower = text.lower()
        if "salary" in text_lower or "employer" in text_lower or "wages" in text_lower:
            key = "labour_salary"
        elif "deposit" in text_lower or "landlord" in text_lower or "tenant" in text_lower:
            key = "tenant_deposit"
        elif "defective" in text_lower or "refund" in text_lower or "seller" in text_lower or "product" in text_lower:
            key = "consumer_defective"
        else:
            # Default to consumer if ambiguous for mock purposes
            key = "consumer_defective"
            
        return LegalEngineResponse(**self.data[key])
