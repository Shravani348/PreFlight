"""Vision-capable model adapter isolating LLM/vision API provider details."""

from typing import Any, Callable, Dict, List, Optional
from PIL import Image

from ai.config import AIConfig, config as default_config
from ai.exceptions import ExtractionError
from ai.schemas.document import DocumentType


class VisionExtractor:
    """Adapter for vision-capable models, isolating vendor APIs and supporting offline testing.

    Accepts text context and/or page images and returns structured extracted data dictionaries.
    A custom model_client callable can be injected for testing or swapping LLM backends
    (e.g., Google Gemini, OpenAI, Claude) without modifying extraction pipeline logic.
    """

    def __init__(
        self,
        config: Optional[AIConfig] = None,
        model_client: Optional[
            Callable[[str, Optional[str], Optional[List[Image.Image]], DocumentType], Dict[str, Any]]
        ] = None,
    ) -> None:
        """Initialize adapter with configuration and optional mock/custom client."""
        self.config = config or default_config
        self.model_client = model_client

    def extract(
        self,
        prompt: str,
        text_content: Optional[str] = None,
        images: Optional[List[Image.Image]] = None,
        document_type: DocumentType = DocumentType.UNKNOWN,
    ) -> Dict[str, Any]:
        """Execute extraction through configured model client or adapter boundary.

        Args:
            prompt: Structured extraction instructions and schema definition.
            text_content: Extracted selectable text from the preprocessed document.
            images: Rendered or embedded images for vision analysis.
            document_type: Classified document type.

        Returns:
            Dict[str, Any]: Structured dictionary of extracted fields.

        Raises:
            ExtractionError: If extraction fails or model output is unavailable.
        """
        # 1. Custom or Mocked model client (used in tests and custom provider setups)
        if self.model_client is not None:
            try:
                result = self.model_client(prompt, text_content, images, document_type)
                if not isinstance(result, dict):
                    raise ExtractionError(
                        f"Model client returned non-dictionary response: {type(result).__name__}"
                    )
                return result
            except ExtractionError:
                raise
            except Exception as exc:
                raise ExtractionError(f"Model client extraction execution failed: {exc}") from exc

        # 2. Live API boundary (when API key is present in environment)
        if self.config.api_key:
            # Here real provider SDK (e.g. google-genai or openai) would be invoked.
            # Kept isolated so the rest of the application is completely decoupled.
            raise ExtractionError(
                "Live LLM provider adapter is not configured with a concrete SDK implementation yet. "
                "Inject a model_client or mock provider."
            )

        # 3. Offline / Unconfigured fallback
        # When no model client and no API key are provided, return an empty dictionary
        return {}
