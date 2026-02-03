"""Data models for the Context Engine.

Defines content chunks, file metadata, project indexes,
and query results used throughout the context engine.
"""

from typing import Literal, Optional

from pydantic import BaseModel, Field

# Valid content types for chunks and file metadata
ContentType = Literal["code", "document", "data", "image"]

# Valid indexing modes for projects
IndexMode = Literal["realtime", "ondemand"]


class ContentChunk(BaseModel):
    """A chunk of content extracted from a project file.

    Chunks are the atomic unit of indexing and retrieval.
    Each chunk should be self-contained enough for standalone
    comprehension while focused enough for precise retrieval.
    """

    content: str = Field(..., description="The text content of this chunk")
    source_path: str = Field(..., description="Absolute path to the source file")
    start_line: int = Field(..., description="Starting line number in source file")
    end_line: int = Field(..., description="Ending line number in source file")
    content_type: ContentType = Field(
        ..., description="Content type: code, document, data, image"
    )
    language: Optional[str] = Field(
        None, description="Programming language or file format"
    )
    heading: Optional[str] = Field(
        None, description="Section heading or function/class name"
    )
    embedding_id: Optional[int] = Field(None, description="Index into embeddings array")


class FileMetadata(BaseModel):
    """Metadata about an indexed file."""

    path: str = Field(..., description="Absolute file path")
    content_type: ContentType = Field(
        ..., description="Content type: code, document, data, image"
    )
    language: Optional[str] = Field(
        None, description="Programming language or file format"
    )
    size_bytes: int = Field(..., description="File size in bytes")
    last_modified: float = Field(..., description="Last modification timestamp")
    content_hash: Optional[str] = Field(
        None, description="SHA-256 hash of file content for change detection"
    )
    chunk_count: int = Field(0, description="Number of chunks extracted")


class ProjectIndex(BaseModel):
    """Complete index for a single project."""

    project_id: str = Field(..., description="Unique project identifier")
    project_path: str = Field(..., description="Absolute path to project root")
    chunks: list[ContentChunk] = Field(
        default_factory=list, description="All indexed content chunks"
    )
    files: list[FileMetadata] = Field(
        default_factory=list, description="Metadata for all indexed files"
    )
    created_at: str = Field(..., description="ISO timestamp of index creation")
    updated_at: str = Field(..., description="ISO timestamp of last update")
    embedding_model: str = Field(..., description="Model used for embeddings")
    total_chunks: int = Field(0, description="Total number of chunks indexed")
    total_files: int = Field(0, description="Total number of files indexed")
    index_mode: IndexMode = Field(
        "realtime", description="Indexing mode: realtime or ondemand"
    )


class QueryResult(BaseModel):
    """A single result from a project content query."""

    chunk: ContentChunk = Field(..., description="The matching content chunk")
    semantic_score: float = Field(
        0.0, ge=0.0, le=1.0, description="Semantic similarity score"
    )
    keyword_score: float = Field(
        0.0, ge=0.0, le=1.0, description="BM25 keyword score (normalized)"
    )
    combined_score: float = Field(
        0.0, ge=0.0, le=1.0, description="Fused relevance score"
    )


class ProjectQueryResult(BaseModel):
    """Complete result from querying a project's content."""

    query: str = Field(..., description="The original query")
    project_id: str = Field(..., description="Project that was queried")
    project_path: str = Field(..., description="Path to project root")
    results: list[QueryResult] = Field(
        default_factory=list, description="Ranked results"
    )
    total_results: int = Field(0, description="Number of results returned")
    query_time_ms: Optional[float] = Field(
        None, description="Query execution time in milliseconds"
    )


class ProjectStatus(BaseModel):
    """Status information about a project's index."""

    project_id: str = Field(..., description="Unique project identifier")
    project_path: str = Field(..., description="Absolute path to project root")
    total_files: int = Field(0, description="Number of indexed files")
    total_chunks: int = Field(0, description="Number of indexed chunks")
    index_mode: IndexMode = Field("realtime", description="Current indexing mode")
    last_updated: Optional[str] = Field(
        None, description="ISO timestamp of last index update"
    )
    index_size_bytes: int = Field(0, description="Total index size on disk")
    embedding_model: str = Field(..., description="Model used for embeddings")
