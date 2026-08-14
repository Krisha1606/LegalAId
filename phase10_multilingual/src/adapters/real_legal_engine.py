import asyncio
import sys
from pathlib import Path
from typing import Any

# Ensure project root is in sys.path for LegalAId imports
root_path = Path(__file__).resolve().parent.parent.parent.parent
if str(root_path) not in sys.path:
    sys.path.insert(0, str(root_path))

# Ensure phase10_multilingual is in sys.path
p10_path = Path(__file__).resolve().parent.parent.parent
if str(p10_path) not in sys.path:
    sys.path.insert(0, str(p10_path))

try:
    from src.schemas.legal_response import ApplicableLaw, LegalEngineResponse
except ImportError:
    from phase10_multilingual.src.schemas.legal_response import ApplicableLaw, LegalEngineResponse

from src.generator import GroundedResponse, LegalGenerator


class RealLegalEngineAdapter:
    """Adapter connecting Phase 10 Multilingual Processor to LegalAId's RAG + Ollama Engine."""

    def __init__(self, generator: LegalGenerator | None = None) -> None:
        """Initializes the adapter.

        Args:
            generator: Optional LegalGenerator instance. Defaults to new instance.
        """
        self.generator = generator or LegalGenerator()

    def _extract_recommended_actions(self, answer: str, sources: list[dict[str, Any]]) -> list[str]:
        """Derives actionable legal guidance bullet points from generated answer and sources."""
        actions: list[str] = []

        # Parse lines looking for action bullets or recommendations
        for line in answer.splitlines():
            cleaned = line.strip()
            if cleaned.startswith(("-", "*", "1.", "2.", "3.", "4.", "5.")):
                action_text = cleaned.lstrip("-*0123456789. ").strip()
                if len(action_text) > 10 and not action_text.lower().startswith("citation"):
                    actions.append(action_text)

        # Fallback standard actionable guidance if no specific bullets were parsed
        if not actions:
            actions = [
                "Preserve all relevant documentation, receipts, contracts, or notices.",
                "Send a formal legal notice detailing your claim and seeking redress.",
                "Approach the appropriate legal forum, tribunal, or consumer commission if unresolved.",
            ]

        return actions[:5]

    def _extract_citations(self, sources: list[dict[str, Any]]) -> list[str]:
        """Formats citation strings from retrieved qualified sources."""
        citations: list[str] = []
        seen = set()

        for s in sources:
            act = s.get("act", "").strip()
            section = s.get("section", "").strip()
            sec_title = s.get("section_title", "").strip()

            if act and section:
                cit = f"{act}, {section}"
                if sec_title:
                    cit += f" ({sec_title})"
                if cit not in seen:
                    seen.add(cit)
                    citations.append(cit)

        return citations

    def transform_response(self, grounded_resp: GroundedResponse) -> LegalEngineResponse:
        """Transforms a GroundedResponse dataclass into a Phase 10 LegalEngineResponse schema object."""
        applicable_laws: list[ApplicableLaw] = []
        seen_laws = set()

        for src in grounded_resp.sources:
            act = src.get("act", "Unknown Act").strip()
            section = src.get("section", "N/A").strip()
            explanation = src.get("section_title") or src.get("issue") or f"Legal provision under {act}"
            source_url = src.get("source_url") or src.get("source")

            law_key = (act, section)
            if law_key not in seen_laws:
                seen_laws.add(law_key)
                applicable_laws.append(
                    ApplicableLaw(
                        act=act,
                        section=section,
                        explanation=explanation,
                        source=source_url,
                    )
                )

        recommended_actions = self._extract_recommended_actions(
            grounded_resp.answer, grounded_resp.sources
        )
        citations = self._extract_citations(grounded_resp.sources)

        return LegalEngineResponse(
            rights_explanation=grounded_resp.answer,
            applicable_laws=applicable_laws,
            recommended_actions=recommended_actions,
            document=None,
            citations=citations,
        )

    async def get_response(self, text: str) -> LegalEngineResponse:
        """Asynchronously executes LegalAId RAG generation and returns Phase 10 LegalEngineResponse.

        Args:
            text: User's normalized English legal query statement.

        Returns:
            LegalEngineResponse object adhering to Phase 10 integration contract.
        """
        # Run synchronous RAG generator in executor thread to avoid blocking async event loop
        loop = asyncio.get_event_loop()
        grounded_resp: GroundedResponse = await loop.run_in_executor(
            None, self.generator.generate, text
        )
        return self.transform_response(grounded_resp)
