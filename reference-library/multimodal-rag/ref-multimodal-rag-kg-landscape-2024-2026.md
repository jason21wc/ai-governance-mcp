---
id: ref-multimodal-rag-kg-landscape-2024-2026
title: "Knowledge Graph RAG Landscape 2024-2026: Community Detection, Multi-Hop Retrieval, and Tool Evaluation"
domain: multimodal-rag
tags: ["knowledge-graph", "graphrag", "community-detection", "hipporag", "cognee", "multi-hop-retrieval", "personalized-pagerank"]
status: current
entry_type: reference
summary: "Comprehensive landscape analysis of knowledge graph RAG systems (2024-2026) covering Microsoft GraphRAG community detection, HippoRAG Personalized PageRank, LEGO-GraphRAG multi-hop decomposition, tool evaluation (Cognee recommended), cost/scale decision framework, graph quality metrics, and educational domain schema patterns."
created: 2026-05-15
last_verified: 2026-05-15
maturity: seedling
decay_class: research
source: "Session-177 research agents — two parallel investigations covering best practices and tool evaluation"
external_url: "https://arxiv.org/abs/2404.16130"
external_author: "Microsoft Research (primary); multiple authors across referenced works"
accessed_date: 2026-05-15
related:
  - ref-multimodal-rag-kg-landscape-2024-2026 # self
---

## Context

This entry captures research findings from a systematic evaluation of knowledge graph RAG systems (2024-2026), conducted to identify gaps in the A5 Knowledge Graph Integration principle and §3.8 methods. Two research agents investigated: (1) best practices from academic and industry sources, and (2) tool evaluation across 10+ candidates for a concrete use case (ingesting hundreds of raw statistics education documents with multi-hop retrieval).

**When to consult this entry:** When designing or evaluating a knowledge graph-based RAG system; when implementing A5/§3.8 procedures; when selecting tooling for graph+vector hybrid retrieval; when the Cognee integration spike (BACKLOG #47) is activated.

---

## Community Detection & Hierarchical Summarization

### Microsoft GraphRAG (arXiv 2404.16130, 2024)

The core innovation that separates modern graph RAG from basic entity-relationship traversal:

1. **Entity extraction** — LLM builds a knowledge graph from source documents (entities + relationships)
2. **Community detection** — Leiden algorithm performs hierarchical multi-level clustering on the graph, producing a tree of communities (Level 0 = finest-grained, Level 1+ = progressively aggregated)
3. **Community summary generation** — For every community at every level, an LLM generates a summary synthesizing entity and relationship information. Higher-level summaries recursively incorporate lower-level summaries
4. **Two query modes:**
   - **Local** — entity-focused retrieval (find content about specific entities)
   - **Global** — corpus-level synthesis (community summaries generate partial responses, combined into final answer)

### GraphRAG Variants

| Variant | Key Innovation | Cost vs Full GraphRAG | Best For |
|---------|---------------|----------------------|----------|
| **Full GraphRAG** | Pre-computed community summaries at all levels | Baseline (3-5x baseline RAG) | Stable corpora, frequent global queries |
| **LazyGraphRAG** (Microsoft, 2025) | Defers graph construction to query time; combines best-first + breadth-first search in iterative deepening | ~0.1% indexing cost; ~700x cheaper queries at comparable quality | Dynamic corpora, budget-constrained, exploratory queries |
| **LightRAG** (2024) | Single-pass entity/relation extraction; incremental graph updates via graph union (~50% reduced update time) | ~30% query latency reduction | Incremental update scenarios |
| **FastGraphRAG** | PageRank at retrieval time instead of community summaries | Similar to LightRAG | When PageRank-based ranking suffices |
| **ArchRAG** (AAAI 2026) | Augments communities with node attributes; C-HNSW index for efficient retrieval | Outperforms others in accuracy AND token cost | When node attributes carry important signal |

### Decision Criteria: Which Variant?

- **Corpus stability:** High stability (rarely changes) → Full GraphRAG. Frequent changes → LazyGraphRAG or LightRAG.
- **Query pattern:** Mostly global ("what are the themes?") → Full GraphRAG with community summaries. Mostly local ("what about entity X?") → LightRAG or basic graph traversal.
- **Budget:** Tight → LazyGraphRAG (0.1% of full GraphRAG indexing cost). Flexible → Full GraphRAG for best quality.
- **Scale:** <1K documents → any variant works. >10K documents → evaluate partitioned or lazy approaches.

---

## Advanced Retrieval Strategies

### Personalized PageRank (HippoRAG, NeurIPS 2024 / ICLR 2025)

Hippocampus-inspired retrieval that replaces static weighted merge with graph-adaptive ranking:

- **Mechanism:** Spread activation across the graph from query-relevant seed nodes using Personalized PageRank
- **Benefits:** Cluster promotion (semantically coherent groups reinforce each other) + noise suppression (isolated hits drop in ranking)
- **Key insight:** This is fundamentally different from a static weighted merge (e.g., `graph * 0.4 + vector * 0.6`). PageRank adapts to the graph topology around the query, producing different rankings for different query types even on the same graph.

### Multi-Stage Reranking Pipeline

The current best practice for production graph-augmented retrieval:

1. **Stage 1 — Broad retrieval** (optimize for recall): parallel vector search + graph entity matching + community summary matching. Cast a wide net (top-20 to top-50).
2. **Stage 2 — Precision reranking** (optimize for relevance): cross-encoder models, graph-structural signals (degree centrality, community membership, PageRank score), and semantic relevance. Narrow to top-5 to top-10.
3. **Stage 3 — Context assembly**: select final results respecting context window budget, include community summaries for global context, assemble with source attribution.

**Key research finding:** Graph operators (how you traverse and rank) matter more than graph structure (how you store). Methods combining topological traversal with statistical ranking (Personalized PageRank) consistently outperform others (arXiv 2506.05690v3).

---

## Multi-Hop Query Decomposition

### LEGO-GraphRAG Pipeline (VLDB 2025)

Modular framework decomposing multi-hop retrieval into separable stages:

1. **Subgraph extraction** — Identify the relevant portion of the knowledge graph for the query. This is the main efficiency bottleneck for large graphs.
2. **Path filtering** — From the extracted subgraph, identify candidate reasoning paths (chains of relationships connecting query entities to answer entities).
3. **Path refinement** — Evaluate candidate paths for relevance and correctness. Semantic-augmented methods are essential for complex (2+ hop) queries; structure-based methods are faster but less accurate.

### StepChain GraphRAG

Unites question decomposition with BFS-based reasoning flow:
- At inference, passages are parsed on-the-fly into a knowledge graph
- BFS traversal dynamically expands along relevant edges for each sub-question
- Each hop produces an intermediate answer that informs the next hop

### Cross-Reference

AG2 (Query Decomposition) in multimodal-rag principles handles modality routing for decomposed queries. The procedures here are complementary — AG2 decomposes by modality, these procedures decompose by graph structure. For chain integrity verification after multi-hop retrieval, see §5.5 (Multi-Hop Cross-Modal Reasoning Verification).

---

## Cost/Scale Decision Framework

| Corpus Size | Query Pattern | Recommended Approach | Rationale |
|-------------|--------------|---------------------|-----------|
| <1K docs, simple queries | Keyword/semantic lookup | No KG — vector search sufficient | KG overhead (3-5x) not justified |
| <1K docs, relationship queries | Structural traversal | Lightweight KG (NetworkX, Kuzu) | Graph adds value; scale is small |
| 1K-10K docs, stable corpus | Global + local queries | Full GraphRAG (community detection + pre-computed summaries) | Investment amortized over many queries |
| 1K-10K docs, high change rate | Mixed queries | LazyGraphRAG or LightRAG (incremental) | Pre-computation invalidated too frequently |
| 10K-100K docs | Any | Partitioned KG or domain-specific subgraphs | Single monolithic graph becomes unwieldy |
| >100K docs | Any | Evaluate streaming incremental + periodic full refresh | Full rebuilds become prohibitively expensive |

**Cost multiplier:** KG extraction adds 3-5x cost over baseline vector RAG. The cost is primarily LLM calls for entity/relationship extraction and community summarization, not graph storage. Triplex model (R2R/SciPhi) reduces extraction cost by ~98% using a fine-tuned model instead of general LLM calls — worth evaluating for cost-sensitive deployments.

**Scale-based maintenance guidelines:**
- <1M graph edges: full refresh (rebuild cost negligible)
- 1M-10M edges: hybrid (full rebuild periodic + incremental between rebuilds)
- 10M-100M edges: incremental with weekly/monthly full refresh
- >100M edges: streaming incremental mandatory
- **30-50% change rate threshold:** When exceeded, full rebuild is cheaper than incremental maintenance

---

## Graph Quality Metrics

The HAL 2025 survey identifies 23 quality dimensions for knowledge graphs. For operational use, prioritize these 5:

| Metric | What It Measures | How to Assess |
|--------|-----------------|---------------|
| **Entity accuracy** | Are extracted entities real? | Precision/recall on sampled entity set vs human annotation |
| **Relationship accuracy** | Do stated relationships hold? | Sample edges, verify against source documents |
| **Completeness** | Are expected entities present? | Compare entity count against expected domain coverage |
| **Consistency** | No contradictory edges? | Check for conflicting relationships (A→B and A→¬B) |
| **Freshness** | Time since last verification | Track age of oldest unverified node; alert when stale |

**LP-Measure:** Assesses KG quality through link prediction tasks without requiring gold standards — useful when human annotation is impractical.

**Dual-perspective evaluation:** Structural adequacy (does the graph topology support the queries?) + semantic alignment (do entity/relationship labels match the domain vocabulary?).

---

## Educational Domain Schema Patterns

### Math Academy Knowledge Graph (Skycak)

The most directly relevant pattern for statistics/STEM education domains:

- **~2,500 topics** with 3-4 knowledge points each
- Each knowledge point has one or more **prerequisites** with **encompassing weights** (fraction of the prerequisite exercised: 0.0-1.0)
- Uses **Fractional Implicit Repetition (FIRe)** for spaced review driven by the graph structure

**Recommended schema for statistics education:**

| Node Type | Examples | Attributes |
|-----------|---------|------------|
| Concept | Standard deviation, Regression, Hypothesis testing | level (intro/intermediate/advanced), domain area |
| Knowledge Point | "Compute standard deviation from raw data" | associated concept, difficulty |
| Resource | Textbook chapter, presentation, problem set | format, source, date |

| Edge Type | Meaning | Attributes |
|-----------|---------|------------|
| `prerequisite_of` | Topic A must be understood before Topic B | encompassing weight (0.0-1.0) |
| `co_requisite` | Topics that benefit from parallel study | strength |
| `extends` | Topic B builds directly on Topic A's foundations | derivation type |
| `illustrated_by` | Links concepts to concrete resources | resource type |
| `derived_from` | Mathematical derivation chain | proof/formula dependency |

**Key structural property:** Prerequisite graphs naturally form directed acyclic graphs (DAGs). The topological ordering of this DAG defines valid learning sequences. This enables: prerequisite chain validation (is a learning path well-ordered?), gap detection (what prerequisites is the learner missing?), and adaptive sequencing (what should come next?).

**Other educational KG references:**
- EDUKG (IEEE 2018): Fine-grained K-12 ontology, 635 classes, 1,314 properties
- CurrKG (2025): Ontology for curriculum and learning material representation
- ACE: AI-assisted construction of educational KGs with prerequisite relations

---

## Tool Evaluation: Cognee Recommended

### Why Cognee

For the specific use case evaluated (hundreds of raw multi-format documents → knowledge graph → multi-hop retrieval → local execution → LLM-agnostic → open source):

| Requirement | Cognee |
|-------------|--------|
| Bulk document ingestion | 38+ formats via ECL pipeline |
| Knowledge graph construction | Native 6-stage pipeline (classify → permissions → chunk → extract graph → summarize → embed) |
| Multi-hop retrieval | 15 search types including graph completion, decomposition, chain-of-thought |
| Local execution | Fully local: Ollama/llama.cpp + Fastembed + Kuzu + LanceDB + SQLite |
| LLM-agnostic | 11 LLM providers, 12 embedding providers, configurable independently |
| Open source | Apache-2.0 |
| MCP server | Official, 14 tools, Docker deployment |
| Self-improvement | Prunes stale nodes, strengthens frequent connections, adds derived facts |
| Community | ~17.2k GitHub stars, active development (last commit May 2026) |

### Cognee Architecture

**Storage (three-tier polystore):**
- Relational: SQLite (default) / PostgreSQL
- Vector: LanceDB (default, file-based) / Qdrant / pgvector / Redis / ChromaDB / Pinecone / Milvus / Weaviate
- Graph: Kuzu (default, embedded) / Neo4j / FalkorDB / Amazon Neptune / Memgraph / NetworkX

**Cognify pipeline (6 stages):**
1. Classify documents → Document objects with metadata
2. Check permissions → write access verification
3. Extract chunks → DocumentChunk units with token counts
4. Extract graph → LLM identifies entities and relationships; deduplication and coreference resolution
5. Summarize text → concise summaries per chunk as TextSummary DataPoints
6. Add data points → embed and persist across vector and graph stores

**15 search types (SearchType enum):**
SUMMARIES, CHUNKS, CHUNKS_LEXICAL, RAG_COMPLETION, TRIPLET_COMPLETION, GRAPH_COMPLETION (default), GRAPH_COMPLETION_DECOMPOSITION, GRAPH_SUMMARY_COMPLETION, GRAPH_COMPLETION_COT, GRAPH_COMPLETION_CONTEXT_EXTENSION, CYPHER, NATURAL_LANGUAGE, TEMPORAL, CODING_RULES, FEELING_LUCKY (auto-selects best type).

**Ontology support:** Optional layer that grounds entity extraction in domain-specific taxonomies (e.g., SNOMED CT for medical, FIBO for finance). Entities receive an `ontology_valid` flag. Particularly valuable for structured domains like statistics where formal mathematical taxonomy exists.

### Competitive Landscape

| Tool | Why Not Selected | Stars |
|------|-----------------|-------|
| **Microsoft GraphRAG** | Text-only ingestion, expensive indexing (3-5x), no native vector store, no MCP server | ~33k |
| **LlamaIndex** | Framework (assemble yourself), no turnkey ingest-and-search. Has Cognee integration package. | ~49k |
| **LangChain/LangGraph** | Orchestration layer, not standalone KG solution. More glue code. | ~103k |
| **R2R (SciPhi)** | Closest competitor. Production REST API, 38+ formats, Triplex model (98% cheaper extraction). Smaller community. Worth watching. | ~7.8k |
| **Mem0** | Graph features paywalled ($249/month). OSS is vector-only. Memory-focused, not doc ingestion. | ~55.8k |
| **Zep/Graphiti** | Temporal KG (unique strength). Designed for conversational data, not bulk docs. | ~26.1k |
| **Letta (MemGPT)** | Agent runtime with memory, not KG system. No knowledge graph, no multi-hop. | ~22.7k |
| **MemPalace** | Conversation memory tool. No PDF/image ingestion. ChromaDB + hierarchical metaphor. | ~52.3k |
| **MindsDB** | Database federation layer. "Knowledge Bases" are vector stores, not graphs. Elastic License (not OSS). | ~39.2k |
| **MemoryLake** | Closed-source, cloud-only, proprietary. Too new (March 2026). No self-host. | N/A |
| **Neo4j direct** | Most mature graph DB but infrastructure only — you build everything yourself. | ~13k |

### Implementation Path (when activated)

1. Install Cognee: `pip install cognee`
2. Configure: Anthropic for LLM + Fastembed for local embeddings (or Ollama for fully local)
3. Install cognee-mcp: Docker deployment, connect to Claude Code
4. Bulk-add raw documents: `cognee.add()` handles 38+ formats
5. Run cognify: builds knowledge graph (entity extraction, relationship mapping, summarization)
6. Validate multi-hop: query across concepts to confirm relationship traversal works
7. Progressively enhance: run `/content-enhancer` on high-value documents, feed enhanced output back into Cognee
8. Evaluate community detection: as graph matures, assess whether GraphRAG-style community summaries add value for corpus-level queries

---

## Key Insights

1. **Graph operators > graph structure.** How you traverse and rank matters more than how you store. Personalized PageRank consistently outperforms static weighted formulas.
2. **Community detection is the core GraphRAG innovation.** It bridges entity-level and corpus-level understanding. Without it, graph RAG only answers "what's related to X?" not "what are the themes?"
3. **Ingest-time synthesis is now a recognized pattern.** Pre-computing summaries at ingest (GraphRAG communities, Karpathy wiki pages) trades storage for query latency and quality.
4. **Cost matters.** KG extraction is 3-5x baseline RAG. The cost/scale decision framework should be applied before committing to graph infrastructure.
5. **The Karpathy wiki pattern emerges naturally from existing tools.** Raw documents → `/content-enhancer` output → domain index = the three-layer architecture (raw → compiled → schema). Cognee adds the graph layer underneath for relationship-aware retrieval.

---

## Sources

- [Microsoft GraphRAG (arXiv 2404.16130)](https://arxiv.org/abs/2404.16130)
- [LazyGraphRAG (Microsoft Research, 2025)](https://www.microsoft.com/en-us/research/blog/lazygraphrag-setting-a-new-standard-for-quality-and-cost/)
- [HippoRAG (NeurIPS 2024 / ICLR 2025)](https://github.com/osu-nlp-group/hipporag)
- [LEGO-GraphRAG (VLDB 2025)](https://arxiv.org/html/2411.05844v3)
- [ArchRAG (AAAI 2026)](https://arxiv.org/abs/2502.09891)
- [Math Academy Knowledge Graph (Skycak)](https://www.justinmath.com/how-math-academy-creates-its-knowledge-graph/)
- [Cognee Documentation](https://docs.cognee.ai/)
- [Cognee GitHub](https://github.com/topoteretes/cognee)
- [KG Quality Metrics (HAL 2025)](https://hal.science/hal-05236372v1/document)
- [Graph Operators Analysis (arXiv 2506.05690v3)](https://arxiv.org/html/2506.05690v3)
- [Karpathy LLM Wiki Pattern](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)
