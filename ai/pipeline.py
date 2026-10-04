"""PreFlight AI pipeline orchestration."""

from typing import Any


class AIPipeline:
    """Orchestrates the end-to-end AI document validation pipeline."""

    def run(self, document_inputs: Any) -> Any:
        """Execute the pipeline on input documents."""
        raise NotImplementedError
