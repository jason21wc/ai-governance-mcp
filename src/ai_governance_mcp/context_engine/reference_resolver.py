"""Code reference resolver for the Context Engine.

Walks tree-sitter ASTs to resolve cross-file references (imports,
calls, inheritance) and produces typed CodeEdge instances.

Symbol Matching Rules (from design spike — Task 4.5):
  Heading shapes from _get_definition_name():
    - Clean names (47%): "CodeConnector", "parse", "_validate_project_id"
      → Direct match against import names. This is the primary case.
    - Composite "Class.method" (35%): "CodeConnector.__init__", "BaseStorage.save_embeddings"
      → Match the class part against import names; method-level edges use the composite.
    - "preamble" (14%): Module-level code outside definitions.
      → Cannot participate as a target (no importable name). Can be a source for imports.
    - None (4%): Unparseable definitions.
      → Skipped entirely (both as source and target).
    - "export" (0% in Python, present in JS/TS): Default exports.
      → Matched via default import resolution.
    - "ClassName (header)" (<1%): Class headers from large-class splitting.
      → Matched by extracting class name before " (header)".
"""

import logging
import re
from pathlib import Path

from .models import CodeEdge

logger = logging.getLogger("ai_governance_mcp.context_engine.reference_resolver")

MAX_BARREL_DEPTH = 5

# JS/TS extensions to probe when resolving bare import paths
_JS_TS_EXTENSIONS = [".ts", ".tsx", ".js", ".jsx"]


class ReferenceResolver:
    """Resolves cross-file code references into typed edges.

    Takes existing ContentChunks (from indexing) and produces CodeEdge
    instances by re-parsing files with tree-sitter and walking the AST
    for import statements, function calls, and class inheritance.
    """

    def __init__(self, project_path: str | Path):
        self.project_path = Path(project_path).resolve()

    def resolve_all(self, chunks: list) -> list[CodeEdge]:
        """Resolve all cross-file references for the given chunks.

        Args:
            chunks: ContentChunk instances from indexing.

        Returns:
            List of CodeEdge instances representing discovered references.
        """
        symbol_index = self._build_symbol_index(chunks)
        edges: list[CodeEdge] = []

        source_files = self._group_chunks_by_file(chunks)

        for rel_path, file_chunks in source_files.items():
            abs_path = self.project_path / rel_path
            if not abs_path.exists():
                continue

            language = self._detect_language(rel_path)
            if not language:
                continue

            try:
                tree = self._parse_file(abs_path, language)
            except Exception:
                logger.debug("Failed to parse %s for reference resolution", rel_path)
                continue

            if not tree:
                continue

            if language == "python":
                import_map = self._resolve_python_imports(
                    rel_path, tree.root_node, symbol_index
                )
            elif language in ("javascript", "typescript"):
                import_map = self._resolve_js_ts_imports(
                    rel_path, tree.root_node, symbol_index
                )
            else:
                continue

            source_symbols = self._find_source_symbols(rel_path, file_chunks)
            for local_name, (target_path, target_symbol) in import_map.items():
                for src_sym in source_symbols:
                    edges.append(
                        CodeEdge(
                            source_path=rel_path,
                            source_symbol=src_sym,
                            target_path=target_path,
                            target_symbol=target_symbol,
                            edge_type="imports",
                        )
                    )

            call_edges = self._extract_call_edges(
                rel_path, tree.root_node, import_map, file_chunks, language
            )
            edges.extend(call_edges)

            inheritance_edges = self._extract_inheritance_edges(
                rel_path, tree.root_node, import_map, language
            )
            edges.extend(inheritance_edges)

        return self._deduplicate(edges)

    def _build_symbol_index(self, chunks: list) -> dict[str, list[str]]:
        """Build {relative_path: [symbol_names]} from chunk headings.

        Normalizes composite headings (Class.method → Class, method).
        Skips None, preamble, and header-only headings.
        """
        index: dict[str, list[str]] = {}
        for chunk in chunks:
            if chunk.content_type != "code":
                continue
            path = chunk.source_path
            if path not in index:
                index[path] = []
            heading = chunk.heading
            if not heading or heading == "preamble":
                continue
            name = self._normalize_heading(heading)
            if name and name not in index[path]:
                index[path].append(name)
        return index

    def _normalize_heading(self, heading: str) -> str | None:
        """Normalize a chunk heading to a matchable symbol name.

        "CodeConnector" → "CodeConnector"
        "CodeConnector.__init__" → "CodeConnector"
        "CodeConnector (header)" → "CodeConnector"
        "impl SomeType" → "SomeType"
        "export" → None (not matchable)
        "preamble" → None
        """
        if not heading or heading in ("preamble", "export"):
            return None
        if " (header)" in heading:
            heading = heading.split(" (header)")[0]
        if heading.startswith("impl "):
            heading = heading[5:]
        if "." in heading:
            heading = heading.split(".")[0]
        return heading

    def _group_chunks_by_file(self, chunks: list) -> dict[str, list]:
        """Group chunks by their source_path."""
        groups: dict[str, list] = {}
        for chunk in chunks:
            if chunk.content_type != "code":
                continue
            path = chunk.source_path
            if path not in groups:
                groups[path] = []
            groups[path].append(chunk)
        return groups

    def _find_source_symbols(self, rel_path: str, chunks: list) -> list[str]:
        """Get importable symbol names from the file's chunks.

        Returns the file-level module name for import edges
        (imports are file-to-file, not symbol-to-symbol).
        """
        module = Path(rel_path).stem
        if module == "__init__":
            module = Path(rel_path).parent.name
        return [module]

    def _detect_language(self, rel_path: str) -> str | None:
        """Detect language from file extension."""
        ext = Path(rel_path).suffix.lower()
        lang_map = {
            ".py": "python",
            ".js": "javascript",
            ".jsx": "javascript",
            ".ts": "typescript",
            ".tsx": "typescript",
        }
        return lang_map.get(ext)

    def _parse_file(self, abs_path: Path, language: str):
        """Parse a file with tree-sitter. Returns tree or None."""
        try:
            from tree_sitter_language_pack import get_parser
        except ImportError:
            return None

        try:
            parser = get_parser(language)
        except Exception:
            return None

        try:
            content = abs_path.read_bytes()
            return parser.parse(content)
        except Exception:
            return None

    # ─── Python import resolution ───

    def _resolve_python_imports(
        self,
        source_path: str,
        root_node,
        symbol_index: dict[str, list[str]],
    ) -> dict[str, tuple[str, str]]:
        """Resolve Python imports to project-internal targets.

        Returns {local_name: (target_path, target_symbol)} for resolved imports.
        Stdlib/third-party imports (no matching project file) are skipped.
        """
        import_map: dict[str, tuple[str, str]] = {}

        for child in root_node.children:
            if child.type == "import_from_statement":
                self._resolve_python_from_import(
                    child, source_path, symbol_index, import_map
                )
            elif child.type == "import_statement":
                self._resolve_python_import(
                    child, source_path, symbol_index, import_map
                )

        return import_map

    def _resolve_python_from_import(
        self,
        node,
        source_path: str,
        symbol_index: dict[str, list[str]],
        import_map: dict[str, tuple[str, str]],
    ) -> None:
        """Resolve 'from X import Y' style imports."""
        module_path = self._extract_python_module_path(node)
        if module_path is None:
            return

        is_relative = any(
            c.type == "relative_import" or c.text == b"." for c in node.children
        )

        # Count leading dots for relative imports
        dot_count = 0
        if is_relative:
            for c in node.children:
                if c.type == "relative_import":
                    dot_count = c.text.decode("utf-8").count(".")
                    break
                if c.text == b".":
                    dot_count += 1

        target_file = self._resolve_python_module_to_file(
            module_path, source_path, is_relative, dot_count, symbol_index
        )
        if not target_file:
            return

        # Check for wildcard import
        has_wildcard = any(c.type == "wildcard_import" for c in node.children)
        if has_wildcard:
            symbols = symbol_index.get(target_file, [])
            for sym in symbols:
                import_map[sym] = (target_file, sym)
            return

        # Extract imported names
        for c in node.children:
            if c.type == "dotted_name":
                module_node = node.child_by_field_name("module_name")
                if c is module_node:
                    continue
                name = c.text.decode("utf-8")
                import_map[name] = (target_file, name)
            elif c.type == "aliased_import":
                alias = c.child_by_field_name("alias")
                orig = c.child_by_field_name("name")
                local = (
                    (alias or orig).text.decode("utf-8") if (alias or orig) else None
                )
                orig_name = orig.text.decode("utf-8") if orig else None
                if local and orig_name:
                    import_map[local] = (target_file, orig_name)

    def _resolve_python_import(
        self,
        node,
        source_path: str,
        symbol_index: dict[str, list[str]],
        import_map: dict[str, tuple[str, str]],
    ) -> None:
        """Resolve 'import X' style imports."""
        for c in node.children:
            if c.type == "dotted_name":
                module = c.text.decode("utf-8")
                target = self._resolve_python_module_to_file(
                    module, source_path, False, 0, symbol_index
                )
                if target:
                    local_name = module.split(".")[0]
                    import_map[local_name] = (target, Path(target).stem)
            elif c.type == "aliased_import":
                orig = c.child_by_field_name("name")
                alias = c.child_by_field_name("alias")
                if orig:
                    module = orig.text.decode("utf-8")
                    target = self._resolve_python_module_to_file(
                        module, source_path, False, 0, symbol_index
                    )
                    if target:
                        local = (
                            alias.text.decode("utf-8")
                            if alias
                            else module.split(".")[0]
                        )
                        import_map[local] = (target, Path(target).stem)

    def _extract_python_module_path(self, node) -> str | None:
        """Extract the module path from a Python import node."""
        module_node = node.child_by_field_name("module_name")
        if module_node:
            return module_node.text.decode("utf-8")
        for c in node.children:
            if c.type == "relative_import":
                dotted = c.child_by_field_name("module_name")
                if dotted:
                    return dotted.text.decode("utf-8")
                for sub in c.children:
                    if sub.type == "dotted_name":
                        return sub.text.decode("utf-8")
                return ""
            if c.type == "dotted_name":
                return c.text.decode("utf-8")
        return None

    def _resolve_python_module_to_file(
        self,
        module_path: str,
        source_path: str,
        is_relative: bool,
        dot_count: int,
        symbol_index: dict[str, list[str]],
    ) -> str | None:
        """Resolve a Python module path to a project-relative file path.

        Returns the matching file path from symbol_index, or None.
        """
        if is_relative:
            source_dir = Path(source_path).parent
            for _ in range(dot_count - 1):
                source_dir = source_dir.parent

            if module_path:
                parts = module_path.split(".")
                candidate_dir = source_dir / "/".join(parts)
                candidate_file = (
                    source_dir / "/".join(parts[:-1]) / f"{parts[-1]}.py"
                    if len(parts) > 0
                    else None
                )

                candidates = []
                if candidate_file:
                    candidates.append(str(candidate_file))
                candidates.append(str(candidate_dir / "__init__.py"))
                candidates.append(
                    str(source_dir / f"{module_path.replace('.', '/')}.py")
                )

                for c in candidates:
                    normalized = str(Path(c))
                    if normalized in symbol_index:
                        return normalized
            else:
                init = str(source_dir / "__init__.py")
                if init in symbol_index:
                    return init
        else:
            parts = module_path.split(".")
            candidates = [
                "/".join(parts) + ".py",
                "/".join(parts) + "/__init__.py",
            ]
            if len(parts) > 1:
                candidates.append("/".join(parts[:-1]) + ".py")

            for c in candidates:
                normalized = str(Path(c))
                if normalized in symbol_index:
                    return normalized

            for known_path in symbol_index:
                if known_path.endswith(f"/{parts[-1]}.py") or known_path.endswith(
                    f"/{'/'.join(parts)}.py"
                ):
                    return known_path
                if known_path.endswith(f"/{'/'.join(parts)}/__init__.py"):
                    return known_path

        return None

    # ─── JS/TS import resolution ───

    def _resolve_js_ts_imports(
        self,
        source_path: str,
        root_node,
        symbol_index: dict[str, list[str]],
    ) -> dict[str, tuple[str, str]]:
        """Resolve JS/TS imports to project-internal targets."""
        import_map: dict[str, tuple[str, str]] = {}

        for child in root_node.children:
            if child.type == "import_statement":
                self._resolve_js_import_node(
                    child, source_path, symbol_index, import_map
                )

        return import_map

    def _resolve_js_import_node(
        self,
        node,
        source_path: str,
        symbol_index: dict[str, list[str]],
        import_map: dict[str, tuple[str, str]],
    ) -> None:
        """Resolve a single JS/TS import statement."""
        source_node = node.child_by_field_name("source")
        if not source_node:
            for c in node.children:
                if c.type == "string":
                    source_node = c
                    break
        if not source_node:
            return

        raw = source_node.text.decode("utf-8").strip("'\"")

        if not raw.startswith("."):
            return

        target_file = self._resolve_js_path(raw, source_path, symbol_index)
        if not target_file:
            return

        target_file = self._follow_barrel_exports(target_file, symbol_index, set(), 0)

        for c in node.children:
            if c.type == "import_clause":
                self._extract_js_import_names(c, target_file, symbol_index, import_map)
            elif c.type == "named_imports":
                self._extract_named_imports(c, target_file, symbol_index, import_map)
            elif c.type == "identifier":
                name = c.text.decode("utf-8")
                if name != "from":
                    import_map[name] = (target_file, name)

    def _resolve_js_path(
        self,
        raw_path: str,
        source_path: str,
        symbol_index: dict[str, list[str]],
    ) -> str | None:
        """Resolve a JS/TS relative import path with extension probing."""
        source_dir = Path(source_path).parent
        base = source_dir / raw_path

        for ext in _JS_TS_EXTENSIONS:
            candidate = str(Path(str(base) + ext))
            if candidate in symbol_index:
                return candidate

        for ext in _JS_TS_EXTENSIONS:
            candidate = str(base / f"index{ext}")
            if candidate in symbol_index:
                return candidate

        candidate = str(base)
        if candidate in symbol_index:
            return candidate

        return None

    def _follow_barrel_exports(
        self,
        file_path: str,
        symbol_index: dict[str, list[str]],
        visited: set[str],
        depth: int,
    ) -> str:
        """Follow barrel export chains (index files that re-export).

        Returns the final resolved file, or the original if not a barrel.
        """
        if depth >= MAX_BARREL_DEPTH or file_path in visited:
            return file_path

        if not file_path.endswith(("index.ts", "index.tsx", "index.js", "index.jsx")):
            return file_path

        abs_path = self.project_path / file_path
        if not abs_path.exists():
            return file_path

        try:
            content = abs_path.read_text(errors="replace")
        except OSError:
            return file_path

        export_from = re.findall(
            r"""export\s+\{[^}]*\}\s+from\s+['"]([^'"]+)['"]""", content
        )
        export_star = re.findall(r"""export\s+\*\s+from\s+['"]([^'"]+)['"]""", content)

        all_reexports = export_from + export_star
        if len(all_reexports) == 1:
            visited.add(file_path)
            resolved = self._resolve_js_path(all_reexports[0], file_path, symbol_index)
            if resolved:
                return self._follow_barrel_exports(
                    resolved, symbol_index, visited, depth + 1
                )

        return file_path

    def _extract_js_import_names(
        self, clause_node, target_file, symbol_index, import_map
    ) -> None:
        """Extract names from an import_clause node."""
        for c in clause_node.children:
            if c.type == "identifier":
                name = c.text.decode("utf-8")
                import_map[name] = (target_file, name)
            elif c.type == "named_imports":
                self._extract_named_imports(c, target_file, symbol_index, import_map)

    def _extract_named_imports(
        self, node, target_file, symbol_index, import_map
    ) -> None:
        """Extract names from a named_imports node: { foo, bar as baz }."""
        for c in node.children:
            if c.type == "import_specifier":
                alias = c.child_by_field_name("alias")
                name = c.child_by_field_name("name")
                if alias and name:
                    import_map[alias.text.decode("utf-8")] = (
                        target_file,
                        name.text.decode("utf-8"),
                    )
                elif name:
                    n = name.text.decode("utf-8")
                    import_map[n] = (target_file, n)

    # ─── Call edge extraction ───

    def _extract_call_edges(
        self,
        source_path: str,
        root_node,
        import_map: dict[str, tuple[str, str]],
        file_chunks: list,
        language: str,
    ) -> list[CodeEdge]:
        """Extract function/method call edges from AST."""
        edges: list[CodeEdge] = []
        call_type = "call" if language == "python" else "call_expression"

        calls = self._find_nodes_of_type(root_node, call_type)

        for call_node in calls:
            called_name = self._extract_called_name(call_node, language)
            if not called_name:
                continue

            base_name = called_name.split(".")[0]
            if base_name not in import_map:
                continue

            target_path, target_symbol = import_map[base_name]
            source_symbol = self._find_enclosing_symbol(
                call_node, root_node, file_chunks, language
            )
            if not source_symbol:
                continue

            edges.append(
                CodeEdge(
                    source_path=source_path,
                    source_symbol=source_symbol,
                    target_path=target_path,
                    target_symbol=called_name if "." in called_name else target_symbol,
                    edge_type="calls",
                    confidence=0.8,
                )
            )

        return edges

    def _extract_called_name(self, call_node, language: str) -> str | None:
        """Extract the name being called from a call expression."""
        func_node = call_node.child_by_field_name("function")

        if not func_node:
            if call_node.children:
                func_node = call_node.children[0]

        if not func_node:
            return None

        if func_node.type == "identifier":
            return func_node.text.decode("utf-8")
        elif func_node.type == "attribute" or func_node.type == "member_expression":
            return func_node.text.decode("utf-8")

        return None

    def _find_enclosing_symbol(
        self, node, root_node, file_chunks: list, language: str
    ) -> str | None:
        """Find the chunk heading that encloses a given AST node."""
        line = node.start_point[0] + 1
        for chunk in file_chunks:
            if chunk.start_line <= line <= chunk.end_line:
                heading = chunk.heading
                if heading and heading != "preamble":
                    return self._normalize_heading(heading) or heading
                return None
        return None

    def _find_nodes_of_type(self, node, node_type: str) -> list:
        """Recursively find all nodes of a given type in the AST."""
        results = []
        if node.type == node_type:
            results.append(node)
        for child in node.children:
            results.extend(self._find_nodes_of_type(child, node_type))
        return results

    # ─── Inheritance edge extraction ───

    def _extract_inheritance_edges(
        self,
        source_path: str,
        root_node,
        import_map: dict[str, tuple[str, str]],
        language: str,
    ) -> list[CodeEdge]:
        """Extract class inheritance (extends/implements) edges."""
        edges: list[CodeEdge] = []

        if language == "python":
            edges.extend(
                self._extract_python_inheritance(source_path, root_node, import_map)
            )
        elif language in ("javascript", "typescript"):
            edges.extend(
                self._extract_js_ts_inheritance(
                    source_path, root_node, import_map, language
                )
            )

        return edges

    def _extract_python_inheritance(
        self, source_path: str, root_node, import_map: dict
    ) -> list[CodeEdge]:
        """Extract Python class inheritance edges."""
        edges: list[CodeEdge] = []

        for node in self._find_nodes_of_type(root_node, "class_definition"):
            class_name_node = node.child_by_field_name("name")
            if not class_name_node:
                continue
            class_name = class_name_node.text.decode("utf-8")

            superclasses = node.child_by_field_name("superclasses")
            if not superclasses:
                arg_list = None
                for c in node.children:
                    if c.type == "argument_list":
                        arg_list = c
                        break
                superclasses = arg_list

            if not superclasses:
                continue

            for c in superclasses.children:
                if c.type in ("identifier", "dotted_name", "attribute"):
                    parent_name = c.text.decode("utf-8")
                    base_name = parent_name.split(".")[0]
                    if base_name in import_map:
                        target_path, target_symbol = import_map[base_name]
                        edges.append(
                            CodeEdge(
                                source_path=source_path,
                                source_symbol=class_name,
                                target_path=target_path,
                                target_symbol=parent_name
                                if "." in parent_name
                                else target_symbol,
                                edge_type="extends",
                            )
                        )

        return edges

    def _extract_js_ts_inheritance(
        self, source_path: str, root_node, import_map: dict, language: str
    ) -> list[CodeEdge]:
        """Extract JS/TS class extends/implements edges."""
        edges: list[CodeEdge] = []

        for node in self._find_nodes_of_type(root_node, "class_declaration"):
            class_name_node = node.child_by_field_name("name")
            if not class_name_node:
                continue
            class_name = class_name_node.text.decode("utf-8")

            for c in node.children:
                if c.type == "class_heritage":
                    for heritage in c.children:
                        if heritage.type in ("extends_clause", "extends_type_clause"):
                            for ident in heritage.children:
                                if ident.type in ("identifier", "type_identifier"):
                                    parent = ident.text.decode("utf-8")
                                    if parent in import_map:
                                        tp, ts = import_map[parent]
                                        edges.append(
                                            CodeEdge(
                                                source_path=source_path,
                                                source_symbol=class_name,
                                                target_path=tp,
                                                target_symbol=ts,
                                                edge_type="extends",
                                            )
                                        )
                        elif heritage.type == "implements_clause":
                            for ident in heritage.children:
                                if ident.type in ("identifier", "type_identifier"):
                                    iface = ident.text.decode("utf-8")
                                    if iface in import_map:
                                        tp, ts = import_map[iface]
                                        edges.append(
                                            CodeEdge(
                                                source_path=source_path,
                                                source_symbol=class_name,
                                                target_path=tp,
                                                target_symbol=ts,
                                                edge_type="implements",
                                            )
                                        )

        return edges

    # ─── Helpers ───

    def _deduplicate(self, edges: list[CodeEdge]) -> list[CodeEdge]:
        """Remove duplicate edges (same source+target+type)."""
        seen: set[tuple] = set()
        unique: list[CodeEdge] = []
        for edge in edges:
            key = (
                edge.source_path,
                edge.source_symbol,
                edge.target_path,
                edge.target_symbol,
                edge.edge_type,
            )
            if key not in seen:
                seen.add(key)
                unique.append(edge)
        return unique
