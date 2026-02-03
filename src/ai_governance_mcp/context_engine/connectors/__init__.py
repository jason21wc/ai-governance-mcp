"""Source connectors for parsing different content types.

Each connector parses project content into indexable chunks appropriate
for its content type. Connectors implement the BaseConnector interface.
"""

from .base import BaseConnector

__all__ = ["BaseConnector"]
