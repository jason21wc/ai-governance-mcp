# Multimodal RAG Methods v2.1.1
## Operational Procedures for Retrieving and Presenting Visual Content

> **SYSTEM INSTRUCTION FOR AI AGENTS:**
> This methods document provides HOW-TO procedures for implementing multimodal RAG domain principles. It is subordinate to the domain principles document (multimodal-rag-domain-principles-v2.1.0.md), which establishes WHAT governance applies.

---

## 1 Presentation Patterns

### 1.1 Image Placement Workflow

When responding with images, follow this sequence:

```
1. PARSE query to identify:
   - What user is asking (procedural steps? concept explanation? troubleshooting?)
   - Which steps/concepts need visual support
   - Audience signals (vocabulary, role mentions)

2. RETRIEVE candidate images for each identified need
   - Apply §1.3 Image Selection Algorithm
   - Score using A2 Relevance Scoring

3. PLAN response structure:
   - Text for each step/concept
   - Image placement points (after introducing the concept, before moving on)
   - Ensure P1 (Inline Integration) compliance

4. GENERATE response:
   - Write text for Step/Concept N
   - Insert image immediately after
   - Continue to Step/Concept N+1
   - No permission-asking (P2)

5. VERIFY before sending:
   - Each image placed after its introduction?
   - No orphan images?
   - Text complexity appropriate (P4, P5)?
   - Alt text present for every image (P5)?
   - Cross-modal consistency verified (V1)?
   - Claims attributed to sources (CT1)?
```

### 1.2 Inline Placement Rules

| Content Type | Placement Rule | Example |
|--------------|----------------|---------|
| Procedural steps | Image after step instruction, before next step | "Click the Settings icon. [screenshot] Next, select..." |
| Concept explanation | Image after concept introduction | "The dashboard shows real-time metrics. [screenshot] The key indicators are..." |
| Troubleshooting | Image showing error/state being discussed | "If you see this error: [screenshot] The solution is..." |
| Comparison | Images side-by-side or sequential with clear labels | "Before: [image1] After: [image2]" |

### 1.3 Image Selection Algorithm (Mayer-Based)

Based on Mayer's Multimedia Learning Theory principles. See P3 for rationale.

```
Input: Query Q, Candidate images I[], Current selection S[]

1. SCORE each candidate image i:
   relevance_score(i) =
     semantic_similarity(Q, i) * 0.6 +
     content_type_match(Q, i) * 0.25 +
     recency(i) * 0.1 +
     step_alignment(Q, i) * 0.05

2. RANK images by relevance_score descending

3. FOR each candidate image j (in score order):
   # Mayer's Three-Test Framework
   coherence_pass = image_directly_supports_instruction(j, Q)
   unique_value_pass = image_adds_info_not_in_text(j, Q)
   proximity_pass = image_can_be_placed_adjacent_to_text(j)

   IF coherence_pass AND unique_value_pass AND proximity_pass:
     IF S[] is empty:
       Add j to S[]  # Best image
     ELSE:
       # Check for redundancy with already-selected images
       IF NOT overlaps_with_existing(j, S[]):
         Add j to S[]

4. RETURN S[] (typically 1-2 images; prefer fewer when uncertain)
```

**Three-Test Definitions:**

| Test | Implementation |
|------|----------------|
| `coherence_pass` | Image content directly relates to the specific instruction/step being explained |
| `unique_value_pass` | Image conveys information that text alone cannot adequately express |
| `proximity_pass` | Image can be placed immediately adjacent to relevant text (not orphaned) |
| `overlaps_with_existing` | New image shows substantially same information as already-selected image |

### 1.4 Content-Type Matching

| Query Intent | Preferred Image Type | Avoid |
|--------------|---------------------|-------|
| "How do I..." (procedural) | UI screenshot, step-by-step | Conceptual diagrams |
| "What is..." (conceptual) | Diagram, flowchart | Raw UI screenshots |
| "Why does..." (troubleshooting) | Error state screenshot | Success state images |
| "Where is..." (navigation) | Annotated screenshot with highlight | Full-page screenshots |
| "Compare..." | Side-by-side comparison | Single images |

### 1.5 Readability Standards

**Default (9th-grade level):**
- Sentence length: 15-20 words average
- Paragraph length: 3-5 sentences
- Vocabulary: Common words; define technical terms on first use
- Structure: Short paragraphs, clear headings, numbered steps

**Technical audience (detected by signals):**
- Can use domain terminology without definition
- Can reference advanced concepts
- Still prefer clarity over complexity

**Audience signals to detect:**
- Vocabulary used in query
- Role/title mentioned ("as a developer...", "I'm a new employee...")
- Platform context (internal tool vs. public documentation)
- Prior conversation history

### 1.6 Accessibility Implementation Checklist

**Purpose:** Operational procedures for implementing P6 (Accessibility Compliance). Ensures WCAG 2.1 AA standards are met for all visual content in multimodal RAG responses.

**Applies To:** Any system presenting visual content to users, including AI responses, documentation, and knowledge base interfaces.

**Per-Image Checklist:**

- [ ] **Alt text present** — Every image has descriptive alt text (not just filename)
- [ ] **Alt text quality** — Alt text describes the essential information the image conveys, not just what it looks like
- [ ] **Decorative vs. informative** — Decorative images marked as such (empty alt=""); informative images have meaningful descriptions
- [ ] **Color independence** — No information conveyed solely through color; use labels, patterns, or position as well
- [ ] **Contrast ratio** — Text in images meets 4.5:1 minimum contrast ratio (AA level)
- [ ] **Text alternatives for complex images** — Charts, graphs, and diagrams include a text summary of key findings
- [ ] **Scalability** — Images remain legible when zoomed to 200%

**Per-Response Checklist:**

- [ ] **Reading order** — Screen reader will encounter images in logical sequence relative to text
- [ ] **Image captions** — Where captions are used, they describe the image's purpose in context
- [ ] **Link text** — If images are clickable, link text describes the destination
- [ ] **No auto-play** — No animated images or auto-playing content without user control

**Audio Description Guidance (for video/animated content):**

When advising on content that includes video or animated sequences:
- Recommend audio descriptions for visual-only information
- Suggest closed captions for all spoken content
- Note that auto-generated captions need human review for accuracy

**References:**
- WCAG 2.1 AA (W3C): https://www.w3.org/WAI/WCAG21/quickref/
- DOJ 2026 Mandate: Digital accessibility requirements for public-facing services

---

## 2 Reference Document Structuring

### 2.1 Document Organization Template

```markdown
# [Procedure/Concept Name]

## Overview
[1-2 sentence summary of what this document covers]

## Prerequisites
[What user needs before starting]

---

## Step 1: [Action Title]

[Instruction text - keep sentences 15-20 words]

![Step 1: [Descriptive title]](path/to/image.png)

*Alt: [What the image shows - for accessibility]*

*Context: [When/why this image is relevant - for retrieval]*

*Tags: [procedure-name, step-1, relevant-concepts]*

[Additional context if needed]

---

## Step 2: [Action Title]

[Continue pattern...]
```

### 2.2 Image Description Requirements

**Alt Text (Required):**
- Describes WHAT the image shows
- Serves accessibility (screen readers)
- Example: "Opera PMS guest profile screen showing the upgrade button highlighted in the Actions menu"

**Context Description (Required):**
- Explains WHY/WHEN this image is relevant
- Serves retrieval optimization
- Example: "Use this image when explaining how to initiate a room upgrade for an existing guest reservation"

**Metadata Tags (Required):**
- Procedure/process name
- Step number if applicable
- Key concepts shown
- UI elements featured
- Example: `guest-upgrade, step-2, actions-menu, profile-screen`

### 2.3 Metadata Schema

```yaml
image_metadata:
  file: "upgrade-step-2.png"
  alt_text: "Opera PMS guest profile with Actions menu expanded"
  context: "Shows location of upgrade button for guest room upgrade process"
  tags:
    procedure: "guest-upgrade"
    step: 2
    concepts: ["actions-menu", "room-upgrade", "guest-profile"]
    ui_elements: ["profile-header", "actions-dropdown"]
    audience: ["front-desk", "reservations"]
  created: "2026-01-15"
  source_document: "front-desk-procedures.md"
  section: "Room Upgrades"
```

### 2.4 Collocation Verification Checklist

Before publishing reference documents:

- [ ] Every image appears within 2 paragraphs of its related text
- [ ] No image galleries or appendices separating images from context
- [ ] Each image has alt text (accessibility)
- [ ] Each image has context description (retrieval)
- [ ] Each image has metadata tags (filtering)
- [ ] Step-by-step procedures have images at each visual step
- [ ] Consistent image naming convention throughout document

### 2.5 Content Ingestion Assistance Workflow

**Content Ingestion Assistance** procedure for AI agents assisting users with preparing multimodal content for RAG knowledge bases. Follow this workflow when a user uploads images, screenshots, or raw documentation and requests help incorporating them into a multimodal RAG system.

#### Step 1: Intake Assessment

When a user provides raw materials (screenshots, images, documents):

1. **Identify content type** — procedural UI steps, conceptual diagram, troubleshooting, or reference
2. **Assess image quality** — legibility, completeness, appropriate UI state shown
3. **Sensitive Data Screening** — scan for PII, credentials, internal IDs, or other sensitive data requiring masking. Flag to user and do NOT proceed with that image until the user confirms it has been masked or cleared
4. **Determine context** — what procedure or concept does this content support?
5. **Ask clarifying questions** — target audience, related procedures, where this fits in the existing knowledge base

#### Step 2: Image Analysis and Text Generation

For each image the user provides:

1. **Generate alt text** per §2.2 — describe WHAT the image shows (serves accessibility)
2. **Generate context description** per §2.2 — explain WHY/WHEN this image is relevant (serves retrieval optimization, R2)
3. **Generate metadata tags** per §2.3 — procedure name, step number, concepts, UI elements, audience
4. **Produce the §2.3 YAML metadata block** — filled out with all applicable fields
5. **Present all generated text to user** for review and correction before proceeding

**Image Analysis and Text Generation** produces the three required description layers (alt text, context, tags) in a single pass per image, ensuring consistency across layers.

#### Step 3: Document Assembly

Using the §2.1 template, structure the content:

1. **Collocate images with related text** — every image appears within context of its related instruction (R1)
2. **Write or refine step/concept text** to pair with each image
3. **Place images inline** after the instruction they illustrate, before the next step (P1)
4. **Add cross-references** to related procedures in the knowledge base
5. **Match text complexity** to the target audience (P4, P5)

#### Step 4: Quality Validation

Run checks against the assembled document:

1. **Execute §2.4 Collocation Verification Checklist** — flag any failures
2. **Legibility check** — can all text in screenshots be read at standard display size?
3. **Accuracy check** — does each screenshot match the written instruction it accompanies?
4. **Completeness check** — are there gaps where a visual would help but is missing?
5. **Tag consistency check** — are tags consistent with existing documents in the knowledge base? (R3)
6. **PII re-check** — scan for any sensitive data that may have been missed in Step 1

#### Step 5: Retrieval Optimization

Optimize the prepared content for retrieval quality:

1. **Search term alignment** — verify that generated alt text and context descriptions contain terms users would actually search for
2. **Tag expansion** — suggest additional tags based on common query patterns for this domain (R3)
3. **Chunking guidance** — recommend chunking boundaries if the document is long (cross-reference §3.5 Vision-Guided Chunking)
4. **Document-as-image considerations** — if the knowledge base uses document-as-image retrieval (A4), advise on image resolution and format requirements
5. **Knowledge graph extraction** — if the knowledge base uses knowledge graphs (A5), identify entities and relationships to extract

**Retrieval Optimization** bridges content preparation and the retrieval pipeline, ensuring prepared documents are findable through the architecture described in Title 3.

> **Batch Processing Pattern**
>
> When a user needs to document an entire workflow (e.g., a full multi-step procedure):
>
> 1. Guide the user to walk through the complete procedure first and capture all screenshots in one pass (ensures consistent UI state)
> 2. Process all images through Steps 1–5 as a batch
> 3. Generate cross-links between related procedure documents
> 4. Validate tag consistency across the full document set
>
> **Batch Processing Pattern** avoids the inconsistency that arises from documenting steps piecemeal across separate sessions.

---

## 3 Retrieval Architecture

### 3.1 Four-Layer Architecture

```
+------------------------------------------------------------+
|                    Layer 1: Query Processing                 |
|  Intent Classification > Query Expansion > Audience Detection|
+------------------------------+-----------------------------+
                               |
+------------------------------v-----------------------------+
|                  Layer 2: Multimodal Embedding               |
|  Text Embedding <-> Unified Space <-> Image Embedding        |
|  (ColPali, ColQwen2, or similar)                            |
+------------------------------+-----------------------------+
                               |
+------------------------------v-----------------------------+
|                  Layer 3: Retrieval & Ranking                |
|  Vector Search > Metadata Filter > Relevance Scoring         |
|  (Apply A2 multi-signal scoring)                            |
+------------------------------+-----------------------------+
                               |
+------------------------------v-----------------------------+
|                  Layer 4: Response Generation                |
|  Text Generation < Image Placement < Failure Handling        |
|  (Apply P-Series, V-Series, CT-Series, and F-Series)       |
+------------------------------------------------------------+
```

### 3.2 Embedding Model Selection

| Model Family | Strengths | Considerations |
|--------------|-----------|----------------|
| **ColPali** | Late interaction, fine-grained matching | Newer, evolving ecosystem |
| **ColQwen2** | Strong multimodal understanding | Similar architecture to ColPali |
| **CLIP-based** | Widely deployed, stable | Less fine-grained than late interaction |
| **Custom fine-tuned** | Domain-specific optimization | Requires training infrastructure |

**Selection Criteria:**
1. Does the model support unified text-image embedding space? (A1)
2. What is latency for your query volume?
3. What is embedding dimension and storage cost?
4. Does the model handle your image types well? (screenshots, diagrams, photos)

### 3.3 Relevance Scoring Implementation

```python
def relevance_score(query, image, config):
    """
    Multi-signal relevance scoring per A2 principle.

    Weights are configurable per deployment.
    Default weights optimized for procedural documentation.
    """
    weights = config.get('weights', {
        'semantic': 0.60,
        'content_type': 0.25,
        'recency': 0.10,
        'step_alignment': 0.05
    })

    # Semantic similarity from embedding space
    semantic = cosine_similarity(
        embed_text(query),
        embed_image(image)
    )

    # Content type match (screenshot for UI query, diagram for concept)
    query_intent = classify_intent(query)  # procedural, conceptual, troubleshooting
    image_type = image.metadata.get('type')  # screenshot, diagram, photo
    content_type = content_type_score(query_intent, image_type)

    # Recency (for rapidly-changing UIs)
    days_old = (today() - image.metadata.get('created')).days
    recency = max(0, 1 - (days_old / config.get('recency_halflife', 180)))

    # Step alignment (for procedural queries)
    if query_intent == 'procedural':
        query_step = extract_step_reference(query)
        image_step = image.metadata.get('step')
        step_alignment = 1.0 if query_step == image_step else 0.5
    else:
        step_alignment = 0.5  # neutral for non-procedural

    return (
        weights['semantic'] * semantic +
        weights['content_type'] * content_type +
        weights['recency'] * recency +
        weights['step_alignment'] * step_alignment
    )
```

### 3.4 Chunk Strategy for Multimodal Documents

When indexing documents with images:

```
Document: front-desk-procedures.md
+-- Chunk 1: "## Step 1: Access Guest Profile\n[text]\n[IMAGE_REF: step1.png]"
+-- Chunk 2: "## Step 2: Open Actions Menu\n[text]\n[IMAGE_REF: step2.png]"
+-- Chunk 3: "## Step 3: Select Upgrade Option\n[text]\n[IMAGE_REF: step3.png]"
```

**Key principles:**
- Keep images with their text context in same chunk
- Include image metadata in chunk for filtering
- Chunk boundaries at logical breaks (steps, sections)
- Embed both text content and image for each chunk

### 3.5 Vision-Guided Chunking Procedures

**Purpose:** Operational procedures for implementing A3 (Vision-Guided Chunking). Ensures visual elements are preserved as complete units during document indexing.

**Applies To:** Any document processing pipeline that chunks multimodal documents for embedding and retrieval.

**Visual Element Detection:**

Before chunking, identify visual elements using layout analysis:

```
1. SCAN document for visual elements:
   - Tables (detected by grid structure, | characters, or HTML <table>)
   - Charts/graphs (detected by axis labels, legends, data points)
   - Diagrams (detected by shapes, arrows, flow patterns)
   - Code blocks (detected by ``` fencing or indentation)
   - Images with captions (detected by ![...] markdown or <img> tags)

2. MARK element boundaries:
   - Start: first line of the visual element (or its title/caption)
   - End: last line of the visual element (or trailing caption/notes)
   - Context: preceding paragraph (up to 3 sentences) for semantic grounding

3. CLASSIFY elements:
   - ATOMIC: Must not be split (tables, charts, diagrams)
   - CAPTIONED: Must stay with caption (images, figures)
   - CONTEXTUAL: Must stay with surrounding text (inline code, formulas)
```

**Chunking Rules:**

| Visual Element | Chunking Rule | Max Chunk Size Override |
|----------------|---------------|------------------------|
| Table (< 50 rows) | Keep complete with title and any notes | 2x normal chunk size |
| Table (>= 50 rows) | Split at logical row groups (sections, categories) | 1.5x normal chunk size per group |
| Chart/Graph | Keep complete with title, legend, and axis labels | 2x normal chunk size |
| Diagram | Keep complete with all labels and caption | 2x normal chunk size |
| Image + Caption | Keep image reference with caption and preceding paragraph | 1.5x normal chunk size |
| Code block | Keep complete with preceding context sentence | 2x normal chunk size |

**Validation Checklist:**

- [ ] No table is split mid-row
- [ ] No diagram is separated from its caption or legend
- [ ] No chart is separated from its axis labels
- [ ] Each visual element chunk includes at least one sentence of surrounding context
- [ ] Chunk size overrides are logged for monitoring

### 3.6 Cross-Modal Reference Linking

**Purpose:** Procedures for maintaining links between text references and visual elements across chunks.

**Applies To:** Systems where text in one chunk references visual elements in another chunk.

**Reference Types:**

| Reference Pattern | Detection | Action |
|-------------------|-----------|--------|
| "See Figure N" / "See Table N" | Regex: `[Ss]ee\s+(Figure|Table|Chart|Diagram)\s+\d+` | Store bidirectional link between text chunk and visual chunk |
| "As shown above/below" | Proximity: find nearest visual element | Store positional reference |
| Explicit image reference | Markdown: `![...]` or HTML: `<img>` | Ensure image ref and text in same chunk |
| Footnote/endnote to visual | Footnote pattern + visual ID | Store reference mapping |

**Link Storage Schema:**

```yaml
cross_modal_references:
  - source_chunk_id: "chunk-042"
    target_chunk_id: "chunk-038"
    reference_type: "figure_reference"
    reference_text: "See Figure 3"
    target_element: "figure-3"
  - source_chunk_id: "chunk-055"
    target_chunk_id: "chunk-055"
    reference_type: "inline_image"
    reference_text: "![Dashboard overview]"
    target_element: "dashboard-overview.png"
```

**At Query Time:**
When a text chunk is retrieved, also retrieve any linked visual element chunks. Present them together in the response per P1 (Inline Integration).

### 3.7 Late Interaction and Document-as-Image Retrieval

**Purpose:** Procedures for implementing A4 (Document-as-Image Retrieval). Defines when and how to use late interaction models (ColPali, ColQwen2, ColEmbed V2) that treat document pages as images rather than extracting text.

**Applies To:** Document collections where layout, formatting, tables, or visual annotations carry semantic meaning that text extraction destroys.

**Paradigm Decision Tree:**

| Document Characteristic | Recommended Paradigm | Rationale |
|------------------------|---------------------|-----------|
| Plain text (articles, manuals, code) | Text extraction + standard embedding | Layout carries no semantic meaning |
| Simple tables (uniform structure) | Text extraction with table parser | Structure can be faithfully extracted |
| Complex tables (merged cells, nested headers) | Document-as-image | Extraction often fails on complex table structures |
| Infographics, annotated diagrams | Document-as-image | Visual arrangement IS the content |
| Forms with spatial relationships | Document-as-image | Field-value spatial relationships lost in extraction |
| Mixed content (text + figures on same page) | Hybrid (both pipelines) | Use text extraction for prose, image for figures |

**Multi-Vector Indexing Procedure:**

```
Input: Document page P (as image), Model M (ColPali/ColQwen2/ColEmbed V2)

1. ENCODE page P through vision-language model M:
   - Output: Set of patch embeddings E[] (one per image patch, typically 1024+ per page)
   - Each patch embedding captures local visual + textual features

2. INDEX patch embeddings:
   - Store all patch embeddings with page_id metadata
   - Storage requirement: ~N_patches × embedding_dim × 4 bytes per page
   - Typical: 1024 patches × 128 dims = 512 KB per page (vs. ~1 KB for single-vector)

3. AT QUERY TIME:
   - Encode query Q through model M's text encoder
   - Compute late interaction score: MaxSim(Q_tokens, P_patches)
   - Score = sum over query tokens of max similarity to any page patch
   - This enables fine-grained matching: specific query terms match specific page regions

4. RANK pages by late interaction score
```

**When to Use vs. Text Extraction:**

```
Decision: Use document-as-image retrieval IF:
  - Text extraction quality < 90% (measured on sample) OR
  - Document contains >30% visual/layout content OR
  - Users report "can't find" for content that exists in documents OR
  - A/B test shows higher retrieval quality with image-based indexing

Decision: Use text extraction IF:
  - Documents are primarily prose text OR
  - Storage budget is constrained (multi-vector is 100-500x more per page) OR
  - Latency budget is constrained (VLM inference is slower than text encoding)
```

**Cost-Quality Reference:**

| Metric | Text Extraction | Document-as-Image | Notes |
|--------|----------------|-------------------|-------|
| Storage per page | ~1 KB (single vector) | ~500 KB (multi-vector) | 500x increase |
| Index time per page | ~10ms (text encode) | ~200ms (VLM encode) | 20x increase |
| Query latency | ~5ms (ANN search) | ~50ms (MaxSim) | 10x increase |
| Retrieval quality (layout-rich) | Low-Medium | High | Main benefit |
| Retrieval quality (text-only) | High | Medium-High | Text extraction wins here |

### 3.8 Graph-Based Multimodal Retrieval

**Purpose:** Procedures for implementing A5 (Knowledge Graph Integration). Defines how to construct and query a knowledge graph from multimodal content for relationship-aware retrieval.

**Applies To:** Complex knowledge bases where entities and relationships span multiple documents and modalities. Particularly valuable when queries involve structural relationships ("what depends on X?", "how is A related to B?").

**Knowledge Graph Construction:**

```
Input: Document collection D[], Modalities: text, images, tables

1. ENTITY EXTRACTION:
   - Text: Apply NER (Named Entity Recognition) for persons, organizations,
     components, concepts, versions
   - Images: Apply visual object detection for components, UI elements,
     diagram entities
   - Tables: Extract row/column headers as entity types, cell values as
     entity instances

2. ENTITY RESOLUTION:
   - Match entities across modalities (text "Login Button" ↔ image region
     containing login button)
   - Resolve aliases ("Auth Module" = "Authentication Module" = component
     in diagram)
   - Assign canonical entity IDs

3. RELATIONSHIP EXTRACTION:
   - Text: Extract relationships from sentence structure ("X depends on Y",
     "X connects to Y")
   - Images: Extract spatial relationships from diagrams (containment,
     connection, flow arrows)
   - Tables: Extract column relationships (row entity has attribute
     column value)

4. GRAPH CONSTRUCTION:
   - Nodes: Resolved entities with attributes (type, source_doc,
     source_modality, embedding)
   - Edges: Relationships with attributes (type, confidence, source_doc)
   - Store: Graph database (Neo4j, NetworkX for small scale) + vector index
     on node embeddings
```

**Graph-Augmented Retrieval Procedure:**

```
Input: Query Q, Knowledge Graph G, Vector Index V

1. VECTOR RETRIEVAL: Standard top-K retrieval from V
   - Returns document chunks related to Q

2. ENTITY MATCHING: Identify entities in Q that exist in G
   - Match query terms to graph node labels/aliases

3. GRAPH EXPANSION: For matched entities, traverse G:
   - 1-hop neighbors: directly related entities
   - 2-hop neighbors: entities related to related entities (use sparingly)
   - Filter by relationship type relevance to query

4. AUGMENTED RETRIEVAL: For each graph-expanded entity:
   - Retrieve the document chunks containing that entity
   - Score by: graph_relevance * 0.4 + vector_relevance * 0.6

5. MERGE: Combine vector results and graph-augmented results
   - Deduplicate by chunk ID
   - Re-rank combined set
```

**Graph Maintenance:**

| Trigger | Action | Frequency |
|---------|--------|-----------|
| New document added | Extract entities/relationships, merge into graph | On ingest |
| Document updated | Re-extract changed sections, update graph nodes/edges | On update |
| Entity conflict detected | Queue for human resolution | As needed |
| Graph quality audit | Sample-based verification of entity/relationship accuracy | Monthly |

---

## 4 Failure Handling

### 4.1 Failure Classification

| Failure Type | Code | Cause | User-Facing Message |
|--------------|------|-------|---------------------|
| Format unsupported | `format_unsupported` | Image format not renderable | "Image format not supported in this context" |
| Size exceeded | `size_exceeded` | Image too large for display/transmission | "Image exceeds size limits" |
| Retrieval failed | `retrieval_failed` | Network/storage error during fetch | "Unable to retrieve image at this time" |
| Not found | `not_found` | Image doesn't exist or was deleted | "Referenced image not available" |
| Permission denied | `permission_denied` | Access control prevents retrieval | "Access to image not permitted" |

### 4.2 Graceful Degradation Procedure

```
IF image_retrieval_fails:
    1. LOG failure with classification and details

    2. CONTINUE generating text response
       - Response MUST be complete and useful without image
       - Do NOT say "I cannot answer without the image"

    3. APPEND failure note at appropriate position:
       ---
       Note: Visual reference for [Step N / this concept] could not be displayed.
       Reason: [failure_type from section 4.1]
       Reference: [source_document, section/page] for manual lookup

    4. IF multiple images fail:
       - Group failure notes at end of response
       - Maintain readable response flow
```

### 4.3 Failure Note Templates

**Single Image Failure:**
```
---
Note: Screenshot for Step 3 could not be displayed.
Reason: Retrieval failed
Reference: See "Front Desk Procedures" document, page 12, for the visual guide.
```

**Multiple Image Failures:**
```
---
Note: Some visual references could not be displayed:
- Step 2 screenshot: Format not supported in this context
- Step 5 diagram: Image not available
Reference: See "System Administration Guide" sections 4.2 and 4.5 for visuals.
```

**Critical Image Failure (escalation):**
```
---
Note: The visual reference that typically accompanies this procedure could not be loaded.
Reason: [reason]
Recommendation: This procedure is highly visual. Consider accessing the source document directly:
- Document: [name]
- Section: [section]
- Or contact support if this persists.
```

### 4.4 Failure Logging Schema

```yaml
failure_log:
  timestamp: "2026-01-24T14:30:00Z"
  query_id: "q-12345"
  image_ref: "upgrade-step-3.png"
  failure_type: "retrieval_failed"
  error_detail: "Connection timeout after 5000ms"
  fallback_applied: true
  reference_provided: "front-desk-procedures.md, section 3.3"
  user_notified: true
```

---

## 5 Verification and Hallucination Prevention

### 5.1 Cross-Modal Consistency Check

**Purpose:** Procedures for implementing V1 (Cross-Modal Consistency Verification). Ensures text descriptions match retrieved image content.

**Applies To:** Any response that combines generated text with retrieved images.

**Verification Workflow:**

```
1. DRAFT text that references or describes image content

2. RE-EXAMINE the image with specific attention to:
   - Object presence: Are all described objects actually visible?
   - Attribute accuracy: Colors, sizes, labels, counts correct?
   - Spatial relationships: "left of", "above", "next to" verified?
   - Text in image: Any text/labels readable and correctly cited?

3. COMPARE draft text against image:
   - Mark each image-referencing claim as VERIFIED or UNVERIFIED
   - For UNVERIFIED claims: correct text or add uncertainty qualifier

4. RESOLVE conflicts:
   - If text contradicts image: ALWAYS prefer what the image shows
   - If image is ambiguous: State the ambiguity explicitly
   - If multiple images conflict: Note the discrepancy per V1 (CoRe-MMRAG)
```

**Conflict Resolution Matrix:**

| Conflict Type | Resolution | Example |
|---------------|------------|---------|
| Text says X, image shows Y | Correct text to match image | "The blue button" -> "The green button" (matching screenshot) |
| Text describes element absent from image | Remove claim or add qualifier | "The sidebar shows..." -> "The sidebar (not visible in this view) typically shows..." |
| Multiple images show different states | Note both states, indicate which is current | "Figure A shows the old layout; Figure B shows the current design" |
| Image too low-resolution to verify | State uncertainty | "The label appears to read 'Settings' (image resolution limits certainty)" |

### 5.2 Visual Scene Graph Validation

**Purpose:** Procedures for implementing V2 (Visual Scene Graph Checking). Prevents hallucinated visual descriptions.

**Applies To:** Any text that describes the content of an image.

**Validation Steps:**

```
Before asserting any visual detail, verify:

1. OBJECTS: List objects you can definitively identify in the image
   - Only claim objects you can see, not objects you expect to see
   - "The image shows a dialog box with two buttons" (verified count)

2. ATTRIBUTES: For each object, verify observable attributes
   - Color: Only state if clearly discernible
   - Size: Use relative terms ("larger than", "approximately half")
   - State: Active/inactive, expanded/collapsed, checked/unchecked

3. SPATIAL LAYOUT: Verify positions before claiming them
   - Use image quadrants: "upper-left", "center", "bottom-right"
   - Verify adjacency: "next to the search bar" (confirm search bar is visible)

4. TEXT IN IMAGE: Only quote text that is legible
   - If partially legible: "The heading reads '[readable part]...'"
   - If illegible: "A text label is present but not legible at this resolution"
```

**Red Flags (likely hallucination):**

| Signal | Risk | Action |
|--------|------|--------|
| Describing specific text you cannot read | High | Remove specific text, note illegibility |
| Counting items in a dense area | Medium | Qualify with "approximately" |
| Describing colors in a low-contrast image | Medium | Use hedging language |
| Referencing UI elements by name without visible label | High | Describe by position instead |

### 5.3 Modality Conflict Resolution

**Purpose:** Procedures for handling conflicts between retrieved text and image sources. Based on CoRe-MMRAG (ACL 2025) methodology.

**Applies To:** Responses that synthesize information from both text and image sources.

**Decision Framework:**

```
When text source and image source provide conflicting information:

1. IDENTIFY the conflict explicitly
   - "The text manual states [X], but the screenshot shows [Y]"

2. ASSESS which is more likely current:
   - Image dated more recently? Prefer image.
   - Text updated after image? Prefer text.
   - No date information? Flag uncertainty.

3. PRESENT resolution:
   - State both pieces of information
   - Indicate which you believe is more current and why
   - Recommend the user verify with the primary source

4. NEVER silently pick one over the other
```

### 5.4 Visual-Textual Inconsistency Handling

**Purpose:** Specific handling procedures for the most common inconsistency patterns.

| Inconsistency Pattern | Detection | Response Template |
|----------------------|-----------|-------------------|
| UI has changed since screenshot | Screenshot shows old layout; text describes new layout | "Note: The screenshot shows an earlier version of this interface. The current layout may differ. [Describe known changes if available.]" |
| Caption doesn't match image | Image metadata/caption describes different content | Do not use the caption. Describe what the image actually shows. |
| Step numbering mismatch | Text says "Step 3" but image shows "Step 4" content | "The image shows the state after Step [correct number]. [Describe what's shown.]" |
| Partial image (cropped) | Image is cropped and missing elements referenced in text | "Note: The image shows a partial view. [Element X] referenced in the instructions is not visible in this screenshot." |

### 5.5 Multi-Hop Cross-Modal Reasoning Verification

**Purpose:** Procedures for implementing V4 (Cross-Modal Reasoning Chain Integrity). Defines chain integrity checks, hop-level error detection, and propagation control for multi-hop cross-modal reasoning.

**Applies To:** Queries that require reasoning across multiple modalities in sequence (e.g., identify component in image → find specification in table → verify against diagram).

**Chain Integrity Check Procedure:**

```
Input: Multi-hop reasoning chain C = [hop_1, hop_2, ..., hop_n]
       Each hop_i = {source_modality, source_element, conclusion, confidence}

FOR each hop_i in C:
  1. VERIFY hop independently:
     - Does the source element support the conclusion?
     - Is the modality transition valid (e.g., image element → table lookup)?
     - Confidence above threshold? (default: 0.6 per hop)

  2. VERIFY chain consistency:
     - Does hop_i conclusion align with hop_{i-1} conclusion?
     - Are there contradictions between hop results?

  3. COMPUTE cumulative confidence:
     - chain_confidence = product(hop_confidences)
     - WARNING: Cumulative confidence drops rapidly
       Example: 3 hops at 0.8 each → 0.8³ = 0.512

  4. GATE decision:
     | Hop Confidence | Chain Confidence | Action |
     |---------------|------------------|--------|
     | ≥ 0.8 | ≥ 0.5 | Continue to next hop |
     | ≥ 0.6 | ≥ 0.3 | Continue with uncertainty marker |
     | < 0.6 | any | STOP chain, report partial results |
     | any | < 0.3 | STOP chain, report partial results |
```

**Error Detection at Modality Transitions:**

| Transition | Common Errors | Detection Method |
|-----------|--------------|-----------------|
| Image → Text | Misidentifying visual element | Cross-check element label against image OCR/detection |
| Text → Image | Finding wrong image for text reference | Verify image metadata matches text entity |
| Image → Table | Looking up wrong row/column | Verify entity name match between image and table header |
| Table → Diagram | Mapping wrong specification to component | Verify identifier consistency across sources |

**Chain Provenance Template:**

```yaml
reasoning_chain:
  query: "What is the max throughput for the component shown in Figure 3?"
  hops:
    - hop: 1
      source_modality: image
      source_element: "Figure 3"
      action: "Identify component in image"
      conclusion: "Component is Redis Cache Layer"
      confidence: 0.85
      verified: true
    - hop: 2
      source_modality: table
      source_element: "Table 2: Component Specifications"
      action: "Look up max throughput for Redis Cache Layer"
      conclusion: "Max throughput: 100K ops/sec"
      confidence: 0.92
      verified: true
  chain_confidence: 0.782  # 0.85 × 0.92
  status: "VERIFIED"
```

**Partial Result Reporting:**
When a chain is stopped due to low confidence:
```
Based on the available evidence:
- [Hop 1 result]: [conclusion] (verified, confidence: [score])
- [Hop 2 result]: [conclusion] (verified, confidence: [score])
- [Hop 3]: Could not be reliably completed.
  Reason: [confidence below threshold / contradictory evidence / ambiguous source]
  Suggestion: [Manually verify / Provide clearer source / Rephrase query]
```

---

## 6 Evaluation Framework

### 6.1 RAG-Check 6-Metric Implementation

**Purpose:** Procedures for implementing EV1 (Retrieval Quality Measurement) and EV2 (Answer Faithfulness Assessment). Based on RAG-Check framework (arxiv 2501.03995).

**Applies To:** Any multimodal RAG system in production or evaluation.

**The Six Metrics:**

| Metric | What It Measures | How to Calculate | Target |
|--------|-----------------|------------------|--------|
| **Claim Recall** | Proportion of source claims captured in response | (claims in response that match source) / (total claims in source) | >= 0.80 |
| **Context Relevance** | How relevant retrieved context is to the query | (relevant chunks retrieved) / (total chunks retrieved) | >= 0.70 |
| **Faithfulness** | Whether response claims are supported by sources | (supported claims) / (total claims in response) | >= 0.90 |
| **Context Utilization** | How much of retrieved context is actually used | (used context chunks) / (retrieved context chunks) | >= 0.50 |
| **Noise Sensitivity** | Whether irrelevant context causes errors | (errors introduced by irrelevant context) / (total responses with irrelevant context) | <= 0.10 |
| **Hallucination Rate** | Unsupported claims in responses | (unsupported claims) / (total claims in response) | <= 0.05 |

**Implementation Steps:**

```
1. BUILD evaluation dataset:
   - 50+ query-source-response triples
   - Include diverse query types (procedural, conceptual, troubleshooting)
   - Include queries requiring images and text-only queries
   - Label ground truth for each metric

2. RUN evaluation:
   - Submit each query to the system
   - Collect retrieved context, generated response, and source documents
   - Score each metric per the calculation method above

3. ANALYZE results:
   - Identify metrics below target
   - Root-cause analysis for failing queries
   - Prioritize improvements by metric impact

4. TRACK over time:
   - Run evaluation after every significant system change
   - Store results with system version for trend analysis
```

### 6.2 Multimodal MRR Calculation

**Purpose:** Extending Mean Reciprocal Rank for multimodal retrieval contexts.

**Standard MRR** measures rank of first relevant result. **Multimodal MRR** extends this by considering both text relevance and image relevance.

```python
def multimodal_mrr(queries, retrieval_results, ground_truth):
    """
    Calculate MRR accounting for both text and image relevance.

    A result is 'relevant' if:
    - The text chunk answers the query (text_relevant), OR
    - The associated image answers the query (image_relevant), OR
    - The combination of text + image answers the query (combined_relevant)
    """
    reciprocal_ranks = []

    for query in queries:
        results = retrieval_results[query.id]
        truth = ground_truth[query.id]

        rank = None
        for i, result in enumerate(results, 1):
            text_match = result.chunk_id in truth.relevant_chunks
            image_match = result.image_id in truth.relevant_images
            combined_match = (result.chunk_id, result.image_id) in truth.relevant_pairs

            if text_match or image_match or combined_match:
                rank = i
                break

        reciprocal_ranks.append(1.0 / rank if rank else 0.0)

    return sum(reciprocal_ranks) / len(reciprocal_ranks)
```

### 6.3 Drift Detection

**Purpose:** Procedures for implementing O2 (Continuous Monitoring & Observability). Detects quality degradation over time.

**Applies To:** Production multimodal RAG systems.

**Monitoring Setup:**

```
1. ESTABLISH baseline:
   - Run full evaluation (section 6.1) on current system
   - Record all six metrics with timestamp
   - Save as baseline_v[version].json

2. CONFIGURE drift detection:
   - Threshold: Alert if any metric drops > 10% from baseline
   - Frequency: Run benchmark suite after every index rebuild
   - Comparison: Always compare against the most recent approved baseline

3. ALERT conditions:
   - WARN: Single metric drops 5-10% from baseline
   - ALERT: Single metric drops > 10% from baseline
   - CRITICAL: Two or more metrics drop > 10% simultaneously

4. RESPONSE to alerts:
   - WARN: Log for review at next scheduled evaluation
   - ALERT: Investigate root cause within 24 hours; consider rollback
   - CRITICAL: Immediate rollback to last known-good index; investigate
```

**Drift Sources to Monitor:**

| Source | How It Causes Drift | Detection Method |
|--------|---------------------|------------------|
| Content changes | New/updated documents change retrieval landscape | Compare content hash before/after |
| Model updates | Embedding model changes alter similarity scores | Run benchmark suite pre/post |
| Weight changes | Relevance scoring weight adjustments | A/B evaluation with old vs. new weights |
| Query pattern shift | Users ask different types of questions | Monitor query intent distribution |
| Index corruption | Storage or processing errors | Validate index integrity checksums |

### 6.4 Benchmark Construction

**Purpose:** How to build and maintain a benchmark dataset for multimodal RAG evaluation.

**Benchmark Dataset Requirements:**

| Component | Minimum Count | Description |
|-----------|---------------|-------------|
| Queries | 50 | Representative of actual usage; mix of types |
| Ground truth documents | Per query | Which source documents/images should be retrieved |
| Expected response elements | Per query | Key facts that should appear in the response |
| Negative examples | 10+ | Queries that should NOT retrieve certain content |

**Construction Process:**

```
1. SAMPLE queries from production logs (if available)
   - Stratify by query type: procedural, conceptual, troubleshooting, navigation
   - Include edge cases: ambiguous queries, multi-step queries, queries requiring images

2. ANNOTATE ground truth:
   - For each query, identify the ideal retrieved chunks (text + images)
   - Mark relevance level: highly relevant, somewhat relevant, not relevant
   - Note expected image types for each query

3. VALIDATE with domain experts:
   - Have 2+ people independently annotate a subset
   - Measure inter-annotator agreement (target: Cohen's kappa >= 0.7)
   - Resolve disagreements through discussion

4. VERSION and store:
   - Store benchmark with version number tied to content snapshot
   - Update benchmark when content changes significantly
   - Keep previous versions for trend comparison
```

---

## 7 Citation and Attribution

### 7.1 Fragment-Level Source Tracking

**Purpose:** Procedures for implementing CT1 (Fragment-Level Source Attribution). Enables tracing every claim to a specific source passage.

**Applies To:** Any response that incorporates information from retrieved sources.

**Attribution Workflow:**

```
1. During retrieval, capture source metadata for each chunk:
   - document_id: Which document
   - section_id: Which section/heading
   - chunk_id: Specific chunk identifier
   - line_range: Line numbers in source document
   - image_id: Associated image (if any)

2. During response generation, maintain a claim-source mapping:
   - For each factual statement in the response, record which chunk(s) support it
   - Flag statements that synthesize from multiple chunks

3. Format attribution in response:
   - Inline: "[Source: Document Name, Section 3.2]"
   - Footnote-style: Statement[1], with [1] listed at end
   - Hover/tooltip: For interactive formats, attribution on hover
```

**Attribution Levels:**

| Level | Detail | When to Use |
|-------|--------|-------------|
| **Document-level** | "Source: Front Desk Manual" | Minimum acceptable; for simple queries |
| **Section-level** | "Source: Front Desk Manual, Section 3.2" | Standard; for most responses |
| **Fragment-level** | "Source: Front Desk Manual, Section 3.2, paragraph 3" | Ideal; for critical or disputed information |
| **Image-region** | "Source: Dashboard screenshot, upper-left metrics panel" | For visual content; see section 7.2 |

### 7.2 VISA Spatial Attribution

**Purpose:** Procedures for implementing CT2 (Spatial Attribution for Visual Content). Based on VISA methodology (arxiv 2412.14457).

**Applies To:** Responses that reference specific regions within images.

**Spatial Attribution Methods:**

**Method 1: Verbal Region Description (always available)**
```
"In the top-right corner of the dashboard screenshot, the notification bell icon
shows 3 pending alerts."
```

**Method 2: Quadrant-Based Reference**
```
Divide image into a 3x3 grid:
+----------+----------+----------+
| top-left | top-mid  | top-right|
+----------+----------+----------+
| mid-left | center   | mid-right|
+----------+----------+----------+
| bot-left | bot-mid  | bot-right|
+----------+----------+----------+

Reference: "In the top-right quadrant of the screenshot..."
```

**Method 3: Bounding Box Coordinates (when tooling supports)**
```json
{
  "attribution": {
    "image_id": "dashboard-v3.png",
    "region": {
      "x": 0.75,
      "y": 0.05,
      "width": 0.20,
      "height": 0.15
    },
    "description": "Notification bell with alert count"
  }
}
```

**When to Use Each Method:**

| Context | Recommended Method |
|---------|-------------------|
| Text-based response (chat, email) | Method 1 (Verbal) |
| Interactive UI with image overlay | Method 3 (Bounding Box) |
| Documentation or training materials | Method 2 (Quadrant) |
| Complex diagram with many elements | Methods 1 + 2 combined |

### 7.3 Citation Formatting

**Purpose:** Standard formatting for citations in multimodal RAG responses.

**Inline Citation Format:**

```
The guest profile shows the reservation status in the header bar
[Source: Front Desk Manual v3.1, Section 4.2].
```

**Multi-Source Citation Format:**

```
The upgrade process requires both a room availability check [Source: Reservations
Guide, Section 2.1] and manager approval for rate changes exceeding $50
[Source: Rate Management Policy, Section 3.4].
```

**Image Citation Format:**

```
The Actions menu (shown in the upper-right of the screenshot below) contains
the Upgrade option [Source: Opera PMS v5.6, Actions Menu screenshot, captured
2026-01-15].
```

### 7.4 Citation Verification Checklist

Before delivering a response, verify:

- [ ] Every factual claim has an identified source
- [ ] Sources are cited at the appropriate level (document/section/fragment)
- [ ] Image references include spatial attribution per section 7.2
- [ ] No claim is attributed to a source that doesn't contain it (false citation)
- [ ] Synthesized information from multiple sources notes all contributing sources
- [ ] General knowledge statements are clearly distinguished from sourced claims

---

## 8 Security for Multimodal Knowledge Bases

### 8.1 Poisoning Attack Taxonomy

**Purpose:** Classification of multimodal-specific attack types. Informs SEC1 (Multimodal Poisoning Defense) implementation.

**Applies To:** Any multimodal knowledge base that accepts content from multiple sources or undergoes regular updates.

**Attack Classification (based on MM-PoisonRAG, arxiv 2502.17832):**

| Attack Type | Mechanism | Impact | Detection Difficulty |
|-------------|-----------|--------|---------------------|
| **Localized Image Poisoning** | Adversarial image optimized to rank highly for specific queries | Targeted misinformation for specific topics | Medium |
| **Globalized Image Poisoning** | Adversarial image that disrupts retrieval across many queries | Broad retrieval quality degradation | Easier — shows up in aggregate metrics |
| **Caption Poisoning** | Legitimate image with manipulated caption/metadata | False information attributed to legitimate visual | Hard — image looks correct, text is wrong |
| **Cross-Modal Injection** | Malicious text hidden in image metadata (EXIF, XMP) | Prompt injection via metadata pipeline | Medium — requires metadata sanitization |
| **Single-Image Attack** | One poisoned document page redirects visual RAG results (arxiv 2504.02132) | High-precision targeted attack | Hard — minimal footprint in knowledge base |

### 8.2 Input Validation Pipeline

**Purpose:** Procedures for implementing SEC2 (Cross-Modal Input Validation).

**Applies To:** Any content ingestion pipeline for multimodal knowledge bases.

**Validation Stages:**

```
STAGE 1: Format Validation
  - Verify image format (PNG, JPEG, GIF, WebP, PDF)
  - Verify file size within acceptable bounds
  - Verify image dimensions within bounds
  - Reject or quarantine files that fail format checks

STAGE 2: Content Screening
  - Scan image content for anomalous patterns (statistical analysis of pixel values)
  - Check for steganographic content (LSB analysis)
  - Verify image is not adversarially optimized (embedding outlier detection)

STAGE 3: Metadata Sanitization
  - Strip non-essential EXIF data
  - Sanitize text fields in metadata (remove HTML, scripts, injection patterns)
  - Validate metadata schema conformance
  - Check caption-image consistency

STAGE 4: Cross-Modal Consistency
  - Verify caption/description matches image content (using VLM if available)
  - Check for metadata-content mismatches
  - Flag items where text description contradicts visual content

STAGE 5: Provenance Verification
  - Verify source is in allowed sources list
  - Check content signature/hash if available
  - Record full ingestion provenance per DG2
```

### 8.3 Defense Assessment Checklist

**Periodic security assessment for multimodal knowledge bases:**

- [ ] **Input validation active** — All ingestion paths run through section 8.2 pipeline
- [ ] **Embedding monitoring** — New embeddings checked for outlier distance from cluster centers
- [ ] **Caption integrity** — Sample of captions verified against image content quarterly
- [ ] **Access logs reviewed** — Query and retrieval logs checked for anomalous patterns
- [ ] **Benchmark regression** — Security-specific benchmark queries run after each content update
- [ ] **Metadata sanitization** — EXIF and XMP fields sanitized before text pipeline ingestion
- [ ] **Incident response** — Procedure exists for quarantining and investigating suspicious content

### 8.4 Cross-Domain Security Reference

**Purpose:** Mapping multimodal-RAG security concerns to related governance in other domains.

This section provides cross-references, not duplicate content. Each domain owns its security concerns:

| Security Concern | Primary Domain | Reference |
|-----------------|----------------|-----------|
| Adversarial image attacks on retrieval | **Multimodal RAG** (this document) | SEC1, section 8.1 |
| Cross-modal input injection | **Multimodal RAG** (this document) | SEC2, section 8.2 |
| Agent memory injection | **Multi-Agent** | multi-agent-methods, Title 4 (Agent Security) |
| Tool poisoning defense | **Multi-Agent** | multi-agent-methods, section 4.6 |
| Supply chain integrity | **AI-Coding** | ai-coding-methods, section 5.3.6 |
| Application security patterns | **AI-Coding** | ai-coding-methods, sections 5.7-5.8 |
| MCP server vetting | **AI-Coding** | ai-coding-methods, section 5.4 |
| Content security scanning | **Constitution** | ai-governance-methods, Part 4.3 |

**When to consult other domains:**
- If the security concern involves agent behavior or tool calls -> Multi-Agent
- If the security concern involves code, dependencies, or deployment -> AI-Coding
- If the security concern involves governance document integrity -> Constitution

---

## 9 Data Governance

### 9.1 RBAC Configuration

**Purpose:** Procedures for implementing DG1 (Access Control for Multimodal Knowledge Bases).

**Applies To:** Any multimodal knowledge base serving users with different access levels.

**Role-Based Access Control Schema:**

```yaml
rbac_config:
  roles:
    - name: "viewer"
      description: "Can query and view public content"
      permissions:
        - "query:public"
        - "view:public_images"

    - name: "contributor"
      description: "Can view all content and add new content"
      inherits: "viewer"
      permissions:
        - "query:internal"
        - "view:internal_images"
        - "ingest:content"

    - name: "admin"
      description: "Full access including restricted content and configuration"
      inherits: "contributor"
      permissions:
        - "query:restricted"
        - "view:restricted_images"
        - "manage:roles"
        - "manage:index"
        - "audit:access_logs"

  content_classification:
    - level: "public"
      description: "Available to all authenticated users"
    - level: "internal"
      description: "Available to contributors and admins"
    - level: "restricted"
      description: "Available to admins and specifically authorized users"
```

**Enforcement Points:**

| Layer | Enforcement Action |
|-------|-------------------|
| Query processing | Check user role before executing query |
| Retrieval | Filter results to only include content the user can access |
| Response generation | Verify all images in response are accessible to user |
| Audit logging | Record user, query, and returned content for compliance |

### 9.2 Encryption and Transit Security

**Purpose:** Ensuring visual content is protected at rest and in transit.

**Requirements:**

| State | Minimum Standard | Implementation |
|-------|-----------------|----------------|
| At rest (storage) | AES-256 encryption | Encrypt knowledge base files and index |
| In transit (API) | TLS 1.2+ | HTTPS for all API endpoints |
| In transit (internal) | TLS 1.2+ or mTLS | Encrypted communication between services |
| Embeddings at rest | AES-256 encryption | Embeddings can reconstruct source content |

**Note:** Embeddings deserve the same protection as source content. Research has demonstrated that embeddings can be inverted to reconstruct original text (arxiv 2305.03010), making unprotected embeddings a data leakage vector.

### 9.3 Audit Trail Schema

**Purpose:** Audit logging requirements for access compliance.

```yaml
audit_log_entry:
  timestamp: "2026-02-15T10:30:00Z"
  user_id: "user-456"
  user_role: "contributor"
  action: "query"
  query_text: "How do I process a refund?"
  results_returned:
    - content_id: "doc-123-chunk-5"
      classification: "internal"
      content_type: "text"
    - content_id: "img-456"
      classification: "internal"
      content_type: "image"
  access_decision: "allowed"
  response_delivered: true
```

**Retention Requirements:**
- Audit logs retained for minimum 90 days (configurable per organizational policy)
- Access logs for restricted content retained for minimum 1 year
- Audit logs must be append-only (no modification or deletion)

### 9.4 Data Lineage Tracking

**Purpose:** Procedures for implementing DG2 (Data Lineage and Provenance).

**Lineage Record Schema:**

```yaml
lineage_record:
  content_id: "img-789"
  content_type: "image"

  origin:
    source: "front-desk-procedures-v3.docx"
    page: 12
    extracted_by: "document-processor-v2.1"
    extracted_at: "2026-01-20T08:00:00Z"
    original_hash: "sha256:abc123..."

  transformations:
    - step: 1
      action: "resize"
      from: "3000x2000"
      to: "1500x1000"
      tool: "image-processor-v1.2"
      timestamp: "2026-01-20T08:01:00Z"
    - step: 2
      action: "embed"
      model: "ColPali-v1.3"
      dimensions: 128
      timestamp: "2026-01-20T08:02:00Z"

  current:
    hash: "sha256:def456..."
    index_version: "idx-v4.2"
    last_verified: "2026-02-01T00:00:00Z"
```

**Lineage Verification:**
- On ingestion: Record full origin metadata
- On transformation: Log each processing step
- On query: Include provenance metadata in response citations
- On audit: Verify lineage chain is complete (no gaps)

---

## 10 Operational Management

### 10.1 Vector Index Versioning

**Purpose:** Procedures for implementing O1 (Index Version Management).

**Applies To:** Any system that maintains vector indices for multimodal retrieval.

**Version Identifier Format:**

```
idx-v{major}.{minor}_{content_hash}_{model_hash}_{timestamp}

Example: idx-v4.2_a1b2c3_d4e5f6_20260215
```

| Component | What It Tracks |
|-----------|----------------|
| `major.minor` | Semantic version of the index configuration |
| `content_hash` | Hash of content snapshot (first 6 chars) |
| `model_hash` | Hash of embedding model identifier (first 6 chars) |
| `timestamp` | Build date (YYYYMMDD) |

**Deployment Workflow:**

```
1. BUILD new index version
   - Record: model version, content snapshot, configuration parameters
   - Generate version identifier

2. TEST against benchmark suite (section 6.1)
   - Run all benchmark queries
   - Compare metrics against current production baseline
   - Document any metric changes (improvements and regressions)

3. STAGE for validation
   - Deploy to staging environment
   - Run spot-check queries from production traffic sample
   - Verify no unexpected behavior

4. PROMOTE to production
   - Keep previous version as rollback target
   - Switch traffic to new index
   - Monitor for 24 hours

5. ARCHIVE previous version
   - Retain for minimum 7 days after promotion
   - Compress and move to cold storage after retention period
```

### 10.2 Embedding Model Lifecycle

**Purpose:** Managing embedding model transitions without service disruption.

**Model Change Process:**

```
1. EVALUATE new model:
   - Run benchmark suite with new model (section 6.1)
   - Compare against current model on all six metrics
   - Document improvements and regressions

2. PARALLEL embedding generation:
   - Generate embeddings for entire corpus with new model
   - Keep old embeddings intact
   - Compare retrieval results side-by-side for sample queries

3. CUTOVER decision:
   - Require: No metric regression > 5% on any single metric
   - Require: Net improvement across majority of metrics
   - Document decision rationale

4. EXECUTE transition:
   - Build new index with new model embeddings
   - Follow deployment workflow (section 10.1)
   - Update model identifier in index version

5. RETAIN old model artifacts:
   - Keep old embeddings for rollback capability
   - Document model version in index lineage
```

### 10.3 Prompt Template Versioning

**Purpose:** Tracking changes to prompts used in the RAG pipeline.

**What to Version:**
- System prompts for response generation
- Query expansion prompts
- Intent classification prompts
- Verification prompts (section 5.1)

**Version Control Requirements:**
- All prompt templates stored in version control (git)
- Changes to prompts require evaluation against benchmark suite
- Prompt version recorded in response metadata for debugging
- Rollback capability: previous prompt versions retained

### 10.4 Cost Monitoring

**Purpose:** Tracking operational costs for multimodal RAG systems.

**Cost Categories:**

| Category | What to Track | Alert Threshold |
|----------|---------------|-----------------|
| **Embedding generation** | Cost per 1K embeddings; monthly total | > 2x baseline |
| **Vector storage** | Storage cost per GB; growth rate | > 1.5x baseline monthly growth |
| **Query inference** | Cost per query; p95 cost | > 3x average cost |
| **Image storage** | Storage cost for source images | > 1.5x baseline |
| **Model hosting** | Compute cost for embedding/reranking models | > 1.5x baseline |

**Monthly Cost Review:**
- Compare against previous month and 3-month rolling average
- Investigate any category exceeding alert threshold
- Forecast next month based on growth trends
- Identify optimization opportunities (compression, caching, batching)

### 10.5 Observability Dashboard

**Purpose:** Procedures for implementing O2 (Operational Observability).

**Key Metrics to Display:**

| Metric | Display | Alert Rule |
|--------|---------|------------|
| Query latency (p50, p95, p99) | Time series chart | p95 > 500ms |
| Retrieval error rate | Percentage gauge | > 1% over 1-hour window |
| Index freshness | Time since last update | > 24 hours |
| Embedding generation throughput | Items/minute gauge | < 50% of baseline |
| Active queries | Real-time counter | > 2x normal peak |
| Faithfulness score (rolling) | Trend line | Drops > 10% from baseline |

**Dashboard Tiers:**

| Tier | Audience | Refresh Rate | Content |
|------|----------|-------------|---------|
| **Operational** | Engineers on-call | Real-time (30s) | Latency, errors, throughput |
| **Quality** | Product/ML team | Hourly | Faithfulness, MRR, drift |
| **Executive** | Leadership | Daily/weekly | Cost, query volume, SLA compliance |

---

## 11 Agentic Retrieval Patterns

### 11.1 Adaptive Retrieval Loop Design

**Purpose:** Procedures for implementing AG1 (Adaptive Retrieval Strategy). Defines the control loop architecture for agent-driven retrieval with dynamic modality routing.

**Applies To:** Multimodal RAG systems where query complexity varies and multiple retrieval indexes or modalities are available.

**Adaptive Retrieval Loop:**

```
Input: Query Q, Available indexes I[], Max iterations N (default: 3)
State: Retrieved results R[], Iteration count k=0, Strategy S="default"

1. ANALYZE query Q:
   - Complexity signal: word count, entity count, modality references
   - Modality hints: "show me" → visual, "explain" → text, "compare" → multi-source
   - Decomposition needed? (see §11.2)

2. SELECT initial strategy S based on analysis:
   | Complexity | Strategy | Description |
   |------------|----------|-------------|
   | Simple (single intent, single modality) | single-pass | Top-K from best index |
   | Moderate (single intent, multi-modal) | parallel-search | Query multiple indexes, merge |
   | Complex (multi-intent) | decompose-and-merge | Split query, retrieve per sub-query |
   | Exploratory (vague query) | iterative-refinement | Retrieve, evaluate, refine query |

3. ROUTE to modality-appropriate index(es):
   | Query Signal | Primary Index | Secondary Index |
   |-------------|---------------|-----------------|
   | Visual content requested | Image embedding index | Document-as-image index (A4) |
   | Structured data referenced | Knowledge graph (A5) | Text index |
   | Layout-rich documents | Document-as-image index | Text index |
   | General information | Text index | Image index |
   | Relationship query | Knowledge graph | Text index |

4. EXECUTE retrieval with selected strategy
5. EVALUATE sufficiency (see §11.3)
6. IF sufficient OR k >= N: proceed to generation
   ELSE: adjust strategy and GOTO step 2 with k++
```

**Dynamic Modality Routing Decision Tree:**

```
Query Q arrives
├── Contains visual reference ("show", "image", "diagram", "screenshot")?
│   ├── YES → Route to image/document-as-image index
│   │         Also query text index for supporting context
│   └── NO → Continue
├── References structured relationships ("related to", "depends on", "connected")?
│   ├── YES → Route to knowledge graph
│   │         Also query text index for detail
│   └── NO → Continue
├── References layout-dependent content ("table", "form", "infographic")?
│   ├── YES → Route to document-as-image index (ColPali/ColQwen2)
│   └── NO → Continue
└── Default → Route to text index
    Also query image index if multimodal content exists
```

**Termination Criteria:**
- Retrieval sufficiency threshold met (see §11.3)
- Maximum iteration count reached
- Timeout exceeded (configurable, default: 10s for interactive, 60s for batch)
- No improvement between iterations (relevance scores plateaued)

### 11.2 Query Decomposition Procedures

**Purpose:** Procedures for implementing AG2 (Query Decomposition). Defines patterns for splitting compound multimodal queries into modality-aware sub-queries.

**Applies To:** Queries that contain multiple intents, reference multiple modalities, or require multi-step information synthesis.

**Decomposition Decision:**

```
Input: Query Q

1. COUNT intents in Q:
   - Information need count (distinct questions embedded in Q)
   - Modality reference count (text, image, table, diagram mentions)

2. DECIDE:
   | Intent Count | Modality Count | Action |
   |-------------|----------------|--------|
   | 1 | 1 | No decomposition needed |
   | 1 | 2+ | Modality-parallel decomposition |
   | 2+ | 1 | Intent-serial decomposition |
   | 2+ | 2+ | Full decomposition (intent × modality) |
```

**Decomposition Patterns:**

| Pattern | When to Use | Example |
|---------|------------|---------|
| **Modality-parallel** | Single intent needs information from multiple modalities | "How does Component X work?" → Sub-Q1: "Component X text description" (text index) + Sub-Q2: "Component X diagram" (image index) |
| **Intent-serial** | Multiple questions that may depend on each other | "What failed in yesterday's deployment and how do we fix it?" → Sub-Q1: "deployment failure yesterday" → Sub-Q2: "fix for [result of Q1]" |
| **Full decomposition** | Multiple intents across modalities | "Show me the architecture diagram for Service X and list its failure modes from the incident report" → Sub-Q1: "Service X architecture diagram" (image) + Sub-Q2: "Service X failure modes incident report" (text) |

**Sub-Query Generation Rules:**
1. Each sub-query must be self-contained (understandable without the parent query)
2. Add context from parent query when splitting loses important constraints
3. Preserve modality hints in sub-queries (don't strip "show me" from visual sub-queries)
4. Tag each sub-query with its target modality for routing

**Result Recombination:**

```
Input: Sub-query results SR[], Original query Q

1. FOR each sub-query result sr in SR[]:
   - Tag with source sub-query ID and modality
   - Preserve relevance score from retrieval

2. CHECK for conflicts between sub-query results
   - If visual content contradicts text content → flag per V1
   - If multiple sub-queries return overlapping content → deduplicate

3. SYNTHESIZE unified response:
   - Order by original query structure (not retrieval order)
   - Weave multi-modal results together per P1 (inline integration)
   - Attribute each claim to its sub-query source per CT1
```

### 11.3 Retrieval Sufficiency Evaluation

**Purpose:** Procedures for implementing AG3 (Retrieval Sufficiency Evaluation). Defines how the agent evaluates whether retrieved results are adequate for faithful generation.

**Applies To:** Any agentic retrieval system that iterates on retrieval results.

**Sufficiency Assessment Framework:**

```
Input: Query Q, Retrieved results R[], Quality thresholds T

1. COMPUTE coverage score:
   - Extract intents from Q (or use sub-queries from §11.2)
   - For each intent, check if at least one result in R[] addresses it
   - coverage = intents_covered / total_intents

2. COMPUTE relevance score:
   - Mean relevance score of top-K results
   - Weighted by position (top results weighted more)

3. COMPUTE confidence:
   - confidence = coverage * 0.5 + mean_relevance * 0.3 + source_diversity * 0.2
   - source_diversity = unique_sources / total_results

4. DECIDE:
   | Confidence | Coverage | Action |
   |-----------|----------|--------|
   | ≥ 0.7 | ≥ 0.8 | PROCEED to generation |
   | ≥ 0.5 | ≥ 0.6 | PROCEED with gap notes |
   | < 0.5 | any | RE-RETRIEVE with adjusted params |
   | any | < 0.6 | RE-RETRIEVE with broader query |
```

**Re-Retrieval Adjustments:**

| Situation | Adjustment |
|-----------|------------|
| Low relevance, adequate coverage | Increase top-K, apply cross-encoder reranking |
| High relevance, low coverage | Broaden query terms, add synonyms, try alternate modality |
| Low both | Decompose query (§11.2) if not already decomposed |
| Previous iteration showed no improvement | Switch retrieval strategy (e.g., vector → graph) |

**Gap Reporting:**
When proceeding with incomplete coverage, explicitly note gaps:
```
[Response based on retrieved content]

---
Note: The following aspects of your query could not be fully addressed
from available sources:
- [Uncovered intent 1]: No matching content found in [searched indexes]
- [Uncovered intent 2]: Partial match found but confidence is low
```

### 11.4 Agent Coordination for Knowledge Synthesis

**Purpose:** Procedures for coordinating multiple retrieval agents when a query requires knowledge synthesis across modalities or sources.

**Applies To:** Complex queries that benefit from parallel agent execution or specialized agent delegation.

**Coordination Patterns:**

| Pattern | When to Use | Architecture |
|---------|------------|--------------|
| **Parallel retrieval** | Independent sub-queries across modalities | Spawn one agent per modality; merge results |
| **Sequential handoff** | Dependent sub-queries (Q2 depends on Q1 result) | Chain agents; pass context between hops |
| **Specialist delegation** | Domain-specific sub-queries | Route to domain-expert agent (e.g., graph traversal agent for relationship queries) |

**Cross-Reference to Multi-Agent Domain:**
Agent coordination patterns here complement multi-agent orchestration principles (multi-agent-methods §1-§2). Key differences:
- Multi-agent domain covers general agent coordination (any task)
- This section covers retrieval-specific coordination (query planning, result merging, sufficiency evaluation)
- Use multi-agent §3.3 (Task Dependencies) for dependency ordering between retrieval agents

**Knowledge Synthesis Procedure:**

```
Input: Sub-query results from multiple agents, Original query Q

1. COLLECT all agent results with metadata:
   - Source agent ID, target modality, confidence score
   - Retrieved content with attribution

2. RESOLVE conflicts:
   - Apply V1 (Cross-Modal Consistency) between agent results
   - Apply V4 (Reasoning Chain Integrity) for multi-hop synthesis
   - When agents disagree, prefer the agent with higher-confidence primary source

3. SYNTHESIZE:
   - Build unified response following original query structure
   - Interleave visual and text content per P1
   - Maintain per-claim attribution per CT1
   - Note any unresolved conflicts transparently
```

### 11.5 Termination and Fallback Controls

**Purpose:** Procedures for preventing runaway retrieval loops and ensuring graceful degradation when retrieval cannot satisfy the query.

**Applies To:** All agentic retrieval systems. Implements safeguards against MR-F26 (Infinite Retrieval Loop).

**Termination Controls:**

| Control | Default Value | Configurable | Purpose |
|---------|--------------|-------------|---------|
| Max retrieval iterations | 3 | Yes | Prevent infinite loops |
| Per-iteration timeout | 5s (interactive), 30s (batch) | Yes | Bound per-step latency |
| Total timeout | 15s (interactive), 120s (batch) | Yes | Bound total response time |
| No-improvement threshold | 2 consecutive iterations | Yes | Stop when retrieval plateaus |
| Max tokens retrieved | 10,000 | Yes | Prevent context overflow |

**Fallback Escalation Ladder:**

```
1. NORMAL: Retrieval sufficient → Generate response
2. PARTIAL: Coverage gaps → Generate with gap notes (§11.3)
3. DEGRADED: Low confidence → Generate with explicit uncertainty markers
4. MINIMAL: Timeout or max iterations → Report what was found, note limitations
5. FAILURE: No relevant results → Apply F-Series (F1, F2) fallback procedures
```

**Graceful Degradation Template:**

```
[Best available response based on retrieved content]

---
Retrieval Note: This response was generated with [partial/limited] retrieval coverage.
- Retrieval iterations: [k] of [N] maximum
- Coverage: [X]% of query intents addressed
- Confidence: [score]
- Uncovered aspects: [list]
- Suggestion: [Rephrase query / Try specific sub-question / Consult [source] directly]
```

**Anti-Pattern: The Infinite Loop**
```
# BAD: No termination control
while not sufficient(results):
    results = retrieve(query)  # May never terminate

# GOOD: Bounded with fallback
for k in range(max_iterations):
    results = retrieve(query, strategy=strategies[k])
    if sufficient(results):
        break
    if no_improvement(results, previous_results):
        break
# Always proceed, even with imperfect results
generate_response(results, coverage_notes=assess_gaps(results, query))
```

---

## Appendix A: Claude-Specific Implementation

### A.1 Vision Capabilities

Claude supports inline images in conversations when:
- Images are provided as base64-encoded data or URLs
- Total image data stays within context limits
- Images are in supported formats (PNG, JPEG, GIF, WebP)

### A.2 Token Considerations

| Image Size | Approximate Tokens | Recommendation |
|------------|-------------------|----------------|
| < 500KB | ~1,000-2,000 | Preferred for inline display |
| 500KB-2MB | ~2,000-5,000 | Acceptable, monitor context usage |
| > 2MB | ~5,000+ | Resize or compress before including |

### A.3 Image Inclusion Format

**For Claude API:**
```json
{
  "role": "user",
  "content": [
    {"type": "text", "text": "How do I upgrade a guest room?"},
    {
      "type": "image",
      "source": {
        "type": "base64",
        "media_type": "image/png",
        "data": "[base64_encoded_image_data]"
      }
    }
  ]
}
```

**For retrieval integration:**
```python
def format_response_with_images(text_response, images):
    """Format response with images for Claude."""
    content = []

    # Parse text response for image placement markers
    segments = parse_image_placements(text_response)

    for segment in segments:
        if segment.type == 'text':
            content.append({"type": "text", "text": segment.content})
        elif segment.type == 'image_marker':
            image = images.get(segment.image_ref)
            if image:
                content.append({
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": image.media_type,
                        "data": image.base64_data
                    }
                })
            else:
                # Apply F-Series fallback
                content.append({
                    "type": "text",
                    "text": format_failure_note(segment.image_ref)
                })

    return content
```

### A.4 Prompt Pattern for Multimodal RAG

```
You are an assistant that answers questions using both text and images from a knowledge base.

When answering:
1. Place images at the exact step they support (P1)
2. Do not ask permission before showing images (P2)
3. Select the single best image; add others only if they provide unique value per P3
4. Use clear, accessible language (P4)
5. Ensure all images have alt text descriptions (P5)
6. Verify text descriptions match image content (V1)
7. Cite sources for factual claims (CT1)
8. If an image fails to load, provide complete text answer with failure note (F1, F2)

The following images are available for this query:
[Retrieved images with metadata]

User query: {query}
```

---

## Appendix B: Infrastructure Landscape

### B.1 Current Multimodal Embedding Solutions

| Solution | Description | Status (2026) |
|----------|-------------|---------------|
| **ColPali** | Late interaction multimodal embedding; processes document pages as images | Production-ready |
| **ColQwen2** | Similar architecture to ColPali with Qwen backbone | Production-ready |
| **LlamaIndex** | Framework with multimodal RAG support | Integration available |
| **LangChain** | Framework with image retrieval patterns | Integration available |
| **Weaviate** | Vector DB with multimodal support | Production-ready |
| **Pinecone** | Vector DB, multimodal via custom embeddings | Production-ready |

### B.2 Evaluation Criteria

When selecting infrastructure:

| Criterion | Questions to Ask |
|-----------|------------------|
| **Embedding Quality** | Does the model handle your image types? (UI screenshots, diagrams, photos) |
| **Latency** | What is p99 latency for your query volume? |
| **Scale** | How many images? How many queries/second? |
| **Integration** | Does it work with your existing stack? |
| **Cost** | Embedding generation cost, storage cost, query cost |
| **Maintenance** | Hosted vs. self-managed? Update frequency? |

### B.3 Reference Architecture Example

```
+-------------------------------------------------------------+
|                      Reference Documents                      |
|   (Markdown with embedded images following R-Series)          |
+------------------------------+------------------------------+
                               | Ingestion
                               v
+-------------------------------------------------------------+
|                     Document Processor                        |
|   - Vision-guided chunking per section 3.5                   |
|   - Generate metadata per section 2.3                        |
|   - Validate collocation per section 2.4                     |
|   - Input validation per section 8.2                         |
+------------------------------+------------------------------+
                               |
                               v
+-------------------------------------------------------------+
|                   Multimodal Embedder                         |
|   - ColPali/ColQwen2 for unified embedding                   |
|   - Text chunks -> vectors                                   |
|   - Images -> vectors (same space)                           |
+------------------------------+------------------------------+
                               |
                               v
+-------------------------------------------------------------+
|                      Vector Database                          |
|   - Store embeddings with metadata                           |
|   - Support hybrid search (vector + filter)                  |
|   - RBAC enforcement per section 9.1                         |
|   - (Weaviate, Pinecone, or similar)                         |
+------------------------------+------------------------------+
                               | Query
                               v
+-------------------------------------------------------------+
|                     Retrieval Service                         |
|   - Embed incoming query                                     |
|   - Vector search + metadata filter                          |
|   - Apply relevance scoring (section 3.3)                    |
|   - Verify cross-modal consistency (section 5.1)             |
|   - Return ranked images with context and citations          |
+------------------------------+------------------------------+
                               |
                               v
+-------------------------------------------------------------+
|                   Response Generator                          |
|   - LLM (Claude) with retrieved images                       |
|   - Apply P-Series presentation principles                   |
|   - Apply V-Series verification                              |
|   - Apply CT-Series citation                                 |
|   - Apply F-Series fallback if needed                        |
|   - Return multimodal response to user                       |
+-------------------------------------------------------------+
```

---

## Appendix C: Research References

### Verification and Hallucination Prevention

| Reference | Key Contribution | Year |
|-----------|-----------------|------|
| CoRe-MMRAG (ACL 2025) | Cross-source knowledge reconciliation for multimodal RAG; methodology for resolving conflicting information across text and image sources | 2025 |
| Vision-guided chunking (arxiv 2506.16035) | Preserving visual elements as complete units during document chunking; layout-aware chunking significantly improves retrieval accuracy | 2025 |

### Evaluation Metrics

| Reference | Key Contribution | Year |
|-----------|-----------------|------|
| RAG-Check (arxiv 2501.03995) | 6-metric evaluation framework: claim recall, context relevance, faithfulness, context utilization, noise sensitivity, hallucination rate | 2025 |
| MAVIS (arxiv 2511.12142) | Multimodal source attribution benchmark; standardized evaluation for attribution quality in multimodal RAG | 2025 |

### Citation and Attribution

| Reference | Key Contribution | Year |
|-----------|-----------------|------|
| VISA (arxiv 2412.14457) | Visual Information Spatial Attribution; bounding box-based attribution linking claims to specific image regions | 2024 |
| MAVIS (arxiv 2511.12142) | Multimodal attribution verification benchmark | 2025 |

### Security and Poisoning

| Reference | Key Contribution | Year |
|-----------|-----------------|------|
| MM-PoisonRAG (arxiv 2502.17832) | Localized and globalized multimodal poisoning attacks; demonstrates single-image attack capability | 2025 |
| Single-Image Attacks (arxiv 2504.02132) | Visual document RAG poisoning via single adversarial page insertion | 2025 |
| Embedding Inversion (arxiv 2305.03010) | Demonstrates that embeddings can be inverted to reconstruct source text; implications for embedding storage security | 2023 |

### Accessibility

| Reference | Key Contribution | Year |
|-----------|-----------------|------|
| WCAG 2.1 AA (W3C) | Web Content Accessibility Guidelines; Level AA conformance requirements for images, multimedia, and visual content | 2018 (current standard) |
| DOJ 2026 Mandate | U.S. Department of Justice digital accessibility requirements for public-facing services | 2026 |

### Agentic Retrieval and Multi-Hop Reasoning

| Reference | Key Contribution | Year |
|-----------|-----------------|------|
| MMA-RAG (HAL hal-05322313) | Multimodal Agentic RAG survey; adaptive retrieval strategies, agent-driven modality routing, self-reflective retrieval evaluation | 2025 |
| MMhops-R1 (arxiv 2512.13573) | Multi-hop multimodal reasoning benchmark; demonstrates error propagation in cross-modal reasoning chains; query decomposition with modality-aware sub-queries | 2025 |
| Ask in Any Modality (arxiv 2502.08826, ACL 2025) | Comprehensive survey of multimodal RAG covering agentic retrieval, evaluation, and emerging architectures | 2025 |
| Awesome RAG Reasoning (EMNLP 2025) | Reasoning-focused RAG advances including multi-step retrieval, chain-of-thought with retrieval, and reasoning verification | 2025 |

### Late Interaction and Document-as-Image Retrieval

| Reference | Key Contribution | Year |
|-----------|-----------------|------|
| ColPali (arxiv 2407.01449) | Late interaction retrieval treating document pages as images via VLM embeddings; outperforms complex extraction pipelines on layout-rich documents | 2024 |
| ColQwen2 (github illuin-tech/colpali) | Qwen2-VL-based late interaction model; improved multi-lingual and multi-resolution document retrieval | 2025 |
| ColEmbed V2 (arxiv 2602.03992, NVIDIA) | Top-performing late interaction model; multi-vector document representations with efficient MaxSim scoring | 2026 |

### Knowledge Graph Multimodal RAG

| Reference | Key Contribution | Year |
|-----------|-----------------|------|
| RAG-Anything (github HKUDS/RAG-Anything) | Knowledge graph construction from multimodal sources; entity and relationship extraction across text, images, and tables; graph-augmented retrieval for complex queries | 2025 |

### Industry Best Practices

| Reference | Key Contribution | Year |
|-----------|-----------------|------|
| Augment Code 12 Best Practices | Production multimodal RAG best practices: chunking, retrieval, evaluation, and operations | 2025 |
| ColPali Architecture | Late interaction mechanism for unified multimodal embedding | 2024 |

---

## Governance Integration

### Principle Mapping

This methods document implements:

| Principle | Implementation Location |
|-----------|------------------------|
| P1: Inline Image Integration | §1.1, §1.2, §2.5 |
| P2: Natural Integration | §1.1 (step 4), Appendix A.4 |
| P3: Image Selection Criteria | §1.3, §1.4 |
| P4: Readability Optimization | §1.5 |
| P5: Audience Adaptation | §1.5 |
| P5: Accessibility Compliance | §1.6 |
| R1: Image-Text Collocation | §2.1, §2.4, §2.5 |
| R2: Descriptive Context | §2.2, §2.5 |
| R3: Retrieval Metadata | §2.2, §2.3, §2.5 |
| A1: Unified Embedding Space | §3.1, §3.2 |
| A2: Relevance Scoring | §3.3 |
| A3: Vision-Guided Chunking | §3.5 |
| A4: Document-as-Image Retrieval | §3.7 |
| A5: Knowledge Graph Integration | §3.8 |
| F1: Graceful Degradation | §4.2 |
| F2: Failure Transparency | §4.1, §4.3, §4.4 |
| V1: Cross-Modal Consistency Verification | §5.1, §5.3 |
| V2: Visual Scene Graph Checking | §5.2 |
| V3: Source Fidelity | §5.1, §5.4 |
| V4: Cross-Modal Reasoning Chain Integrity | §5.5 |
| EV1: Retrieval Quality Measurement | §6.1, §6.2 |
| EV2: Answer Faithfulness Assessment | §6.1 |
| O2: Continuous Monitoring & Observability | §6.3, §6.4 |
| CT1: Fragment-Level Source Attribution | §7.1 |
| CT2: Spatial Attribution for Visual Content | §7.2 |
| CT1: Fragment-Level Source Attribution (includes completeness) | §7.3, §7.4 |
| SEC1: Multimodal Poisoning Defense | §8.1, §8.3 |
| SEC2: Cross-Modal Input Validation | §8.2 |
| DG1: Access Control for Multimodal KBs | §9.1, §9.2 |
| DG2: Data Lineage and Provenance | §9.3, §9.4 |
| O1: Index Version Management | §10.1, §10.2 |
| O2: Operational Observability | §10.4, §10.5 |
| AG1: Adaptive Retrieval Strategy | §11.1 |
| AG2: Query Decomposition | §11.2 |
| AG3: Retrieval Sufficiency Evaluation | §11.3, §11.5 |

---

## Changelog

### v2.1.1 (Current)
- **§2.5:** Content Ingestion Assistance Workflow — AI procedure for assisting users with preparing multimodal content for RAG knowledge bases (intake assessment, image analysis and text generation, document assembly, quality validation, retrieval optimization, batch processing)
- Updated Governance Integration table: added §2.5 to R1, R2, R3, P1

### v2.1.0
- Content expansion addressing 6 gap areas (MMA-RAG, MMhops-R1, ColPali/ColQwen2, RAG-Anything, ACL 2025 survey).
- **Title 11:** Agentic Retrieval Patterns (§11.1-11.5) — adaptive retrieval loops, query decomposition, sufficiency evaluation, agent coordination, termination controls
- **§3.7:** Late Interaction and Document-as-Image Retrieval (ColPali, ColQwen2, ColEmbed V2 procedures)
- **§3.8:** Graph-Based Multimodal Retrieval (knowledge graph construction, graph-augmented retrieval)
- **§5.5:** Multi-Hop Cross-Modal Reasoning Verification (chain integrity checks, hop-level error detection)
- **Appendix C:** Added research references for agentic retrieval, multi-hop reasoning, late interaction, and knowledge graph RAG
- Updated Governance Integration principle mapping table (29 → 35 principles)

### v2.0.0
- **Title 5:** Verification & Hallucination Prevention (§5.1-5.4)
- **Title 6:** Evaluation Framework (§6.1-6.4)
- **Title 7:** Citation & Attribution (§7.1-7.4)
- **Title 8:** Security for Multimodal Knowledge Bases (§8.1-8.4)
- **Title 9:** Data Governance (§9.1-9.4)
- **Title 10:** Operational Management (§10.1-10.5)
- **§1.6:** Accessibility Implementation Checklist (new section in Title 1)
- **§3.5:** Vision-Guided Chunking Procedures (new section in Title 3)
- **§3.6:** Cross-Modal Reference Linking (new section in Title 3)
- **Appendix C:** Research References (new appendix)
- Updated §1.1 verification step and §3.1 Layer 4 references
- Updated Appendix A.4 prompt pattern with V-Series and CT-Series
- Updated Appendix B.3 reference architecture with new processing stages
- Expanded Governance Integration principle mapping table (12 -> 29 principles)

### v1.0.1
- PATCH: Coherence audit remediation. (1) Removed ungrounded "30%+" threshold from Appendix A.4 prompt pattern (P3 defines qualitative test, not numeric threshold). (2) Added version to principles file cross-reference in system instruction.

### v1.0.0
- Initial release
- **Title 1:** Presentation Patterns (placement workflow, selection algorithm, readability standards)
- **Title 2:** Reference Document Structuring (templates, metadata schema, collocation checklist)
- **Title 3:** Retrieval Architecture (4-layer architecture, embedding selection, relevance scoring, chunking)
- **Title 4:** Failure Handling (classification, degradation procedure, templates, logging)
- **Appendix A:** Claude-Specific Implementation (vision capabilities, token considerations, API format)
- **Appendix B:** Infrastructure Landscape (current solutions, evaluation criteria, reference architecture)

---

*Version 2.1.1*
*Companion to: Multimodal RAG Domain Principles v2.1.0*
