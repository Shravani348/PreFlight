"""Single integration boundary between the backend and the AI document-intelligence module.

The backend never touches classification, extraction, normalization, matching or
prompt internals. It hands uploaded files to ``AIPipeline.process`` and receives an
``AIProcessingResult``. Uploaded bytes are written to a throw-away temporary
directory that is removed before this function returns, so documents are never
persisted by the backend.
"""

import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from ai.pipeline import AIPipeline
from ai.schemas.result import AIProcessingResult

_pipeline: Optional[AIPipeline] = None


@dataclass
class UploadedDocument:
    """A file received by the upload endpoint together with the slot it was uploaded in."""

    slot: str
    filename: str
    content: bytes


def get_pipeline() -> AIPipeline:
    """Return the shared AI pipeline (offline/deterministic unless a provider is injected)."""
    global _pipeline
    if _pipeline is None:
        _pipeline = AIPipeline()
    return _pipeline


def set_pipeline(pipeline: Optional[AIPipeline]) -> None:
    """Override the shared pipeline (used to inject a vision/LLM model client or in tests)."""
    global _pipeline
    _pipeline = pipeline


def _unique_name(name: str, taken: set) -> str:
    """Keep the original file name as the AI document id, disambiguating duplicates."""
    if name not in taken:
        return name
    stem, suffix = Path(name).stem, Path(name).suffix
    counter = 2
    while f"{stem} ({counter}){suffix}" in taken:
        counter += 1
    return f"{stem} ({counter}){suffix}"


def process_uploads(
    uploads: List[UploadedDocument],
    pipeline: Optional[AIPipeline] = None,
) -> Tuple[AIProcessingResult, Dict[str, UploadedDocument]]:
    """Run the AI pipeline on uploaded files.

    Returns the AI result and a mapping of AI ``document_id`` (file name) -> upload,
    so the adapter can relate AI documents back to the slot they were uploaded in.
    Unreadable files do not abort the run (``allow_partial_failure=True``); they come
    back as UNKNOWN documents carrying a ``processing_error`` field.
    """
    ai = pipeline or get_pipeline()
    id_map: Dict[str, UploadedDocument] = {}
    with tempfile.TemporaryDirectory(prefix="preflight_", ignore_cleanup_errors=True) as tmp:
        paths: List[Path] = []
        for index, upload in enumerate(uploads):
            name = _unique_name(Path(upload.filename).name or "upload", set(id_map))
            folder = Path(tmp) / str(index)
            folder.mkdir()
            target = folder / name
            target.write_bytes(upload.content)
            id_map[name] = upload
            paths.append(target)
        result = ai.process(document_paths=paths, allow_partial_failure=True)
    return result, id_map
