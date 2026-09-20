"""Adapter wrapping all Cognee knowledge graph interactions.

Single isolation boundary — if Cognee's API changes, only this file changes.
Cognee is an optional dependency; all imports are lazy via importlib.
"""

from __future__ import annotations

import importlib
import logging
import os
import re
import shutil
import time
from pathlib import Path
from typing import TYPE_CHECKING

logger = logging.getLogger(__name__)

_THINK_BLOCK_RE = re.compile(
    r"<think>.*?</think>"
    r"|<\|channel>thought\n.*?<channel\|>",
    re.DOTALL,
)
_THINKING_PATCHED = "_cognee_thinking_prefilter_applied"

if TYPE_CHECKING:
    from ai_governance_mcp.context_engine.models import ContentChunk


def _get_cognee_config():
    cognee = _import_cognee()
    return cognee.config


def _import_cognee():
    return importlib.import_module("cognee")


def _get_search_type(name: str):
    try:
        module = importlib.import_module("cognee.api.v1.search")
        search_type_enum = getattr(module, "SearchType")
        return getattr(search_type_enum, name)
    except (AttributeError, ImportError) as exc:
        raise ValueError(f"Invalid search type: {name}") from exc


def _strip_thinking_blocks(response):
    try:
        for choice in response.choices:
            msg = choice.message
            original = msg.content or ""
            stripped = _THINK_BLOCK_RE.sub("", original).strip()
            if stripped:
                msg.content = stripped
            elif getattr(msg, "reasoning_content", None):
                rc = msg.reasoning_content.strip()
                if rc.startswith(("{", "[")):
                    logger.info(
                        "Recovered JSON from reasoning_content (content was empty after stripping)"
                    )
                    msg.content = rc
                else:
                    msg.content = stripped
            else:
                msg.content = stripped
            if original != msg.content:
                logger.info("Stripped thinking blocks from LLM response")
    except Exception:
        logger.warning(
            "Thinking block filter failed; returning response unmodified",
            exc_info=True,
        )
    return response


def _transform_request_kwargs(kwargs):
    try:
        model = kwargs.get("model", "")
        rf = kwargs.get("response_format")
        if (
            isinstance(rf, dict)
            and rf.get("type") == "json_object"
            and isinstance(model, str)
            and model.startswith("lm_studio/")
        ):
            kwargs = {k: v for k, v in kwargs.items() if k != "response_format"}
            logger.info(
                "Stripped json_object response_format for LM Studio compatibility"
            )
    except Exception:
        logger.warning(
            "Request kwargs transformation failed; proceeding with original kwargs",
            exc_info=True,
        )
    return kwargs


def _apply_thinking_prefilter():
    import litellm

    if getattr(litellm.acompletion, _THINKING_PATCHED, False):
        return

    original_acompletion = litellm.acompletion

    async def _filtered_acompletion(*args, **kwargs):
        kwargs = _transform_request_kwargs(kwargs)
        response = await original_acompletion(*args, **kwargs)
        return _strip_thinking_blocks(response)

    _filtered_acompletion.__name__ = original_acompletion.__name__
    _filtered_acompletion.__qualname__ = original_acompletion.__qualname__
    _filtered_acompletion.__module__ = original_acompletion.__module__
    setattr(_filtered_acompletion, _THINKING_PATCHED, True)
    litellm.acompletion = _filtered_acompletion


_CLOUD_PROVIDERS = frozenset({"anthropic", "openai", "azure", "google"})


class CogneeAdapter:
    """Wraps Cognee's async API for use within Context Engine.

    Storage isolation: each project gets its own Cognee data directory
    via cognee.config.system_root_directory(), which redirects all three
    stores (SQLite, LanceDB, Kuzu/Ladybug) to a project-specific path.
    """

    @staticmethod
    def is_available() -> bool:
        try:
            importlib.import_module("cognee")
            return True
        except ImportError:
            return False

    def __init__(self, project_index_path: Path) -> None:
        if not self.is_available():
            raise ImportError(
                "cognee is not installed. Install with: "
                "pip install -e '.[knowledge-graph]'"
            )
        self._project_index_path = project_index_path
        self._cognee_data_path = project_index_path / "cognee"

    def configure(self) -> None:
        config = _get_cognee_config()

        os.environ["ENABLE_BACKEND_ACCESS_CONTROL"] = "false"
        os.environ["COGNEE_SKIP_CONNECTION_TEST"] = "true"

        config.system_root_directory(str(self._cognee_data_path))
        config.data_root_directory(str(self._cognee_data_path / "data"))

        llm_provider = os.environ.get("AI_CONTEXT_ENGINE_COGNEE_LLM_PROVIDER", "ollama")
        llm_model = os.environ.get("AI_CONTEXT_ENGINE_COGNEE_LLM_MODEL", "")
        llm_api_key = os.environ.get("AI_CONTEXT_ENGINE_COGNEE_LLM_API_KEY", "")

        if llm_provider in _CLOUD_PROVIDERS and not llm_api_key:
            raise ValueError(
                f"API key required for cloud LLM provider '{llm_provider}'. "
                f"Set AI_CONTEXT_ENGINE_COGNEE_LLM_API_KEY."
            )

        config.set_llm_provider(llm_provider)
        if llm_model:
            config.set_llm_model(llm_model)
        if llm_api_key:
            config.set_llm_api_key(llm_api_key)

        llm_endpoint = os.environ.get("AI_CONTEXT_ENGINE_COGNEE_LLM_ENDPOINT", "")
        if llm_endpoint:
            config.set_llm_endpoint(llm_endpoint)

        llm_temperature = os.environ.get("AI_CONTEXT_ENGINE_COGNEE_LLM_TEMPERATURE", "")
        if llm_temperature:
            try:
                temp_val = float(llm_temperature)
                if not (0.0 <= temp_val <= 2.0):
                    logger.warning(
                        "AI_CONTEXT_ENGINE_COGNEE_LLM_TEMPERATURE=%s out of range "
                        "[0.0, 2.0]. Ignoring.",
                        llm_temperature,
                    )
                else:
                    config.set_llm_config({"llm_temperature": temp_val})
            except (ValueError, TypeError):
                logger.warning(
                    "Invalid AI_CONTEXT_ENGINE_COGNEE_LLM_TEMPERATURE: %s. Ignoring.",
                    llm_temperature,
                )

        embedding_provider = os.environ.get(
            "AI_CONTEXT_ENGINE_COGNEE_EMBEDDING_PROVIDER", "fastembed"
        )
        config.set_embedding_provider(embedding_provider)

        ce_embedding_model = os.environ.get("AI_CONTEXT_ENGINE_EMBEDDING_MODEL", "")
        cognee_embedding_model = os.environ.get(
            "AI_CONTEXT_ENGINE_COGNEE_EMBEDDING_MODEL", ""
        )
        embedding_model = (
            cognee_embedding_model or ce_embedding_model or "BAAI/bge-small-en-v1.5"
        )
        if (
            cognee_embedding_model
            and ce_embedding_model
            and cognee_embedding_model != ce_embedding_model
        ):
            logger.info(
                "Cognee embedding model (%s) differs from CE embedding model (%s). "
                "KG search and semantic search will use different vector spaces.",
                cognee_embedding_model,
                ce_embedding_model,
            )
        config.set_embedding_model(embedding_model)

        ce_embedding_dims = os.environ.get("AI_CONTEXT_ENGINE_EMBEDDING_DIMENSIONS", "")
        cognee_embedding_dims = os.environ.get(
            "AI_CONTEXT_ENGINE_COGNEE_EMBEDDING_DIMENSIONS", ""
        )
        dims_str = cognee_embedding_dims or ce_embedding_dims or "384"
        try:
            embedding_dimensions = int(dims_str)
            if embedding_dimensions <= 0:
                raise ValueError("must be positive")
        except (ValueError, TypeError):
            embedding_dimensions = 384
        config.set_embedding_dimensions(embedding_dimensions)

        _apply_thinking_prefilter()

    async def add_chunks(self, chunks: list[ContentChunk], dataset_name: str) -> int:
        if not chunks:
            return 0

        cognee = _import_cognee()
        texts = []
        for chunk in chunks:
            parts = []
            if chunk.heading:
                parts.append(f"# {chunk.heading}")
            parts.append(f"Source: {chunk.source_path}")
            parts.append(chunk.content)
            texts.append("\n".join(parts))

        await cognee.add(texts, dataset_name=dataset_name)
        return len(chunks)

    async def cognify(self, dataset_name: str) -> dict:
        cognee = _import_cognee()
        start = time.monotonic()
        try:
            await cognee.cognify(datasets=[dataset_name])
            duration = time.monotonic() - start
            return {
                "dataset_name": dataset_name,
                "status": "success",
                "duration_seconds": duration,
            }
        except Exception as exc:
            duration = time.monotonic() - start
            return {
                "dataset_name": dataset_name,
                "status": "error",
                "error": str(exc),
                "duration_seconds": duration,
            }

    async def search(
        self,
        query: str,
        search_type: str = "GRAPH_COMPLETION",
        top_k: int = 10,
    ) -> list[dict]:
        cognee = _import_cognee()
        enum_val = _get_search_type(search_type)
        results = await cognee.search(
            query_text=query, query_type=enum_val, top_k=top_k
        )
        if not results:
            return []

        normalized = []
        for item in results:
            if isinstance(item, dict):
                normalized.append(
                    {
                        "content": item.get("text", item.get("content", str(item))),
                        "score": item.get("score", 0.0),
                        "source": item.get("source", ""),
                    }
                )
            else:
                normalized.append(
                    {
                        "content": str(item),
                        "score": 0.0,
                        "source": "",
                    }
                )
        return normalized

    async def cleanup(self) -> None:
        shutil.rmtree(self._cognee_data_path, ignore_errors=True)

    def has_knowledge_graph(self) -> bool:
        if not self._cognee_data_path.exists():
            return False
        return any(self._cognee_data_path.iterdir())
