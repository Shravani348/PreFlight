"""Tests for AI module."""

import pathlib
import sys

_repo_root = pathlib.Path(__file__).resolve().parent.parent.parent
_real_ai = _repo_root / "ai"

if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))

if str(_real_ai) not in __path__:
    __path__.append(str(_real_ai))
