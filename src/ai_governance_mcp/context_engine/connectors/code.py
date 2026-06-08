"""Code connector for parsing source code files.

Parses code by language-aware structure (functions, classes, modules)
using Tree-sitter for accurate AST-based chunking. Falls back to
line-based chunking when Tree-sitter grammars are not available.
"""

from pathlib import Path

from .base import BaseConnector
from ..models import ContentChunk, FileMetadata


# Priority languages with tree-sitter AST parsing support.
# All others fall back to line-based chunking even when tree-sitter is available.
TREE_SITTER_LANGUAGES = {"python", "javascript", "typescript", "go", "rust", "java"}

# Node types considered top-level definitions per language.
# These are the AST node types that tree-sitter produces for each language.
DEFINITION_NODE_TYPES: dict[str, set[str]] = {
    "python": {"function_definition", "class_definition", "decorated_definition"},
    "javascript": {
        "function_declaration",
        "class_declaration",
        "export_statement",
    },
    "typescript": {
        "function_declaration",
        "class_declaration",
        "export_statement",
    },
    "go": {"function_declaration", "method_declaration", "type_declaration"},
    "rust": {"function_item", "impl_item", "struct_item", "enum_item", "trait_item"},
    "java": {"class_declaration", "method_declaration", "interface_declaration"},
}

# Body node types that may contain nested definitions (e.g., methods in a class).
BODY_NODE_TYPES = {
    "block",
    "class_body",
    "statement_block",
    "declaration_list",
    "interface_body",
}

# Definitions larger than this are split at nested boundaries.
MAX_DEFINITION_LINES = 200

# Import enrichment constants
MAX_IMPORT_COUNT = 5
MAX_IMPORT_CONTEXT_CHARS = 400

# Python AST node types for import statements
PYTHON_IMPORT_NODE_TYPES = {"import_statement", "import_from_statement"}


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
            import tree_sitter_language_pack  # noqa: F401

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

        For priority languages, parses the AST and creates one chunk per
        top-level definition (function, class, etc.) with heading set to
        the definition name. Non-definition code (imports, constants)
        becomes "preamble" chunks. Definitions > 200 lines are split at
        nested definition boundaries (e.g., methods within a class).

        Falls back to line-based parsing for non-priority languages or
        on any parse error.
        """
        language = self.LANGUAGE_MAP.get(file_path.suffix.lower())

        # Only use tree-sitter for priority languages
        if language not in TREE_SITTER_LANGUAGES:
            return self._parse_line_based(file_path, content, display_path)

        try:
            from tree_sitter_language_pack import get_parser

            parser = get_parser(language)
            tree = parser.parse(content.encode("utf-8"))
        except Exception:
            return self._parse_line_based(file_path, content, display_path)

        root = tree.root_node
        lines = content.split("\n")
        definitions = self._extract_definitions(root, language)

        if not definitions:
            return self._parse_line_based(file_path, content, display_path)

        # Collect import nodes for enrichment (Python only)
        import_nodes: list[tuple[str, object]] = []
        if language == "python":
            for child in root.children:
                if child.type in PYTHON_IMPORT_NODE_TYPES:
                    import_nodes.append((child.text.decode("utf-8"), child))

        chunks: list[ContentChunk] = []
        covered_end = 0  # Next uncovered line (0-indexed)

        for node, name in definitions:
            start_row = node.start_point[0]
            end_row = node.end_point[0]

            # Gap before this definition -> preamble chunk
            if start_row > covered_end:
                gap = "\n".join(lines[covered_end:start_row])
                if gap.strip():
                    chunks.append(
                        ContentChunk(
                            content=gap,
                            source_path=display_path,
                            start_line=covered_end + 1,
                            end_line=start_row,
                            content_type="code",
                            language=language,
                            heading="preamble",
                        )
                    )

            def_line_count = end_row - start_row + 1

            if def_line_count > MAX_DEFINITION_LINES:
                # Split large definitions at nested boundaries
                sub = self._split_large_definition(
                    node, lines, display_path, language, name
                )
                # Enrich split chunks with import context
                if import_nodes:
                    for chunk in sub:
                        if chunk.heading != "preamble":
                            chunk.import_context = self._filter_imports_for_chunk(
                                import_nodes, node
                            )
                chunks.extend(sub)
            else:
                # Compute import context for this definition chunk
                import_ctx = None
                if import_nodes:
                    import_ctx = self._filter_imports_for_chunk(import_nodes, node)

                def_content = "\n".join(lines[start_row : end_row + 1])
                if def_content.strip():
                    chunks.append(
                        ContentChunk(
                            content=def_content,
                            source_path=display_path,
                            start_line=start_row + 1,
                            end_line=end_row + 1,
                            content_type="code",
                            language=language,
                            heading=name,
                            import_context=import_ctx,
                        )
                    )

            covered_end = end_row + 1

        # Epilogue after last definition
        if covered_end < len(lines):
            epilogue = "\n".join(lines[covered_end:])
            if epilogue.strip():
                chunks.append(
                    ContentChunk(
                        content=epilogue,
                        source_path=display_path,
                        start_line=covered_end + 1,
                        end_line=len(lines),
                        content_type="code",
                        language=language,
                        heading="preamble",
                    )
                )

        if not chunks:
            return self._parse_line_based(file_path, content, display_path)

        return chunks

    # ─── Import enrichment helpers (Python only) ───

    def _extract_import_lines(self, root) -> list[str]:
        """Extract import statement text from Python AST root node.

        Returns list of import line strings (e.g., 'import os', 'from pathlib import Path').
        Only processes top-level import_statement and import_from_statement nodes.
        """
        lines = []
        for child in root.children:
            if child.type in PYTHON_IMPORT_NODE_TYPES:
                lines.append(child.text.decode("utf-8"))
        return lines

    def _get_imported_names(self, import_line: str, node) -> list[str]:
        """Extract the usable names from an import AST node.

        For 'import numpy as np' → ['np'] (alias takes precedence)
        For 'from os.path import join, exists' → ['join', 'exists']
        For 'from foo import *' → ['*']
        For 'import os' → ['os']
        """
        names = []
        if node.type == "import_from_statement":
            # Check for star import
            for child in node.children:
                if child.type == "wildcard_import":
                    return ["*"]

            # Look for imported names (skip the module path)
            module_node = node.child_by_field_name("module_name")
            for child in node.children:
                if child.type == "dotted_name" and child is not module_node:
                    # This is an imported name (not the module path)
                    names.append(child.text.decode("utf-8"))
                elif child.type == "aliased_import":
                    alias = child.child_by_field_name("alias")
                    if alias:
                        names.append(alias.text.decode("utf-8"))
                    else:
                        name = child.child_by_field_name("name")
                        if name:
                            names.append(name.text.decode("utf-8"))
        elif node.type == "import_statement":
            for child in node.children:
                if child.type == "aliased_import":
                    alias = child.child_by_field_name("alias")
                    if alias:
                        names.append(alias.text.decode("utf-8"))
                    else:
                        name = child.child_by_field_name("name")
                        if name:
                            # For 'import os.path', the usable name is 'os'
                            full = name.text.decode("utf-8")
                            names.append(full.split(".")[0])
                elif child.type == "dotted_name":
                    full = child.text.decode("utf-8")
                    names.append(full.split(".")[0])
        return names

    def _get_identifier_names_in_node(self, node) -> set[str]:
        """Collect all identifier token text within an AST node (recursive).

        Used to determine which imports are actually referenced in a function body.
        """
        names: set[str] = set()
        if node.type == "identifier":
            names.add(node.text.decode("utf-8"))
        for child in node.children:
            names.update(self._get_identifier_names_in_node(child))
        return names

    def _filter_imports_for_chunk(
        self, import_nodes: list[tuple[str, object]], chunk_node
    ) -> str | None:
        """Filter imports to only those referenced in the chunk's function body.

        Args:
            import_nodes: List of (import_line_text, ast_node) tuples.
            chunk_node: The AST node for the function/class definition.

        Returns:
            Filtered import context string, or None if no relevant imports.
            Capped at MAX_IMPORT_COUNT imports and MAX_IMPORT_CONTEXT_CHARS characters.
        """
        if not import_nodes:
            return None

        body_identifiers = self._get_identifier_names_in_node(chunk_node)
        relevant = []

        for line, node in import_nodes:
            names = self._get_imported_names(line, node)
            # Star imports are always included (we can't know what they provide)
            if "*" in names:
                relevant.append(line)
            elif any(name in body_identifiers for name in names):
                relevant.append(line)

            if len(relevant) >= MAX_IMPORT_COUNT:
                break

        if not relevant:
            return None

        result = "\n".join(relevant)
        if len(result) > MAX_IMPORT_CONTEXT_CHARS:
            # Truncate at last complete line boundary
            truncated = result[:MAX_IMPORT_CONTEXT_CHARS]
            last_newline = truncated.rfind("\n")
            if last_newline > 0:
                result = truncated[:last_newline]
            else:
                result = truncated
        return result

    def _extract_definitions(self, root, language: str) -> list[tuple]:
        """Extract top-level definition nodes from the AST.

        Returns list of (node, name) tuples for top-level definitions.
        """
        def_types = DEFINITION_NODE_TYPES.get(language, set())
        definitions = []

        for child in root.children:
            if child.type in def_types:
                name = self._get_definition_name(child, language)
                definitions.append((child, name))

        return definitions

    def _get_definition_name(self, node, language: str) -> str | None:
        """Extract the human-readable name of a definition node."""
        # Handle Python decorated definitions -- unwrap to the actual definition
        if node.type == "decorated_definition":
            definition = node.child_by_field_name("definition")
            if definition:
                return self._get_definition_name(definition, language)
            return None

        # Handle JS/TS export statements -- look for the wrapped declaration
        if node.type == "export_statement":
            def_types = DEFINITION_NODE_TYPES.get(language, set())
            for child in node.children:
                if child.type in def_types and child.type != "export_statement":
                    return self._get_definition_name(child, language)
            # Fallback: check 'declaration' field
            declaration = node.child_by_field_name("declaration")
            if declaration:
                return self._get_definition_name(declaration, language)
            return "export"

        # Standard: look for 'name' field
        name_node = node.child_by_field_name("name")
        if name_node:
            return name_node.text.decode("utf-8")

        # Rust impl: use 'type' field for the impl target
        if node.type == "impl_item":
            type_node = node.child_by_field_name("type")
            if type_node:
                return f"impl {type_node.text.decode('utf-8')}"

        # Go type_declaration: name is on the type_spec child
        if node.type == "type_declaration":
            for child in node.children:
                if child.type == "type_spec":
                    spec_name = child.child_by_field_name("name")
                    if spec_name:
                        return spec_name.text.decode("utf-8")

        return None

    def _split_large_definition(
        self,
        node,
        lines: list[str],
        display_path: str,
        language: str,
        parent_name: str | None,
    ) -> list[ContentChunk]:
        """Split a large definition (>200 lines) at nested definition boundaries.

        For classes/impls with many methods, splits into:
        - A "header" chunk (class signature + code before first nested def)
        - One chunk per nested definition
        - Remaining code after last nested definition

        If no nested definitions are found, returns the whole definition as one chunk.
        """
        nested = self._find_nested_definitions(node, language)

        start_row = node.start_point[0]
        end_row = node.end_point[0]

        if not nested:
            content = "\n".join(lines[start_row : end_row + 1])
            if content.strip():
                return [
                    ContentChunk(
                        content=content,
                        source_path=display_path,
                        start_line=start_row + 1,
                        end_line=end_row + 1,
                        content_type="code",
                        language=language,
                        heading=parent_name,
                    )
                ]
            return []

        chunks: list[ContentChunk] = []
        covered = start_row

        for nested_node, name in nested:
            ns = nested_node.start_point[0]
            ne = nested_node.end_point[0]

            # Gap before this nested def (class header or inter-method code)
            if ns > covered:
                gap_content = "\n".join(lines[covered:ns])
                if gap_content.strip():
                    heading = (
                        f"{parent_name} (header)"
                        if covered == start_row
                        else parent_name
                    )
                    chunks.append(
                        ContentChunk(
                            content=gap_content,
                            source_path=display_path,
                            start_line=covered + 1,
                            end_line=ns,
                            content_type="code",
                            language=language,
                            heading=heading,
                        )
                    )

            # The nested definition itself
            nest_content = "\n".join(lines[ns : ne + 1])
            if nest_content.strip():
                heading = (
                    f"{parent_name}.{name}"
                    if parent_name and name
                    else name or parent_name
                )
                chunks.append(
                    ContentChunk(
                        content=nest_content,
                        source_path=display_path,
                        start_line=ns + 1,
                        end_line=ne + 1,
                        content_type="code",
                        language=language,
                        heading=heading,
                    )
                )

            covered = ne + 1

        # Remaining code after last nested def
        if covered <= end_row:
            remaining = "\n".join(lines[covered : end_row + 1])
            if remaining.strip():
                chunks.append(
                    ContentChunk(
                        content=remaining,
                        source_path=display_path,
                        start_line=covered + 1,
                        end_line=end_row + 1,
                        content_type="code",
                        language=language,
                        heading=parent_name,
                    )
                )

        return chunks

    def _find_nested_definitions(self, node, language: str) -> list[tuple]:
        """Find nested definitions one level deep within a parent node.

        Searches the immediate children and body blocks (class_body, block, etc.)
        for definition node types.

        Returns list of (node, name) tuples.
        """
        def_types = DEFINITION_NODE_TYPES.get(language, set())
        nested = []

        for child in node.children:
            if child.type in def_types:
                name = self._get_definition_name(child, language)
                nested.append((child, name))
            elif child.type in BODY_NODE_TYPES:
                for grandchild in child.children:
                    if grandchild.type in def_types:
                        name = self._get_definition_name(grandchild, language)
                        nested.append((grandchild, name))

        return nested

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
