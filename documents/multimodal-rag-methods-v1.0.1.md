# Multimodal RAG Methods v1.0.1
## Operational Procedures for Retrieving and Presenting Visual Content

> **SYSTEM INSTRUCTION FOR AI AGENTS:**
> This methods document provides HOW-TO procedures for implementing multimodal RAG domain principles. It is subordinate to the domain principles document (multimodal-rag-domain-principles-v1.0.1.md), which establishes WHAT governance applies.

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

5. VALIDATE before sending:
   - Each image placed after its introduction?
   - No orphan images?
   - Text complexity appropriate (P4, P5)?
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
     semantic_similarity(Q, i) × 0.6 +
     content_type_match(Q, i) × 0.25 +
     recency(i) × 0.1 +
     step_alignment(Q, i) × 0.05

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

---

## 3 Retrieval Architecture

### 3.1 Four-Layer Architecture

```
┌────────────────────────────────────────────────────────────┐
│                    Layer 1: Query Processing               │
│  Intent Classification → Query Expansion → Audience Detection│
└─────────────────────────────┬──────────────────────────────┘
                              │
┌─────────────────────────────▼──────────────────────────────┐
│                  Layer 2: Multimodal Embedding              │
│  Text Embedding ←→ Unified Space ←→ Image Embedding         │
│  (ColPali, ColQwen2, or similar)                           │
└─────────────────────────────┬──────────────────────────────┘
                              │
┌─────────────────────────────▼──────────────────────────────┐
│                  Layer 3: Retrieval & Ranking               │
│  Vector Search → Metadata Filter → Relevance Scoring        │
│  (Apply A2 multi-signal scoring)                           │
└─────────────────────────────┬──────────────────────────────┘
                              │
┌─────────────────────────────▼──────────────────────────────┐
│                  Layer 4: Response Generation               │
│  Text Generation ← Image Placement ← Failure Handling       │
│  (Apply P-Series and F-Series principles)                  │
└────────────────────────────────────────────────────────────┘
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
├── Chunk 1: "## Step 1: Access Guest Profile\n[text]\n[IMAGE_REF: step1.png]"
├── Chunk 2: "## Step 2: Open Actions Menu\n[text]\n[IMAGE_REF: step2.png]"
└── Chunk 3: "## Step 3: Select Upgrade Option\n[text]\n[IMAGE_REF: step3.png]"
```

**Key principles:**
- Keep images with their text context in same chunk
- Include image metadata in chunk for filtering
- Chunk boundaries at logical breaks (steps, sections)
- Embed both text content and image for each chunk

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
       Reason: [failure_type from §4.1]
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
5. If an image fails to load, provide complete text answer with failure note (F1, F2)

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
┌─────────────────────────────────────────────────────────────┐
│                      Reference Documents                     │
│   (Markdown with embedded images following R-Series)         │
└─────────────────────────────┬───────────────────────────────┘
                              │ Ingestion
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                     Document Processor                       │
│   - Extract text chunks with image context                   │
│   - Generate metadata per §2.3                              │
│   - Validate collocation per §2.4                           │
└─────────────────────────────┬───────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   Multimodal Embedder                        │
│   - ColPali/ColQwen2 for unified embedding                  │
│   - Text chunks → vectors                                   │
│   - Images → vectors (same space)                           │
└─────────────────────────────┬───────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      Vector Database                         │
│   - Store embeddings with metadata                          │
│   - Support hybrid search (vector + filter)                 │
│   - (Weaviate, Pinecone, or similar)                        │
└─────────────────────────────┬───────────────────────────────┘
                              │ Query
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                     Retrieval Service                        │
│   - Embed incoming query                                    │
│   - Vector search + metadata filter                         │
│   - Apply relevance scoring (§3.3)                          │
│   - Return ranked images with context                       │
└─────────────────────────────┬───────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   Response Generator                         │
│   - LLM (Claude) with retrieved images                      │
│   - Apply P-Series presentation principles                  │
│   - Apply F-Series fallback if needed                       │
│   - Return multimodal response to user                      │
└─────────────────────────────────────────────────────────────┘
```

---

## Governance Integration

### Principle Mapping

This methods document implements:

| Principle | Implementation Location |
|-----------|------------------------|
| P1: Inline Image Integration | §1.1, §1.2 |
| P2: Natural Integration | §1.1 (step 4), Appendix A.4 |
| P3: Image Selection Criteria | §1.3, §1.4 |
| P4: Readability Optimization | §1.5 |
| P5: Audience Adaptation | §1.5 |
| R1: Image-Text Collocation | §2.1, §2.4 |
| R2: Descriptive Context | §2.2 |
| R3: Retrieval Metadata | §2.2, §2.3 |
| A1: Unified Embedding Space | §3.1, §3.2 |
| A2: Relevance Scoring | §3.3 |
| F1: Graceful Degradation | §4.2 |
| F2: Failure Transparency | §4.1, §4.3, §4.4 |

---

## Changelog

### v1.0.1 (Current)
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

*Version 1.0.1*
*Companion to: Multimodal RAG Domain Principles v1.0.1*
