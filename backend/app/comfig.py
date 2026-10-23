"""Backward-compatible import shim for the historical misspelling.

New code must import from ``backend.app.config``.
"""

from backend.app.config import Settings, settings

__all__ = ["Settings", "settings"]
