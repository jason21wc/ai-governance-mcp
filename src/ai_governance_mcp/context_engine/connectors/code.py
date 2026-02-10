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

    # L3: Language-aware boundary patterns for chunk splitting
    # Each language has patterns that indicate logical code boundaries
    BOUNDARY_PATTERNS: dict[str, list[str]] = {
        "python": ["class ", "def ", "async def ", "@"],
        "javascript": [
            "class ",
            "function ",
            "export ",
            "const ",
            "let ",
            "var ",
            "async function ",
        ],
        "typescript": [
            "class ",
            "function ",
            "export ",
            "const ",
            "let ",
            "interface ",
            "type ",
            "async function ",
        ],
        "java": [
            "class ",
            "interface ",
            "enum ",
            "public ",
            "private ",
            "protected ",
            "@",
        ],
        "go": ["func ", "type ", "const ", "var ", "package "],
        "rust": ["fn ", "struct ", "enum ", "impl ", "trait ", "mod ", "pub "],
        "ruby": ["class ", "def ", "module ", "private", "protected", "public"],
        "c": [
            "int ",
            "void ",
            "char ",
            "struct ",
            "enum ",
            "typedef ",
            "#define ",
            "#include ",
        ],
        "cpp": [
            "class ",
            "struct ",
            "enum ",
            "namespace ",
            "template ",
            "int ",
            "void ",
            "#define ",
            "#include ",
        ],
        "c_sharp": [
            "class ",
            "interface ",
            "struct ",
            "enum ",
            "namespace ",
            "public ",
            "private ",
            "protected ",
        ],
        "swift": [
            "class ",
            "struct ",
            "enum ",
            "func ",
            "protocol ",
            "extension ",
            "@",
        ],
        "kotlin": [
            "class ",
            "fun ",
            "object ",
            "interface ",
            "data class ",
            "sealed class ",
        ],
        "scala": ["class ", "object ", "trait ", "def ", "val ", "var ", "case class "],
        "bash": ["function ", "() {"],
    }

    # Default patterns for languages without specific definitions
    DEFAULT_BOUNDARY_PATTERNS = ["class ", "def ", "function ", "export "]

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

    def parse(
        self, file_path: Path, project_root: Path | None = None
    ) -> list[ContentChunk]:
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

        # Compute display path (relative to project root when available)
        if project_root and file_path.is_relative_to(project_root):
            display_path = str(file_path.relative_to(project_root))
        else:
            display_path = str(file_path)

        if self._tree_sitter_available:
            return self._parse_with_tree_sitter(file_path, content, display_path)
        return self._parse_line_based(file_path, content, display_path)

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
        self, file_path: Path, content: str, display_path: str
    ) -> list[ContentChunk]:
        """Parse using Tree-sitter AST for language-aware chunking.

        TODO: Implement Tree-sitter parsing. This requires:
        1. Loading the appropriate language grammar
        2. Parsing the file into an AST
        3. Extracting top-level definitions (functions, classes, methods)
        4. Creating chunks at logical boundaries
        """
        # Placeholder: fall back to line-based parsing until Tree-sitter is integrated
        return self._parse_line_based(file_path, content, display_path)

    def _parse_line_based(
        self, file_path: Path, content: str, display_path: str
    ) -> list[ContentChunk]:
        """Fall back to line-based chunking.

        Splits content into chunks at logical boundaries (blank lines,
        class/function definitions) with a target chunk size.
        Uses L3 language-aware boundary patterns for better chunking.
        """
        lines = content.split("\n")
        chunks: list[ContentChunk] = []
        chunk_lines: list[str] = []
        chunk_start = 1
        target_chunk_size = 50  # lines

        # L3: Get language-specific boundary patterns
        language = self.LANGUAGE_MAP.get(file_path.suffix.lower(), "unknown")
        boundary_patterns = self.BOUNDARY_PATTERNS.get(
            language, self.DEFAULT_BOUNDARY_PATTERNS
        )

        for i, line in enumerate(lines, start=1):
            chunk_lines.append(line)

            # Split at logical boundaries near target size
            # L3: Use language-specific patterns
            is_boundary = len(chunk_lines) >= target_chunk_size and (
                line.strip() == ""
                or any(line.lstrip().startswith(p) for p in boundary_patterns)
            )

            # Hard split at 4x target to prevent single massive chunks
            # when no boundary pattern matches (e.g., minified code)
            force_split = len(chunk_lines) >= target_chunk_size * 4

            if is_boundary or force_split or i == len(lines):
                chunk_content = "\n".join(chunk_lines)
                if chunk_content.strip():
                    chunks.append(
                        ContentChunk(
                            content=chunk_content,
                            source_path=display_path,
                            start_line=chunk_start,
                            end_line=i,
                            content_type="code",
                            language=language,
                        )
                    )
                chunk_lines = []
                chunk_start = i + 1

        return chunks
