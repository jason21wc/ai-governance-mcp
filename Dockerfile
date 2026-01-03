# AI Governance MCP Server
# Multi-stage build for minimal image size

# =============================================================================
# Stage 1: Builder - Install dependencies and build index
# =============================================================================
FROM python:3.11-slim AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install CPU-only PyTorch first (avoids ~2GB CUDA dependencies)
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

# Copy dependency files (README needed for pyproject.toml metadata)
COPY pyproject.toml README.md ./
COPY src/ ./src/
COPY documents/ ./documents/

# Install the package
RUN pip install --no-cache-dir .

# Build the index (embeddings + global_index.json)
RUN python -m ai_governance_mcp.extractor

# =============================================================================
# Stage 2: Runtime - Minimal production image
# =============================================================================
FROM python:3.11-slim AS runtime

WORKDIR /app

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash appuser

# Install CPU-only PyTorch
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

# Copy dependency files and install (README needed for pyproject.toml metadata)
COPY pyproject.toml README.md ./
COPY src/ ./src/

RUN pip install --no-cache-dir .

# Copy pre-built index from builder
COPY --from=builder /app/index/ ./index/

# Copy documents (needed for agent templates)
COPY documents/ ./documents/

# Create logs directory
RUN mkdir -p logs && chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV AI_GOVERNANCE_DOCUMENTS_PATH=/app/documents
ENV AI_GOVERNANCE_INDEX_PATH=/app/index

# Health check - verify server can start
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "from ai_governance_mcp.server import server; print('OK')" || exit 1

# Default command - run MCP server
# Note: MCP uses stdio, so container should be run with -i flag
CMD ["python", "-m", "ai_governance_mcp.server"]

# =============================================================================
# Labels for documentation
# =============================================================================
LABEL org.opencontainers.image.title="AI Governance MCP Server"
LABEL org.opencontainers.image.description="Semantic retrieval MCP server for AI governance principles"
LABEL org.opencontainers.image.source="https://github.com/jason21wc/ai-governance-mcp"
LABEL org.opencontainers.image.licenses="MIT"
