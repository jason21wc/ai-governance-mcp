"""Context Engine MCP Server for project content indexing and retrieval.

Provides persistent semantic indexing of project content (code, documents,
configurations) enabling AI assistants to discover and retrieve relevant
information without manually reading files.

Architecture: One shared MCP server managing multiple project indexes,
auto-detecting working directory for per-project index management.
"""

__version__ = "0.1.0"
