"""Code connector for parsing source code files.

Parses code by language-aware structure (functions, classes, modules)
using Tree-sitter for accurate AST-based chunking. Falls back to
line-based chunking when Tree-sitter grammars are not available.
"""

from pathlib import Path

from .base import BaseConnector
from ..models import ContentChunk, FileMetadata


class CodeConnector(BaseConnector):
    """Connector for source code files.

    Uses Tree-sitter for language-aware parsing when available,
    with fallback to line-based chunking for unsupported languages.
    """

    # Common code file extensions mapped to Tree-sitter language names
    LANGUAGE_MAP: dict[str, str] = {
        ".py": "python",
        ".js": "javascript",
        ".ts": "typescript",
        ".jsx": "javascript",
        ".tsx": "typescript",
        ".java": "java",
        ".go": "go",
        ".rs": "rust",
        ".rb": "ruby",
        ".c": "c",
        ".cpp": "cpp",
        ".h": "c",
        ".hpp": "cpp",
        ".cs": "c_sharp",
        ".swift": "swift",
        ".kt": "kotlin",
        ".scala": "scala",
        ".sh": "bash",
        ".bash": "bash",
        ".zsh": "bash",
        ".toml": "toml",
        ".yaml": "yaml",
        ".yml": "yaml",
        ".json": "json",
        ".xml": "xml",
        ".html": "html",
        ".css": "css",
        ".sql": "sql",
    }

    def __init__(self) -> None:
        """Initialize the code connector."""
        self._tree_sitter_available = False
        try:
            import tree_sitter  # noqa: F401

            self._tree_sitter_available = True
        except ImportError:
            pass

    @property
    def supported_extensions(self) -> set[str]:
        """File extensions this connector handles."""
        return set(self.LANGUAGE_MAP.keys())

    def can_handle(self, file_path: Path) -> bool:
        """Check if this connector can handle the given file."""
        return file_path.suffix.lower() in self.supported_extensions

    def parse(self, file_path: Path) -> list[ContentChunk]:
        """Parse a code file into indexable chunks.

        Uses Tree-sitter for AST-based chunking when available,
        falls back to line-based chunking otherwise.
        """
        try:
            content = file_path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            return []

        if not content.strip():
            return []

        if self._tree_sitter_available:
            return self._parse_with_tree_sitter(file_path, content)
        return self._parse_line_based(file_path, content)

    def extract_metadata(self, file_path: Path) -> FileMetadata:
        """Extract metadata from a code file."""
        stat = file_path.stat()
        return FileMetadata(
            path=str(file_path),
            content_type="code",
            language=self.LANGUAGE_MAP.get(file_path.suffix.lower(), "unknown"),
            size_bytes=stat.st_size,
            last_modified=stat.st_mtime,
        )

    def _parse_with_tree_sitter(
        self, file_path: Path, content: str
    ) -> list[ContentChunk]:
        """Parse using Tree-sitter AST for language-aware chunking.

        TODO: Implement Tree-sitter parsing. This requires:
        1. Loading the appropriate language grammar
        2. Parsing the file into an AST
        3. Extracting top-level definitions (functions, classes, methods)
        4. Creating chunks at logical boundaries
        """
        # Placeholder: fall back to line-based parsing until Tree-sitter is integrated
        return self._parse_line_based(file_path, content)

    def _parse_line_based(self, file_path: Path, content: str) -> list[ContentChunk]:
        """Fall back to line-based chunking.

        Splits content into chunks at logical boundaries (blank lines,
        class/function definitions) with a target chunk size.
        """
        lines = content.split("\n")
        chunks: list[ContentChunk] = []
        chunk_lines: list[str] = []
        chunk_start = 1
        target_chunk_size = 50  # lines

        for i, line in enumerate(lines, start=1):
            chunk_lines.append(line)

            # Split at logical boundaries near target size
            is_boundary = len(chunk_lines) >= target_chunk_size and (
                line.strip() == ""
                or line.startswith("class ")
                or line.startswith("def ")
                or line.startswith("function ")
                or line.startswith("export ")
            )

            if is_boundary or i == len(lines):
                chunk_content = "\n".join(chunk_lines)
                if chunk_content.strip():
                    chunks.append(
                        ContentChunk(
                            content=chunk_content,
                            source_path=str(file_path),
                            start_line=chunk_start,
                            end_line=i,
                            content_type="code",
                            language=self.LANGUAGE_MAP.get(
                                file_path.suffix.lower(), "unknown"
                            ),
                        )
                    )
                chunk_lines = []
                chunk_start = i + 1

        return chunks
