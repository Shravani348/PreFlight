"""Pytest configuration and environment setup for AI tests."""

import pathlib
import sys

# Ensure repository root is on sys.path so 'ai' package is resolved correctly
REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
