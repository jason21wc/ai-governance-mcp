# Multimodal RAG Domain Principles Framework v1.0.1
## Federal Statutes for AI Agents Retrieving and Presenting Visual Content

> **SYSTEM INSTRUCTION FOR AI AGENTS:**
> **This document represents the FEDERAL STATUTES (Domain Principles) for the Multimodal RAG jurisdiction.**
> * **Status:** Domain-specific laws derived from the Constitution (Meta-Principles). These principles govern AI agents that retrieve and present images inline with text responses.
> * **Hierarchy:** These statutes must comply with the Constitution (ai-interaction-principles.md). In case of conflict: **Bill of Rights (S-Series)** > **Constitution (Meta-Principles)** > **Domain Principles (This Document)** > **Methods/Tools (SOPs)**.
> * **Scope:** Retrieval and presentation of existing images alongside text responses—procedural documentation, training materials, customer support, and any context where visual reference materials enhance communication effectiveness.
> * **Application:** Required for all AI-assisted multimodal retrieval activities, whether AI is generating responses with images or advising on reference document structure.
>
> **Action Directive:** When executing multimodal retrieval tasks, apply Constitutional principles (Meta-Principles) through the lens of these Domain Statutes, then derive appropriate Methods that satisfy both.
>
> ---
>
> **RELATIONSHIP TO CONSTITUTIONAL LAW (Meta-Principles):**
> This framework assumes the AI agent has already loaded and internalized the **ai-interaction-principles.md** (Constitution). The principles in this document are **derived applications** of those meta-principles to the specific domain of multimodal retrieval and presentation.
>
> **Derivation Formula:**
> `[Multimodal RAG Failure Mode] + [Research-Based Prevention] + [Constitutional Basis] = [Domain Principle]`
>
> **Supremacy Reminder:**
> If conflict arises: **S-Series (Safety) > Meta-Principles > Domain Principles > Implementation Methods**

---

## Scope and Non-Goals

### In Scope

This document governs AI-assisted multimodal retrieval and presentation:
- **Image retrieval** — Finding and selecting relevant images from reference materials
- **Inline presentation** — Placing images at correct positions within text responses
- **Reference document structuring** — How to organize source materials with images for optimal retrieval
- **Retrieval architecture** — Patterns for building multimodal RAG systems
- **Graceful degradation** — Handling failures when images cannot be retrieved or displayed
- **Audience adaptation** — Adjusting text complexity and image selection based on context

### Out of Scope (Handled Elsewhere)

The following are NOT governed by this document:
- **Image generation** — Creating new images (DALL-E, Midjourney, etc.) → Future domain when reliable methods exist
- **Video retrieval** — Phase 2 consideration after static images
- **General AI safety and alignment** — Constitution S-Series (Bill of Rights)
- **Text-only RAG retrieval mechanics** — Governance Methods Title 12 (RAG Optimization Techniques)
- **Platform-specific API implementation** — Methods documents (multimodal-rag-methods-v1.0.1.md)

If a concern falls outside this scope, refer to the Constitution or appropriate organizational policies.

---

## Domain Context: Why Multimodal RAG Requires Specific Governance

### The Unique Constraints of AI-Assisted Visual Reference Retrieval

**Multimodal RAG** is the practice of retrieving and presenting existing images alongside text responses to enhance comprehension. When AI assists with procedural documentation, training materials, or operational guidance—specific failure modes emerge that do not exist in text-only RAG:

**1. Image-Text Misalignment**
Images placed at wrong positions in instruction flows confuse rather than clarify. A screenshot showing "Step 5" placed after Step 3 instructions creates cognitive dissonance. The AI must understand both the content of images AND their precise placement requirements.

**2. Permission-Asking Anti-Pattern**
AI models trained on conversational patterns may ask "Would you like me to show you a screenshot?" before displaying relevant images. This interrupts flow and reduces the instructional effectiveness that images provide. Natural integration—presenting images as part of the response without asking—is essential.

**3. Visual Overwhelm**
Including too many images dilutes impact. Each additional image competes for attention. Without governance, AI may retrieve every tangentially-relevant image rather than selecting the most informative one.

**4. Retrieval Failure Opacity**
When images fail to load or cannot be retrieved, silent failure leaves users without the visual aid they need AND without understanding why. Graceful degradation requires explicit acknowledgment of failures with actionable information.

**5. Reference Document Chaos**
Poorly structured source documents—images without context, missing metadata, inconsistent tagging—make multimodal retrieval unreliable. The AI-facing side of the system depends on human-facing document organization.

**6. Audience Mismatch**
Technical screenshots presented to non-technical users overwhelm. Simple diagrams shown to experts waste their time. Both the text complexity and image selection must adapt to the audience asking the question.

### Why Meta-Principles Alone Are Insufficient

The Constitution (Meta-Principles) establishes universal reasoning principles. However, multimodal RAG has domain-specific failure modes requiring domain-specific governance:

| Meta-Principle | What It Says | What Multimodal RAG Needs |
|----------------|--------------|---------------------------|
| Context Engineering | "Load necessary information" | **Selection:** WHICH image best answers this query at this step? |
| Visible Reasoning | "Articulate reasoning before output" | **Presentation:** HOW to weave images naturally into text flow? |
| Minimal Relevant Context | "Only load what's necessary" | **Threshold:** When does an additional image ADD vs. DISTRACT? |
| Failure Recovery & Resilience | "Handle failures appropriately" | **Fallback:** What specific information to provide when images fail? |
| Foundation-First Architecture | "Establish foundations before implementation" | **Structure:** HOW to organize reference documents for multimodal retrieval? |

These domain principles provide the **selection criteria, presentation patterns, threshold rules, fallback procedures, and structuring guidance** that make meta-principles actionable for multimodal RAG specifically.

### Evidence Base

This framework derives from analysis of multimodal retrieval research including:
- **ColPali architecture:** Late interaction mechanism for unified multimodal embedding space
- **Relevance scoring patterns:** Semantic similarity combined with content-type matching and recency signals
- **Instructional design research:** Image placement principles, information density optimization
- **Accessibility standards:** Alt text requirements, visual communication best practices
- **Readability research:** Plain language principles, audience adaptation patterns

---

## Failure Mode Taxonomy

Multimodal RAG systems have specific failure modes that require dedicated prevention. This taxonomy enables early detection and targeted remediation.

| Code | Category | Failure Mode | Detection Heuristic |
|------|----------|--------------|---------------------|
| **MR-F1** | Placement | Image-Text Misalignment | Image appears at wrong step; screenshot shows UI state inconsistent with instructions |
| **MR-F2** | Integration | Permission-Asking Pattern | AI asks "Would you like to see..." instead of naturally presenting relevant images |
| **MR-F3** | Selection | Visual Overwhelm | More than 3 images without clear justification; images with overlapping information content |
| **MR-F4** | Failure | Silent Retrieval Failure | Image fails to display with no explanation or alternative |
| **MR-F5** | Structure | Missing Image Context | Source document has images without descriptions, alt text, or retrieval metadata |
| **MR-F6** | Audience | Complexity Mismatch | Technical screenshots shown to non-technical audience; oversimplified visuals for experts |
| **MR-F7** | Relevance | Tangential Image Selection | Image is related to topic but doesn't answer the specific query |
| **MR-F8** | Density | Redundant Visual Information | Multiple images showing the same information from different angles |
| **MR-F9** | Accessibility | Missing Alt Text | Images presented without alternative text for accessibility |
| **MR-F10** | Timing | Premature Image Display | Image shown before the concept it illustrates is introduced in text |

---

## Framework Overview: The Four Principle Series

This framework organizes domain principles into four series that address different functional aspects of multimodal RAG. This mirrors the Constitution's functional organization and groups principles by what they govern.

### The Four Series

1. **Presentation Principles (P-Series)**
   * **Role:** Response Optimization
   * **Function:** Governing HOW AI presents retrieved images with text—placement, selection, natural integration. These principles ensure AI weaves images into responses effectively without interruption or permission-asking.

2. **Reference Principles (R-Series)**
   * **Role:** Source Document Structure
   * **Function:** Defining HOW to organize reference materials with images—collocation, descriptions, metadata. These principles ensure source documents are structured for optimal retrieval.

3. **Architecture Principles (A-Series)**
   * **Role:** System Design
   * **Function:** Establishing patterns for building multimodal retrieval systems—embedding approaches, relevance scoring, retrieval pipelines. These principles guide technical implementation.

4. **Fallback Principles (F-Series)**
   * **Role:** Failure Handling
   * **Function:** Defining WHAT happens when images fail—degradation behavior, diagnostic output, alternative guidance. These principles ensure failures are visible and actionable.

### The Twelve Domain Principles

**P-Series: Presentation Principles** — *How AI presents images with text*

| Principle | Primary Failure Mode Addressed |
|-----------|-------------------------------|
| P1: Inline Image Integration | MR-F1 (Image-Text Misalignment) |
| P2: Natural Integration | MR-F2 (Permission-Asking Pattern) |
| P3: Image Selection Criteria | MR-F3 (Visual Overwhelm), MR-F7 (Tangential Selection) |
| P4: Readability Optimization | MR-F6 (Complexity Mismatch) |
| P5: Audience Adaptation | MR-F6 (Complexity Mismatch) |

**R-Series: Reference Principles** — *How to structure source documents*

| Principle | Primary Failure Mode Addressed |
|-----------|-------------------------------|
| R1: Image-Text Collocation | MR-F5 (Missing Image Context) |
| R2: Descriptive Context | MR-F9 (Missing Alt Text) |
| R3: Retrieval Metadata | MR-F5 (Missing Image Context), MR-F7 (Tangential Selection) |

**A-Series: Architecture Principles** — *How to build the retrieval system*

| Principle | Primary Failure Mode Addressed |
|-----------|-------------------------------|
| A1: Unified Embedding Space | MR-F7 (Tangential Selection) |
| A2: Relevance Scoring | MR-F7 (Tangential Selection), MR-F8 (Redundant Information) |

**F-Series: Fallback Principles** — *What happens when images fail*

| Principle | Primary Failure Mode Addressed |
|-----------|-------------------------------|
| F1: Graceful Degradation | MR-F4 (Silent Retrieval Failure) |
| F2: Failure Transparency | MR-F4 (Silent Retrieval Failure) |

---

## P-Series: Presentation Principles

*Principles governing HOW AI presents retrieved images with text*

### P1: Inline Image Integration

**Definition**
Images MUST be placed at the exact step they support, woven into the instruction flow rather than appended at the end or clustered separately. The image should appear immediately after the text that describes what the image shows.

**How the AI Applies This Principle**
- **Step Alignment:** For procedural content, place each image immediately after the instruction it illustrates.
- **Concept Introduction First:** Never show an image before the concept it illustrates is introduced in text (prevents MR-F10).
- **Flow Preservation:** Images should feel like a natural part of reading, not interruptions.

**Constitutional Derivation**
Derived from `meta-core-context-engineering` and `meta-quality-structured-output-enforcement`.

**Why This Principle Matters**
Images placed at wrong positions create cognitive dissonance. Research in instructional design consistently shows that proximity between text and related visuals improves comprehension and retention.

**When Human Interaction Is Needed**
- When image placement is ambiguous (could support multiple steps).
- When source document structure doesn't clearly indicate image-step relationships.

**Common Pitfalls or Failure Modes**
- **The Appendix Dump:** Clustering all images at the end rather than inline.
- **The Premature Visual:** Showing an image before explaining what it represents.
- **The Orphan Image:** Image appears without clear connection to surrounding text.

---

### P2: Natural Integration

**Definition**
AI MUST NOT ask permission before showing relevant images. Images should be presented as natural components of the response, integrated seamlessly without conversational interruption.

**How the AI Applies This Principle**
- **No Permission Requests:** Never ask "Would you like me to show..." or "Here's an image if you want it."
- **Seamless Flow:** Present images as inherent parts of the answer, not optional additions.
- **Declarative Framing:** "Here is the interface:" not "Would you like to see the interface?"

**Constitutional Derivation**
Domain-native principle addressing MR-F2 (Permission-Asking Pattern). Conceptually aligned with `meta-operational-interaction-mode-adaptation` (adapting to instructional context).

**Why This Principle Matters**
Permission-asking interrupts the instructional flow and reduces the "order of magnitude" effectiveness that images provide. The user asked a question; the answer includes images. No additional permission needed.

**When Human Interaction Is Needed**
- When images contain potentially sensitive content (not typical for procedural documentation).
- When bandwidth or display constraints are explicitly communicated.

**Common Pitfalls or Failure Modes**
- **The Polite Interruption:** "I found a screenshot—would you like to see it?"
- **The Optional Qualifier:** "If you'd like, I can show you..."
- **The Buried Reference:** Mentioning that an image exists rather than displaying it.

---

### P3: Image Selection Criteria (Mayer-Based)

**Definition**
Select images using Mayer's Multimedia Learning principles. Each image must pass the Coherence Test (directly supports instruction) and the Unique Value Test (adds information not conveyed by text). For multiple images, each must independently pass both tests.

**How the AI Applies This Principle**

*The Three-Test Framework (based on Mayer's Multimedia Learning Theory):*

| Test | Principle | Question |
|------|-----------|----------|
| **Coherence Test** | Coherence Principle | Does this image directly support the instruction being given? |
| **Unique Value Test** | Redundancy Principle | Does this image add information NOT already conveyed by text? |
| **Proximity Test** | Spatial Contiguity | Can this image be placed adjacent to the text it supports? |

- **Best Image First:** Identify and present the single most informative image that passes all tests.
- **Additional Images:** Each must independently pass all three tests; if images overlap in information, include only the most informative one.
- **When Uncertain, Prefer Fewer:** Cognitive overload from redundant visuals hurts comprehension more than missing visuals.
- **No Redundancy:** Avoid multiple images showing the same information from different angles (MR-F8).

**Constitutional Derivation**
Derived from `meta-operational-minimal-relevant-context` and `meta-operational-resource-efficiency-waste-reduction`. Grounded in Mayer's Coherence Principle ("include only essential content directly linked to learning objectives") and Redundancy Principle ("people learn better when extraneous material is excluded").

**Why This Principle Matters**
Each additional image competes for attention and consumes cognitive capacity. Research shows that redundant visuals create extraneous cognitive load that interferes with learning. The goal is maximum clarity with minimum visual noise.

**When Human Interaction Is Needed**
- When multiple images have comparable relevance and the best choice is unclear.
- When user explicitly requests comprehensive visual coverage.
- When Coherence and Unique Value tests produce conflicting results.

**Common Pitfalls or Failure Modes**
- **The Kitchen Sink:** Including every image that's somewhat related (fails Coherence Test).
- **The Close Enough:** Selecting a tangentially-related image because no perfect match exists.
- **The Redundant Angles:** Multiple screenshots of the same UI with minor variations (fails Unique Value Test).
- **The Overwhelming Gallery:** Adding images that pass Coherence but collectively create cognitive overload.

---

### P4: Readability Optimization

**Definition**
Default text complexity to 9th-grade reading level with 15-20 word sentences and plain language. Adjust complexity based on audience and context, but maintain clarity as the primary goal.

**How the AI Applies This Principle**
- **Sentence Length:** Target 15-20 words per sentence average.
- **Plain Language:** Avoid jargon unless audience requires it.
- **9th-Grade Default:** Assume general audience unless context indicates otherwise.
- **Image-Text Harmony:** Text complexity should match image complexity.

**Constitutional Derivation**
Derived from `meta-governance-accessibility-and-inclusiveness`.

**Why This Principle Matters**
Complex text paired with instructional images creates cognitive overload. The purpose of images is to simplify—text should support that goal, not undermine it.

**When Human Interaction Is Needed**
- When audience expertise level is unclear.
- When technical precision conflicts with simplicity.

**Common Pitfalls or Failure Modes**
- **The Expert Assumption:** Writing at technical level regardless of audience.
- **The Jargon Wall:** Using terminology that excludes non-experts.
- **The Run-On Explanation:** Long sentences that lose readers before they reach the image.

---

### P5: Audience Adaptation

**Definition**
Infer audience from query context and available signals. Adjust both text complexity and image selection to match audience needs. When uncertain, default to accessible (P4) and offer to adjust.

**How the AI Applies This Principle**
- **Signal Reading:** Vocabulary in query, role mentioned, context clues.
- **Bidirectional Adaptation:** Simplify for general audiences; use precision for experts.
- **Image Matching:** Technical screenshots for technical users; annotated/simplified visuals for general users.
- **Uncertainty Protocol:** When audience is unclear, use accessible defaults and invite calibration.

**Constitutional Derivation**
Derived from `meta-operational-interaction-mode-adaptation` and `meta-core-discovery-before-commitment`.

**Why This Principle Matters**
The same image presented to different audiences may need different surrounding text. A network diagram with technical annotations serves engineers; the same diagram with simplified labels serves managers.

**When Human Interaction Is Needed**
- When audience signals are contradictory.
- When single response must serve multiple audience segments.

**Common Pitfalls or Failure Modes**
- **The One-Size-Fits-All:** Same response regardless of audience signals.
- **The Condescending Simplification:** Oversimplifying for clearly expert audiences.
- **The Expertise Projection:** Assuming audience matches AI's knowledge level.

---

## R-Series: Reference Principles

*Principles governing HOW to structure source documents with images*

### R1: Image-Text Collocation

**Definition**
In source documents, images MUST be placed immediately adjacent to the text they support. The organizing principle is proximity—readers (and retrieval systems) should encounter image and related text together.

**How the AI Applies This Principle (When Advising on Document Structure)**
- **Adjacent Placement:** Image follows the paragraph or step it illustrates.
- **No Separation:** Avoid image galleries or appendices that separate images from context.
- **Structural Consistency:** Same collocation pattern throughout document.

**Constitutional Derivation**
Derived from `meta-core-context-engineering` applied to document design.

**Why This Principle Matters**
Retrieval systems chunk documents. If images are separated from their context, chunks containing images may lack the text needed to understand when to retrieve them.

**When Human Interaction Is Needed**
- When document format constraints prevent collocation (some PDFs, legacy systems).
- When images support multiple text sections.

**Common Pitfalls or Failure Modes**
- **The Appendix Pattern:** All images at document end.
- **The Gallery Cluster:** Images grouped by visual similarity rather than textual relevance.
- **The Reference Number:** "See Figure 7" without embedding Figure 7 nearby.

---

### R2: Descriptive Context

**Definition**
Every image MUST have alt text describing what it shows AND contextual description explaining its purpose. Alt text serves accessibility; context serves retrieval.

**How the AI Applies This Principle (When Advising on Document Structure)**
- **Alt Text (What):** Describe visual content for accessibility.
- **Context (Why):** Explain what the image demonstrates and when to use it.
- **Dual Purpose:** Alt text for screen readers and accessibility; context for retrieval relevance.

**Constitutional Derivation**
Derived from `meta-governance-accessibility-and-inclusiveness` and `meta-core-context-engineering`.

**Why This Principle Matters**
Images without descriptions are invisible to retrieval systems and inaccessible to users with visual impairments. Descriptions bridge the semantic gap between visual content and text queries.

**When Human Interaction Is Needed**
- When images are complex and descriptions are difficult.
- When balancing description length against document readability.

**Common Pitfalls or Failure Modes**
- **The File Name Alt:** "image_003.png" instead of descriptive alt text.
- **The Missing Context:** Alt text exists but no explanation of when/why to use image.
- **The Vague Description:** "Screenshot of application" instead of specific content description.

---

### R3: Retrieval Metadata

**Definition**
Images MUST have tags or metadata linking them to specific procedural steps, concepts, or use cases. This enables retrieval systems to match queries to images beyond semantic similarity alone.

**How the AI Applies This Principle (When Advising on Document Structure)**
- **Step Tags:** `step-3`, `guest-upgrade-process`
- **Concept Tags:** `rate-codes`, `room-assignment`, `billing`
- **Use Case Tags:** `troubleshooting`, `new-employee`, `advanced`

**Constitutional Derivation**
Derived from `meta-core-context-engineering` and `meta-operational-established-solutions-first` (using proven metadata patterns).

**Why This Principle Matters**
Semantic embedding alone may not distinguish between images of similar content used for different purposes. Metadata provides explicit signals that improve retrieval precision.

**When Human Interaction Is Needed**
- When establishing metadata taxonomy for a new document set.
- When existing metadata standards must be followed.

**Common Pitfalls or Failure Modes**
- **The Missing Metadata:** Images stored without any categorization.
- **The Inconsistent Taxonomy:** Different tag systems for different documents.
- **The Over-Tagging:** So many tags that signal is lost in noise.

---

## A-Series: Architecture Principles

*Principles governing HOW to build multimodal retrieval systems*

### A1: Unified Embedding Space

**Definition**
Multimodal RAG systems SHOULD use embedding models that place text and images in the same vector space, enabling direct similarity comparison between text queries and image content.

**How the AI Applies This Principle (When Advising on System Design)**
- **Multimodal Embeddings:** Prefer models like ColPali, ColQwen2, or similar that create unified representations.
- **Cross-Modal Retrieval:** System should retrieve relevant images directly from text queries.
- **Late Interaction:** Consider architectures that enable fine-grained query-document matching.

**Constitutional Derivation**
Domain-native principle addressing architectural foundations for effective multimodal retrieval.

**Why This Principle Matters**
Separate embedding spaces for text and images require translation layers that introduce error and latency. Unified spaces enable direct semantic comparison.

**When Human Interaction Is Needed**
- When evaluating embedding model options for specific use cases.
- When infrastructure constraints limit model choices.

**Common Pitfalls or Failure Modes**
- **The Translation Gap:** Separate text and image embeddings requiring brittle mapping.
- **The Text-Only Retrieval:** Using text embeddings for image retrieval via captions alone.
- **The Outdated Model:** Using embedding models that predate multimodal advances.

---

### A2: Relevance Scoring

**Definition**
Combine multiple signals to determine image relevance: semantic similarity, content-type match, recency, and step alignment. No single signal suffices.

**Recommended Scoring Formula:**
```
final_score = semantic_similarity × 0.6 + content_type_match × 0.25 + recency × 0.1 + step_alignment × 0.05
```

**How the AI Applies This Principle (When Advising on System Design)**
- **Semantic Similarity:** Core embedding distance/similarity.
- **Content-Type Match:** Does the image type match query intent? (screenshot for UI question, diagram for concept question)
- **Recency:** For rapidly-changing UIs, prefer recent images.
- **Step Alignment:** For procedural queries, match images to specific steps.

**Constitutional Derivation**
Derived from `meta-quality-visible-reasoning` and `meta-governance-measurable-success-criteria`.

**Why This Principle Matters**
Pure semantic similarity may rank tangentially-related images highly. Combining signals improves precision and reduces MR-F7 (Tangential Selection).

**When Human Interaction Is Needed**
- When calibrating weights for specific use cases.
- When adding domain-specific scoring signals.

**Common Pitfalls or Failure Modes**
- **The Single Signal:** Relying only on embedding similarity.
- **The Miscalibrated Weights:** Weights that don't reflect actual relevance patterns.
- **The Missing Recency:** Showing outdated UI screenshots for current queries.

---

## F-Series: Fallback Principles

*Principles governing WHAT happens when images fail*

### F1: Graceful Degradation

**Definition**
When image retrieval fails, provide a complete text-only response plus a note about the missing image. The response must still answer the user's question; the image absence is acknowledged but doesn't block helpfulness.

**How the AI Applies This Principle**
- **Text-First Completeness:** Answer must be fully usable without the image.
- **Explicit Acknowledgment:** Note that an image was intended but unavailable.
- **Alternative Guidance:** Provide document reference for manual lookup if possible.

**Constitutional Derivation**
Derived from `meta-quality-failure-recovery-resilience` (Failure Recovery & Resilience) from the Constitution.

**Why This Principle Matters**
Silent failure (MR-F4) leaves users without images AND without understanding why. Explicit degradation maintains trust and provides fallback options.

**When Human Interaction Is Needed**
- When image is critical and text-only response may be insufficient.
- When repeated failures suggest systemic issues requiring escalation.

**Common Pitfalls or Failure Modes**
- **The Silent Failure:** Image simply doesn't appear; user doesn't know it was expected.
- **The Blocking Failure:** "I cannot answer without the image."
- **The Incomplete Fallback:** Acknowledging failure but not providing alternative guidance.

---

### F2: Failure Transparency

**Definition**
When images fail, report the failure reason with enough specificity to enable troubleshooting. Distinguish between format issues, size limits, retrieval errors, and "image not found" scenarios.

**Failure Response Format:**
```
[Text-only response here]

---
Note: Image for Step N could not be displayed.
Reason: [format_unsupported | size_exceeded | retrieval_failed | not_found]
Reference: [document_name, page/section] for manual lookup
```

**How the AI Applies This Principle**
- **Classified Reasons:** Categorize failures into actionable types.
- **Reference Pointers:** When possible, tell users where to find the image manually.
- **Visibility:** Failure notes should be visible, not hidden in metadata.

**Constitutional Derivation**
Derived from `meta-governance-transparent-reasoning-and-traceability`.

**Why This Principle Matters**
Different failure types require different remediation. "Format unsupported" suggests source document issue; "retrieval failed" suggests system issue; "not found" suggests content gap.

**When Human Interaction Is Needed**
- When failure reasons are ambiguous.
- When escalation path for persistent failures needs definition.

**Common Pitfalls or Failure Modes**
- **The Generic Error:** "Image could not be loaded" without specificity.
- **The Hidden Diagnostic:** Failure details in logs but not in response.
- **The Missing Reference:** Failure noted but no guidance for manual lookup.

---

## Implementation Guidance

### When AI Retrieves and Presents Images

1. **Query Analysis** — Understand what the user is asking and what visual support would help
2. **Image Retrieval** — Select best image using A2 (Relevance Scoring)
3. **Placement Planning** — Determine where image belongs in response (P1)
4. **Natural Integration** — Present without permission-asking (P2)
5. **Selection Validation** — Verify unique value for additional images per P3
6. **Text Calibration** — Match text complexity to audience (P4, P5)
7. **Failure Handling** — If retrieval fails, apply F1 and F2

### When AI Advises on Document Structure

Apply **R-Series** principles to guide reference document organization:
- Collocate images with supporting text (R1)
- Ensure all images have alt text and contextual descriptions (R2)
- Establish consistent metadata/tagging scheme (R3)

### When AI Advises on System Design

Apply **A-Series** principles to guide architecture decisions:
- Recommend unified embedding approaches (A1)
- Define multi-signal relevance scoring (A2)
- Consider platform-specific constraints (see Methods Appendix A)

---

## Relationship to Methods

This Domain Principles document establishes WHAT governance applies to multimodal RAG. The companion methods document establishes HOW to implement these principles.

### Available Methods Documents

| Document | Version | Coverage |
|----------|---------|----------|
| **multimodal-rag-methods-v1.0.1.md** | v1.0.1 | Presentation patterns, document structuring, retrieval architecture, failure handling |

**Methods document includes:**
- Title 1: Presentation Patterns (image placement workflows, selection algorithms)
- Title 2: Reference Document Structuring (templates, metadata schemas)
- Title 3: Retrieval Architecture (4-layer architecture, embedding selection)
- Title 4: Failure Handling (degradation procedures, error classification)
- Appendix A: Claude-Specific Implementation
- Appendix B: Infrastructure Landscape (current solutions, evaluation criteria)

---

## Changelog

### v1.0.1 (Current)
- PATCH: Coherence audit remediation. (1) Fixed 2 phantom constitutional IDs: `meta-operational-graceful-degradation` → `meta-quality-failure-recovery-resilience`, `meta-governance-resource-efficiency` → `meta-operational-resource-efficiency-waste-reduction`. (2) Corrected meta-principle name "Graceful Degradation" → "Failure Recovery & Resilience" in contextual table. (3) Fixed "Constitution Title 12" → "Governance Methods Title 12 (RAG Optimization Techniques)". (4) Removed ungrounded "30%" threshold from Implementation Guidance (P3 defines qualitative test, not numeric threshold). (5) Added version to methods file cross-reference. (6) Updated methods document version reference in Relationship to Methods table.

### v1.0.0
- Initial release
- **Four series:** P-Series (Presentation), R-Series (Reference), A-Series (Architecture), F-Series (Fallback)
- **Twelve principles:** P1-P5, R1-R3, A1-A2, F1-F2
- **Ten failure modes:** MR-F1 through MR-F10
- Scope: Retrieval-only (image generation out of scope)
- Platform-agnostic principles with Claude-first methods

---

*Version 1.0.1*
*Derived from: AI Coding Domain Principles v2.2.1, Multi-Agent Domain Principles v2.0.0, Storytelling Domain Principles v1.0.0*
