"""Storage backends for context engine indexes.

Supports local filesystem storage (default) and extensible to
remote storage (S3) for team sharing.
"""

from .base import BaseStorage

__all__ = ["BaseStorage"]
