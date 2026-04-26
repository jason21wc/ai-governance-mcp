---
version: "2.4.2"
status: "active"
effective_date: "2026-04-19"
domain: "multimodal-rag"
governance_level: "federal-statute"
---

# Multimodal RAG Domain Principles Framework v2.4.2
## Federal Statutes for AI Agents Retrieving and Presenting Visual Content

> **SYSTEM INSTRUCTION FOR AI AGENTS:**
> **This document represents the FEDERAL STATUTES (Domain Principles) for the Multimodal RAG jurisdiction.**
> * **Status:** Domain-specific laws derived from the Constitution (Meta-Principles). These principles govern AI agents that retrieve and present images inline with text responses.
> * **Hierarchy:** These statutes must comply with the Constitution (constitution.md). In case of conflict: **Bill of Rights (S-Series)** > **Constitution (Meta-Principles)** > **Domain Principles (This Document)** > **Methods/Tools (SOPs)**.
> * **Scope:** Retrieval and presentation of existing images alongside text responses—procedural documentation, training materials, customer support, and any context where visual reference materials enhance communication effectiveness. Also covers verification, evaluation, citation, security, data governance, and operational management of multimodal knowledge bases.
> * **Application:** Required for all AI-assisted multimodal retrieval activities, whether AI is generating responses with images or advising on reference document structure.
>
> **Action Directive:** When executing multimodal retrieval tasks, apply Constitutional principles (Meta-Principles) through the lens of these Domain Statutes, then derive appropriate Methods that satisfy both.
>
> ---
>
> **RELATIONSHIP TO CONSTITUTIONAL LAW (Meta-Principles):**
> This framework assumes the AI agent has already loaded and internalized the **constitution.md** (Constitution). The principles in this document are **derived applications** of those meta-principles to the specific domain of multimodal retrieval and presentation.
>
> **Derivation Formula:**
> `[Multimodal RAG Failure Mode] + [Evidence-Based Prevention] + [Constitutional Basis] = [Domain Principle]`
>
> **Supremacy Reminder:**
> If conflict arises: **S-Series (Safety) > Meta-Principles > Domain Principles > Implementation Methods**
>
> **Truth Source Hierarchy:**
> Constitution > Multimodal RAG Domain Principles > Multimodal RAG Methods > External References (WCAG 2.1, Mayer Multimedia Learning, CLIP/SigLIP research, RAG Triad evaluation frameworks)

---

## Scope and Non-Goals

### In Scope

This document governs AI-assisted multimodal retrieval and presentation:
- **Image retrieval** — Finding and selecting relevant images from reference materials
- **Inline presentation** — Placing images at correct positions within text responses
- **Reference document structuring** — How to organize source materials with images for optimal retrieval
- **Retrieval architecture** — Patterns for building multimodal RAG systems including vision-guided chunking
- **Graceful degradation** — Handling failures when images cannot be retrieved or displayed
- **Audience adaptation** — Adjusting text complexity and image selection based on context
- **Verification** — Cross-modal consistency checking and hallucination prevention
- **Evaluation** — Retrieval quality measurement and answer faithfulness assessment
- **Citation** — Fragment-level source attribution including spatial attribution for visual content
- **Security** — Multimodal poisoning defense and cross-modal input validation
- **Accessibility** — WCAG 2.1 AA compliance for visual content
- **Data governance** — Access control, lineage, and provenance for multimodal knowledge bases
- **Operations** — Index versioning, embedding lifecycle, and observability

### Out of Scope (Handled Elsewhere)

The following are NOT governed by this document:
- **Image generation** — Creating new images (DALL-E, Midjourney, etc.) — Future domain when reliable methods exist
- **Video retrieval** — Phase 2 consideration after static images
- **General AI safety and alignment** — Constitution S-Series (Bill of Rights)
- **Text-only RAG retrieval mechanics** — Governance Methods Title 12 (RAG Optimization Techniques)
- **Agent memory injection attacks** — Multi-agent methods (title-20-multi-agent-cfr, Title 4)
- **General application security** — AI-coding methods (title-10-ai-coding-cfr, Title 5)
- **Platform-specific API implementation** — Methods documents (title-40-multimodal-rag-cfr.md)

If a concern falls outside this scope, refer to the Constitution or appropriate organizational policies.

### Cross-Domain Dependencies

- **UI/UX domain (accessibility):** P5 (Accessibility Compliance) focuses on visual content accessibility (WCAG 2.1 AA, alt text, audio descriptions). For interactive interface accessibility, see UI/UX ACC-Series.
- **Storytelling domain (accessibility):** For narrative-level accessibility (cognitive load, cultural dimensions) in knowledge bases that include storytelling-like content, see Storytelling A3 (Accessibility by Design).
- **AI Coding domain (security):** SEC-Series covers multimodal-specific security (adversarial images, cross-modal injection). For general application security practices, see AI Coding domain.

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

**7. Cross-Modal Hallucination**
AI may describe visual content that contradicts or fabricates details not present in the retrieved image. Without cross-modal verification, generated text can claim an image shows elements it does not contain, eroding trust and causing users to act on false information.

**8. Untraceable Claims**
When AI synthesizes information from multiple retrieved images and text passages, the source of each claim becomes opaque. Without fragment-level attribution, users cannot verify which source supports which statement, undermining trust and auditability.

**9. Knowledge Base Poisoning**
Multimodal knowledge bases face unique attack surfaces: adversarial images that manipulate retrieval rankings, poisoned captions that inject false information, and cross-modal inputs designed to bypass single-modality validation. Unlike text-only RAG, attacks can exploit the gap between visual and textual understanding.

**10. Inaccessible Visual Content**
Visual content without proper accessibility accommodations excludes users with disabilities. This is both an ethical obligation and, as of the DOJ 2026 mandate, a legal requirement for many organizations.

### Why Meta-Principles Alone Are Insufficient

The Constitution (Meta-Principles) establishes universal reasoning principles. However, multimodal RAG has domain-specific failure modes requiring domain-specific governance:

| Meta-Principle | What It Says | What Multimodal RAG Needs |
|----------------|--------------|---------------------------|
| Context Engineering | "Load necessary information" | **Selection:** WHICH image best answers this query at this step? |
| Visible Reasoning & Traceability | "Articulate reasoning before output" | **Presentation:** HOW to weave images naturally into text flow? |
| Context Engineering | "Only load what's necessary" | **Threshold:** When does an additional image ADD vs. DISTRACT? |
| Failure Recovery & Resilience | "Handle failures appropriately" | **Fallback:** What specific information to provide when images fail? |
| Structural Foundations | "Establish foundations before implementation" | **Structure:** HOW to organize reference documents for multimodal retrieval? |
| Visible Reasoning & Traceability | "Make reasoning auditable" | **Citation:** HOW to attribute each claim to specific source fragments? |
| Verification & Validation | "Define what good looks like" | **Evaluation:** WHICH metrics measure multimodal retrieval quality? |
| Bias Awareness & Fairness | "Ensure access for all" | **Accessibility:** HOW to make visual content usable for all users? |

These domain principles provide the **selection criteria, presentation patterns, threshold rules, fallback procedures, structuring guidance, verification checks, evaluation metrics, citation standards, security defenses, accessibility requirements, data governance controls, and operational procedures** that make meta-principles actionable for multimodal RAG specifically.

### Evidence Base

This framework derives from analysis of multimodal retrieval research including:
- **ColPali architecture:** Late interaction mechanism for unified multimodal embedding space
- **Relevance scoring patterns:** Semantic similarity combined with content-type matching and recency signals
- **Instructional design research:** Image placement principles, information density optimization
- **Accessibility standards:** WCAG 2.1 AA requirements, alt text best practices, DOJ 2026 mandate
- **Readability research:** Plain language principles, audience adaptation patterns
- **RAG-Check (arxiv 2501.03995):** 6-metric evaluation framework for multimodal RAG
- **MM-PoisonRAG (arxiv 2502.17832):** Localized and globalized multimodal poisoning attacks
- **VISA (arxiv 2412.14457):** Visual Information Spatial Attribution with bounding boxes
- **CoRe-MMRAG (ACL 2025):** Cross-source knowledge reconciliation for multimodal RAG
- **Vision-guided chunking (arxiv 2506.16035):** Preserving visual elements as complete units during document chunking
- **MAVIS (arxiv 2511.12142):** Multimodal source attribution benchmark
- **MMA-RAG (HAL hal-05322313):** Multimodal Agentic RAG survey — adaptive retrieval, query decomposition, sufficiency evaluation
- **MMhops-R1 (arxiv 2512.13573):** Multi-hop multimodal reasoning with reinforcement learning
- **ColPali (arxiv 2407.01449):** Document retrieval with Vision Language Models — late interaction paradigm
- **ColQwen2 (github illuin-tech/colpali):** Qwen2-based late interaction retrieval model
- **ColEmbed V2 (arxiv 2602.03992):** NVIDIA late interaction model for document-as-image retrieval
- **RAG-Anything (github HKUDS/RAG-Anything):** Knowledge graph construction for multimodal RAG
- **Ask in Any Modality survey (arxiv 2502.08826, ACL 2025):** Comprehensive multimodal RAG survey

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
| **MR-F9** | Accessibility | Missing Alt Text | Images presented without alternative text for accessibility. *Subset of MR-F20; retained for backward compatibility with R2 mapping.* |
| **MR-F10** | Timing | Premature Image Display | Image shown before the concept it illustrates is introduced in text |
| **MR-F11** | Verification | Cross-Modal Contradiction | Generated text describes visual elements that contradict what the image actually shows |
| **MR-F12** | Verification | Hallucinated Visual Description | AI fabricates details about an image that are not present in the visual content |
| **MR-F13** | Verification | Source Distortion | Information from source document is materially altered during retrieval and presentation |
| **MR-F14** | Evaluation | Unmeasured Quality | No metrics track retrieval relevance, answer faithfulness, or user satisfaction over time. *Absence of measurement; compare MR-F22 which is undetected change despite measurement existing.* |
| **MR-F15** | Evaluation | Faithfulness Gap | Generated response makes claims not grounded in any retrieved source |
| **MR-F16** | Citation | Untraceable Claim | Statement in response cannot be linked to a specific source document or image region |
| **MR-F17** | Citation | Vague Visual Reference | AI references "the image" or "as shown" without specifying which image or region |
| **MR-F18** | Security | Knowledge Base Poisoning | Adversarial content inserted into knowledge base manipulates retrieval results |
| **MR-F19** | Security | Cross-Modal Injection | Malicious content in one modality (e.g., image metadata) exploits processing in another modality |
| **MR-F20** | Accessibility | Inaccessible Visual Content | Visual content lacks alt text, captions, audio descriptions, or other accessibility accommodations. *Superset of MR-F9; covers all accessibility modes, not just alt text.* |
| **MR-F21** | Data Governance | Unauthorized Visual Access | User accesses visual content they lack permission to view based on role or clearance |
| **MR-F22** | Operations | Silent Index Drift | Embedding model updates or index rebuilds change retrieval behavior without detection or rollback capability. *Change goes undetected; compare MR-F14 which is absence of any measurement.* |
| **MR-F23** | Retrieval | Retrieval-Limiting Caption | Accurate but insufficiently detailed text representation of visual content causes relevant multimodal content to be missed during retrieval. *Distinct from MR-F12 (hallucinated description): the caption is correct but lacks the specificity needed for retrieval matching.* |
| **MR-F24** | Reasoning | Cross-Modal Error Propagation | Error in one reasoning hop propagates and amplifies through subsequent hops in a multi-hop cross-modal reasoning chain. Early misidentification of a visual element causes cascading incorrect conclusions in later steps. |
| **MR-F25** | Retrieval | Overloaded Retrieval Query | Complex multimodal query conflating multiple intents or modalities is submitted as a single retrieval operation, causing poor recall because no single result satisfies all sub-intents simultaneously. |
| **MR-F26** | Agentic | Infinite Retrieval Loop | Agentic retrieval system repeatedly retrieves, evaluates as insufficient, and re-retrieves without converging on a satisfactory result set, consuming resources without producing a response. |
| **MR-F27** | Architecture | Retrieval Paradigm Mismatch | System uses text-extraction-based retrieval for documents where layout, formatting, or visual structure carries semantic meaning that text extraction destroys (e.g., infographics, complex tables, annotated screenshots). |

---

## Framework Overview: The Eleven Principle Series

This framework organizes domain principles into eleven series that address different functional aspects of multimodal RAG. This mirrors the Constitution's functional organization and groups principles by what they govern.

### The Eleven Series

1. **Presentation Principles (P-Series)**
   * **Role:** Response Optimization
   * **Function:** Governing HOW AI presents retrieved images with text—placement, selection, natural integration, accessibility. These principles ensure AI weaves images into responses effectively without interruption or permission-asking.

2. **Reference Principles (R-Series)**
   * **Role:** Source Document Structure
   * **Function:** Defining HOW to organize reference materials with images—collocation, descriptions, metadata. These principles ensure source documents are structured for optimal retrieval.

3. **Architecture Principles (A-Series)**
   * **Role:** System Design
   * **Function:** Establishing patterns for building multimodal retrieval systems—embedding approaches, relevance scoring, vision-guided chunking. These principles guide technical implementation.

4. **Fallback Principles (F-Series)**
   * **Role:** Failure Handling
   * **Function:** Defining WHAT happens when images fail—degradation behavior, diagnostic output, alternative guidance. These principles ensure failures are visible and actionable.

5. **Verification Principles (V-Series)**
   * **Role:** Hallucination Prevention
   * **Function:** Ensuring cross-modal consistency between retrieved images and generated text. These principles prevent the AI from fabricating or contradicting visual content.

6. **Evaluation Principles (EV-Series)**
   * **Role:** Quality Measurement
   * **Function:** Defining HOW to measure and monitor multimodal RAG quality—retrieval metrics, faithfulness assessment, continuous monitoring. These principles ensure systems improve over time.

7. **Citation Principles (CT-Series)**
   * **Role:** Source Attribution
   * **Function:** Ensuring every claim in a response can be traced to a specific source fragment or image region. These principles maintain trust and enable verification.

8. **Security Principles (SEC-Series)**
   * **Role:** Knowledge Base Protection
   * **Function:** Defending against multimodal-specific attacks—poisoning, cross-modal injection, adversarial inputs. These principles protect the integrity of the retrieval pipeline.

9. **Data Governance Principles (DG-Series)**
   * **Role:** Access Control and Lineage
   * **Function:** Governing WHO can access WHAT visual content, and tracking WHERE content originates. These principles ensure compliance with organizational and regulatory requirements.

10. **Operations Principles (O-Series)**
    * **Role:** System Lifecycle Management
    * **Function:** Managing index versions, embedding model transitions, and operational observability. These principles ensure multimodal RAG systems remain reliable through change.

11. **Agentic Retrieval Principles (AG-Series)**
    * **Role:** Agent-Driven Retrieval Orchestration
    * **Function:** Governing HOW AI agents adaptively plan, decompose, execute, and evaluate retrieval operations. These principles address dynamic modality routing, query decomposition for overloaded multimodal queries, and self-reflective retrieval sufficiency evaluation.

### The Thirty-Two Domain Principles

**P-Series: Presentation Principles** — *How AI presents images with text*

| Principle | Primary Failure Mode Addressed |
|-----------|-------------------------------|
| P1: Inline Image Integration | MR-F1 (Image-Text Misalignment) |
| P2: Natural Integration | MR-F2 (Permission-Asking Pattern) |
| P3: Image Selection Criteria | MR-F3 (Visual Overwhelm), MR-F7 (Tangential Selection) |
| P4: Audience Adaptation | MR-F6 (Complexity Mismatch) |
| P5: Accessibility Compliance | MR-F9 (Missing Alt Text), MR-F20 (Inaccessible Visual Content) |

**R-Series: Reference Principles** — *How to structure source documents*

| Principle | Primary Failure Mode Addressed |
|-----------|-------------------------------|
| R1: Image-Text Collocation | MR-F5 (Missing Image Context) |
| R2: Descriptive Context | MR-F9 (Missing Alt Text), MR-F23 (Retrieval-Limiting Caption) |
| R3: Retrieval Metadata | MR-F5 (Missing Image Context), MR-F7 (Tangential Selection) |

**A-Series: Architecture Principles** — *How to build the retrieval system*

| Principle | Primary Failure Mode Addressed |
|-----------|-------------------------------|
| A1: Unified Embedding Space | MR-F7 (Tangential Selection) |
| A2: Relevance Scoring | MR-F7 (Tangential Selection), MR-F8 (Redundant Information) |
| A3: Vision-Guided Chunking | MR-F1 (Image-Text Misalignment), MR-F5 (Missing Image Context) |
| A4: Document-as-Image Retrieval | MR-F27 (Retrieval Paradigm Mismatch) |
| A5: Knowledge Graph Integration | MR-F7 (Tangential Selection), MR-F16 (Untraceable Claim) |

**F-Series: Fallback Principles** — *What happens when images fail*

| Principle | Primary Failure Mode Addressed |
|-----------|-------------------------------|
| F1: Graceful Degradation | MR-F4 (Silent Retrieval Failure) |
| F2: Failure Transparency | MR-F4 (Silent Retrieval Failure) |

**V-Series: Verification Principles** — *Cross-modal consistency and hallucination prevention*

| Principle | Primary Failure Mode Addressed |
|-----------|-------------------------------|
| V1: Cross-Modal Consistency Verification | MR-F11 (Cross-Modal Contradiction) |
| V2: Visual Scene Graph Checking | MR-F12 (Hallucinated Visual Description) |
| V3: Source Fidelity | MR-F13 (Source Distortion) |
| V4: Cross-Modal Reasoning Chain Integrity | MR-F24 (Cross-Modal Error Propagation) |

**EV-Series: Evaluation Principles** — *How to measure and monitor quality*

| Principle | Primary Failure Mode Addressed |
|-----------|-------------------------------|
| EV1: Retrieval Quality Measurement | MR-F14 (Unmeasured Quality), MR-F23 (Retrieval-Limiting Caption) |
| EV2: Answer Faithfulness Assessment | MR-F15 (Faithfulness Gap) |

**CT-Series: Citation Principles** — *Source attribution and traceability*

| Principle | Primary Failure Mode Addressed |
|-----------|-------------------------------|
| CT1: Fragment-Level Source Attribution | MR-F16 (Untraceable Claim) |
| CT2: Spatial Attribution for Visual Content | MR-F17 (Vague Visual Reference) |

**SEC-Series: Security Principles** — *Knowledge base protection*

| Principle | Primary Failure Mode Addressed |
|-----------|-------------------------------|
| SEC1: Multimodal Poisoning Defense | MR-F18 (Knowledge Base Poisoning) |
| SEC2: Cross-Modal Input Validation | MR-F19 (Cross-Modal Injection) |

**DG-Series: Data Governance Principles** — *Access control and lineage*

| Principle | Primary Failure Mode Addressed |
|-----------|-------------------------------|
| DG1: Access Control for Multimodal Knowledge Bases | MR-F21 (Unauthorized Visual Access) |
| DG2: Data Lineage and Provenance | MR-F13 (Source Distortion) |

**O-Series: Operations Principles** — *System lifecycle management*

| Principle | Primary Failure Mode Addressed |
|-----------|-------------------------------|
| O1: Index Version Management | MR-F22 (Silent Index Drift) |
| O2: Continuous Monitoring & Observability | MR-F22 (Silent Index Drift), MR-F14 (Unmeasured Quality) |

**AG-Series: Agentic Retrieval Principles** — *Agent-driven retrieval orchestration*

| Principle | Primary Failure Mode Addressed |
|-----------|-------------------------------|
| AG1: Adaptive Retrieval Strategy | MR-F7 (Tangential Selection), MR-F27 (Retrieval Paradigm Mismatch) |
| AG2: Query Decomposition | MR-F25 (Overloaded Retrieval Query) |
| AG3: Retrieval Sufficiency Evaluation | MR-F26 (Infinite Retrieval Loop), MR-F15 (Faithfulness Gap) |

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

**Constitutional Basis**
Derived from `Context Engineering` and `Structured Output Enforcement`.

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

**Constitutional Basis**
Domain-native principle addressing MR-F2 (Permission-Asking Pattern). Conceptually aligned with `Interaction Mode Adaptation` (adapting to instructional context).

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

**Constitutional Basis**
Derived from `Context Engineering` and `Resource Efficiency & Waste Reduction`. Grounded in Mayer's Coherence Principle ("include only essential content directly linked to learning objectives") and Redundancy Principle ("people learn better when extraneous material is excluded").

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

### P4: Audience Adaptation

*Aliases: Readability Optimization (former P4), Audience Adaptation (former P5)*

**Definition**
Infer audience from query context and available signals. Adjust both text complexity and image selection to match audience needs. When audience is uncertain, apply the default readability case (below) and offer to adjust.

**Default Readability Case (When Audience Is Unknown)**
When audience signals are absent or ambiguous, apply these defaults:
- **Reading Level:** 9th-grade (Flesch-Kincaid reference)
- **Sentence Length:** Target 15-20 words per sentence average
- **Plain Language:** Avoid jargon unless audience requires it
- **Image-Text Harmony:** Text complexity should match image complexity—the purpose of images is to simplify, and text should support that goal

**How the AI Applies This Principle**
- **Signal Reading:** Vocabulary in query, role mentioned, context clues.
- **Bidirectional Adaptation:** Simplify for general audiences; use precision for experts.
- **Image Matching:** Technical screenshots for technical users; annotated/simplified visuals for general users.
- **Uncertainty Protocol:** When audience is unclear, use default readability case and invite calibration.

**Constitutional Basis**
Derived from `Interaction Mode Adaptation`, `Discovery Before Commitment`, and `Bias Awareness & Fairness`.

**Why This Principle Matters**
The same image presented to different audiences may need different surrounding text. A network diagram with technical annotations serves engineers; the same diagram with simplified labels serves managers. Complex text paired with instructional images creates cognitive overload—text should support the clarity that images provide, not undermine it.

**When Human Interaction Is Needed**
- When audience signals are contradictory.
- When single response must serve multiple audience segments.
- When audience expertise level is unclear and default readability feels wrong.
- When technical precision conflicts with simplicity.

**Common Pitfalls or Failure Modes**
- **The One-Size-Fits-All:** Same response regardless of audience signals.
- **The Condescending Simplification:** Oversimplifying for clearly expert audiences.
- **The Expertise Projection:** Assuming audience matches AI's knowledge level.
- **The Expert Assumption:** Writing at technical level regardless of audience.
- **The Jargon Wall:** Using terminology that excludes non-experts.
- **The Run-On Explanation:** Long sentences that lose readers before they reach the image.

---

### P5: Accessibility Compliance

**Definition**
All visual content presented in multimodal responses MUST meet WCAG 2.1 AA standards. This includes alt text for every image, sufficient color contrast in referenced diagrams, and text-based alternatives for information conveyed solely through visual means.

**How the AI Applies This Principle**
- **Alt Text Required:** Every image in a response must have descriptive alt text that conveys the essential information the image provides.
- **Audio Description Guidance:** When advising on video or animated content, recommend audio descriptions for visual-only information.
- **Color Independence:** Never rely solely on color to convey meaning in diagrams or annotations.
- **Text Alternatives:** For complex visualizations (charts, graphs, diagrams), provide a text summary of key findings alongside the image.

**Constitutional Basis**
Derived from `Bias Awareness & Fairness`. Strengthened by DOJ 2026 mandate requiring digital accessibility compliance.

**Why This Principle Matters**
Visual content without accessibility accommodations excludes users with visual impairments, cognitive disabilities, or situational limitations (e.g., poor screen, bright sunlight). Accessibility is both an ethical requirement and increasingly a legal one. WCAG 2.1 AA is the accepted standard.

**When Human Interaction Is Needed**
- When complex images require specialized alt text beyond AI capability.
- When organizational accessibility standards exceed WCAG 2.1 AA baseline.
- When trade-offs arise between image detail and alt text length.

**Common Pitfalls or Failure Modes**
- **The Decorative Assumption:** Marking informative images as decorative to skip alt text.
- **The Over-Description:** Alt text so verbose it impedes rather than aids understanding.
- **The Color-Only Signal:** "Click the green button" without identifying the button by label or position.
- **The Missing Summary:** Complex chart shown without text explanation of its key message.

**Cross-Domain References:** P5 focuses on technical accessibility for visual content (WCAG 2.1 AA, alt text). For narrative accessibility in knowledge bases that include storytelling-like content (cognitive load, cultural dimensions), see Storytelling domain A3 (Accessibility by Design). For interactive interface accessibility, see UI/UX domain ACC-Series.

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

**Constitutional Basis**
Derived from `Context Engineering` applied to document design.

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

**Constitutional Basis**
Derived from `Bias Awareness & Fairness` and `Context Engineering`.

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

**Constitutional Basis**
Derived from `Context Engineering` and `Resource Efficiency & Waste Reduction` (using proven metadata patterns).

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

**Constitutional Basis**
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
final_score = semantic_similarity * 0.6 + content_type_match * 0.25 + recency * 0.1 + step_alignment * 0.05
```
*Note: These weights are a recommended starting point, not a binding constraint. Tune weights based on domain-specific retrieval patterns. See title-40-multimodal-rag-cfr for tuning guidance.*

**How the AI Applies This Principle (When Advising on System Design)**
- **Semantic Similarity:** Core embedding distance/similarity.
- **Content-Type Match:** Does the image type match query intent? (screenshot for UI question, diagram for concept question)
- **Recency:** For rapidly-changing UIs, prefer recent images.
- **Step Alignment:** For procedural queries, match images to specific steps.

**Constitutional Basis**
Derived from `Visible Reasoning & Traceability` and `Verification & Validation`.

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

### A3: Vision-Guided Chunking

**Definition**
When chunking multimodal documents for indexing, tables, charts, diagrams, and other visual elements MUST be preserved as complete units. Chunk boundaries must respect visual element boundaries, not split them mid-element.

**How the AI Applies This Principle (When Advising on System Design)**
- **Visual Element Detection:** Use layout analysis or vision models to identify tables, charts, diagrams, and figures before chunking.
- **Boundary Respect:** Never split a table across two chunks. Never separate a diagram from its caption.
- **Context Preservation:** Include surrounding text context (title, caption, preceding paragraph) in the same chunk as the visual element.
- **Adaptive Chunk Size:** Allow larger chunks when needed to keep visual elements intact rather than enforcing rigid size limits.

**Constitutional Basis**
Domain-native principle addressing the unique chunking requirements of multimodal documents. Aligned with `Context Engineering` (maintaining contextual integrity).

**Why This Principle Matters**
Standard text-based chunking splits documents at fixed token counts, frequently breaking tables mid-row or separating diagrams from captions. This destroys the semantic relationship between visual elements and their context, making retrieval unreliable. Vision-guided chunking (arxiv 2506.16035) demonstrates that preserving visual units as complete chunks significantly improves retrieval accuracy.

**When Human Interaction Is Needed**
- When visual elements span multiple pages.
- When chunk size limits conflict with large visual elements (full-page tables).

**Common Pitfalls or Failure Modes**
- **The Blind Splitter:** Using fixed-size text chunking on documents with tables and diagrams.
- **The Orphaned Caption:** Chart appears in one chunk while its title and legend appear in another.
- **The Table Fragment:** Table rows split across chunks, losing row-column relationships.

---

### A4: Document-as-Image Retrieval

**Definition**
Systems SHOULD support a late interaction retrieval paradigm where document pages are indexed as images (not extracted text) and matched against queries using vision-language model embeddings. This preserves layout, formatting, and visual structure that text extraction destroys.

**How the AI Applies This Principle (When Advising on System Design)**
- **Paradigm Selection:** Evaluate whether documents are layout-rich (infographics, complex tables, annotated screenshots, forms) or text-heavy (articles, manuals). Layout-rich documents benefit from document-as-image retrieval; text-heavy documents can use traditional text extraction.
- **Multi-Vector Indexing:** When using late interaction models (ColPali, ColQwen2, ColEmbed V2), index each document page as a set of patch-level embeddings rather than a single vector. This preserves spatial information for fine-grained matching.
- **Hybrid Pipeline:** Maintain both text-extraction-based and image-based retrieval pipelines. Route queries to the appropriate pipeline based on document type and query characteristics.
- **Cost-Quality Tradeoff:** Document-as-image retrieval requires more storage (multi-vector per page) and compute (VLM inference). Apply to document collections where layout carries meaning; use text extraction for structurally simple documents.

**Constitutional Basis**
Domain-native principle addressing MR-F27 (Retrieval Paradigm Mismatch). Aligned with `Resource Efficiency & Waste Reduction` (choose the right tool for the document type).

**Why This Principle Matters**
Traditional RAG pipelines assume documents can be faithfully converted to text via OCR or PDF extraction. For documents where layout, spatial relationships, tables, and visual annotations carry semantic meaning, this assumption is false. ColPali (arxiv 2407.01449) demonstrated that treating document pages as images and using VLM embeddings can outperform complex extraction pipelines while being simpler to implement. The late interaction paradigm (multi-vector representations) enables fine-grained matching between query tokens and document page patches.

**When Human Interaction Is Needed**
- When deciding which document collections warrant image-based vs. text-based indexing.
- When storage and compute budgets constrain the choice of retrieval paradigm.
- When evaluating retrieval quality differences between paradigms for specific content types.

**Common Pitfalls or Failure Modes**
- **The Universal Extractor:** Applying text extraction to all documents regardless of whether layout carries meaning.
- **The Resolution Trap:** Indexing document images at too low a resolution, losing fine-grained visual details.
- **The Overkill Index:** Using document-as-image retrieval for plain text documents where it adds cost without quality benefit.

---

### A5: Knowledge Graph Integration

**Definition**
For complex knowledge bases where entities, relationships, and hierarchies span multiple documents and modalities, systems SHOULD construct and maintain a knowledge graph that links multimodal content structurally. Graph-based retrieval complements vector similarity search by enabling relationship-aware traversal.

**How the AI Applies This Principle (When Advising on System Design)**
- **Entity Extraction:** Extract entities from both text (NER) and images (visual object detection, diagram parsing) and unify them in a shared graph.
- **Relationship Mapping:** Build explicit relationships between entities across modalities (e.g., "Component X" in text → visual representation in Diagram Y → specification in Table Z).
- **Graph-Augmented Retrieval:** Use the knowledge graph to expand retrieval results: when a query matches entity A, also retrieve content about entities related to A via graph traversal.
- **Incremental Maintenance:** Update the knowledge graph incrementally as new content is added, rather than rebuilding from scratch.

**Constitutional Basis**
Domain-native principle addressing complex multimodal knowledge bases. Aligned with `Context Engineering` (maintaining relationships between content) and `Structured Output Enforcement`.

**Why This Principle Matters**
Vector similarity search finds content that looks similar to the query but cannot follow structural relationships. When a user asks about a component that spans multiple documents, diagrams, and specifications, vector search may find some relevant chunks but miss structurally related content. Knowledge graph integration (RAG-Anything) enables traversal from one piece of knowledge to related pieces across modalities, improving answer completeness for complex queries.

**When Human Interaction Is Needed**
- When defining the entity types and relationship schema for the knowledge graph.
- When deciding which document collections warrant graph construction overhead.
- When resolving entity conflicts (same name, different entities across documents).

**Common Pitfalls or Failure Modes**
- **The Flat Graph:** Building a graph without meaningful relationship types, reducing it to a glorified tag system.
- **The Stale Graph:** Graph structure diverges from underlying documents as content is updated but the graph is not.
- **The Extraction Hallucination:** NER or visual detection extracts non-existent entities, creating phantom nodes in the graph.

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

**Constitutional Basis**
Derived from `Failure Recovery & Resilience` from the Constitution.

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

**Constitutional Basis**
Derived from `Visible Reasoning & Traceability`.

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

## V-Series: Verification Principles

*Principles governing cross-modal consistency and hallucination prevention*

### V1: Cross-Modal Consistency Verification

**Definition**
Before presenting a response that combines retrieved images with generated text, the AI MUST verify that textual descriptions of visual content are consistent with what the images actually show. Any contradiction between text and image content must be resolved before the response is delivered.

**How the AI Applies This Principle**
- **Describe-Then-Verify:** After drafting text that references an image, re-examine the image to confirm the description matches.
- **Conflict Detection:** If text says "click the blue button" but the image shows a green button, flag and correct.
- **Explicit Uncertainty:** When visual details are ambiguous, state uncertainty rather than guess.
- **Cross-Source Reconciliation:** When multiple sources provide conflicting visual information, acknowledge the conflict per CoRe-MMRAG methodology.

**Constitutional Basis**
Derived from `Visible Reasoning & Traceability` (make reasoning auditable) and `Verification & Validation` (verify before committing).

**Why This Principle Matters**
Cross-modal contradictions (MR-F11) are uniquely damaging because users trust the combination of text and image more than either alone. When text contradicts an image, users may follow the incorrect modality and take wrong actions.

**When Human Interaction Is Needed**
- When image quality is too low to verify details.
- When text and image appear to conflict but the correct interpretation is unclear.

**Common Pitfalls or Failure Modes**
- **The Confident Fabrication:** Describing image details with certainty that aren't actually visible.
- **The Label Mismatch:** Text references UI elements by wrong names compared to what the image shows.
- **The Stale Description:** Text describes an older version of the UI while the image shows the current version.

---

### V2: Visual Scene Graph Checking

**Definition**
When describing what an image shows, the AI MUST verify the presence, attributes, and spatial relationships of objects before asserting them. Claims about visual content should be grounded in observable elements, not inferred or hallucinated.

**How the AI Applies This Principle**
- **Object Verification:** Before stating "the dialog box shows three options," verify that three options are actually visible.
- **Attribute Accuracy:** Before stating "the red warning icon," verify the icon is actually red and is actually a warning indicator.
- **Spatial Claims:** Before stating "the button is in the upper-right corner," verify the spatial position.
- **Absence Acknowledgment:** If an expected element is not visible in the image, say so rather than assuming it exists.

**Constitutional Basis**
Domain-native principle addressing MR-F12 (Hallucinated Visual Description). Aligned with `Visible Reasoning & Traceability`.

**Why This Principle Matters**
AI models can hallucinate visual details—describing objects, colors, text, or layouts that are not present in the image. In procedural contexts, this can lead users to search for non-existent UI elements, wasting time and eroding trust.

**When Human Interaction Is Needed**
- When image resolution is insufficient to verify specific details.
- When overlapping UI elements make spatial relationships ambiguous.

**Common Pitfalls or Failure Modes**
- **The Phantom Button:** Describing a button or menu item that doesn't exist in the screenshot.
- **The Wrong Count:** Stating "five tabs" when the image shows four.
- **The Inferred Content:** Describing text in an image based on expectation rather than readability.

---

### V3: Source Fidelity

**Definition**
Information retrieved from source documents MUST be presented faithfully. The AI must not materially alter, embellish, or omit critical details from retrieved content when incorporating it into responses.

**How the AI Applies This Principle**
- **Faithful Reproduction:** When citing source content, preserve the essential meaning.
- **No Embellishment:** Do not add claims, statistics, or details not present in the source.
- **Omission Transparency:** If summarizing and omitting details, note that the response is a summary.
- **Version Awareness:** When source documents have versions, cite the specific version used.

**Constitutional Basis**
Derived from `Visible Reasoning & Traceability`.

**Why This Principle Matters**
Source distortion (MR-F13) can range from subtle rewording that changes meaning to outright fabrication attributed to a legitimate source. In contexts where users rely on retrieved information for decision-making, source fidelity is critical for trust and correctness.

**When Human Interaction Is Needed**
- When source content is ambiguous and multiple interpretations exist.
- When summarization requires omitting details that may be important to some audiences.

**Common Pitfalls or Failure Modes**
- **The Creative Paraphrase:** Rewording source content in a way that subtly changes its meaning.
- **The Confidence Injection:** Stating source claims with more certainty than the source itself expresses.
- **The Invisible Omission:** Dropping caveats or qualifications from source material without noting the omission.

---

### V4: Cross-Modal Reasoning Chain Integrity

**Definition**
When answering queries that require multi-hop reasoning across modalities (e.g., "identify the component in Image A, find its specification in Table B, then verify against Diagram C"), the AI MUST verify the correctness of each reasoning hop independently before proceeding to the next. Error propagation controls must be applied at each modality transition.

**How the AI Applies This Principle**
- **Hop-Level Verification:** After each reasoning step that crosses a modality boundary (text→image, image→table, etc.), verify the intermediate conclusion before using it as input to the next hop.
- **Confidence Gating:** If confidence in an intermediate conclusion falls below a usable threshold, stop the chain and report partial results with explicit uncertainty markers rather than propagating a likely error.
- **Chain Provenance:** Maintain a reasoning trace that records: (1) the source modality and element for each hop, (2) the intermediate conclusion, and (3) the confidence level. This trace enables post-hoc verification and debugging.
- **Error Isolation:** When a multi-hop chain fails verification at hop N, report results up to hop N-1 as verified and clearly mark hop N onward as unverified.

**Constitutional Basis**
Extends V1 (Cross-Modal Consistency Verification) to multi-hop chains. Derived from `Visible Reasoning & Traceability` (make reasoning steps auditable) and `Verification & Validation` (verify each hop independently).

**Why This Principle Matters**
Multi-hop cross-modal reasoning is uniquely vulnerable to error amplification (MR-F24). A small misidentification in the first hop (e.g., confusing two similar components in an image) can cascade through subsequent hops, producing a final answer that appears internally consistent but is built on a faulty foundation. Research on MMhops-R1 demonstrates that even frontier models struggle with multi-hop multimodal reasoning, achieving significantly lower accuracy as hop count increases.

**When Human Interaction Is Needed**
- When multi-hop chains exceed 3 hops with declining confidence.
- When intermediate conclusions depend on ambiguous visual elements.
- When the final answer has high-stakes implications (safety, financial, medical).

**Common Pitfalls or Failure Modes**
- **The Cascade Error:** Misidentifying a component in Image A, then confidently looking up the wrong specification in Table B.
- **The Confidence Illusion:** Each individual hop has moderate confidence, but compound probability makes the chain unreliable.
- **The Missing Link:** Skipping a verification step between hops because the chain "makes sense" end-to-end.
- **The Anchored Interpretation:** First-hop interpretation anchors subsequent hops, preventing correction even when later evidence contradicts it.

---

## EV-Series: Evaluation Principles

*Principles governing HOW to measure and monitor multimodal RAG quality*

### EV1: Retrieval Quality Measurement

**Definition**
Multimodal RAG systems MUST track retrieval quality using established metrics. At minimum: multimodal MRR (Mean Reciprocal Rank), Recall@K, and content-type precision. These metrics must be measured against a curated benchmark set, not just production traffic.

**How the AI Applies This Principle (When Advising on System Design)**
- **Benchmark Construction:** Maintain a set of query-answer pairs with known relevant images for regression testing.
- **Multimodal MRR:** Extend standard MRR to account for both text relevance and image relevance in ranked results.
- **Content-Type Precision:** Measure whether the system returns the right type of visual content (screenshot vs. diagram vs. photo) for each query type.
- **Regular Measurement:** Run benchmarks after index rebuilds, model changes, and weight adjustments.

**Constitutional Basis**
Derived from `Verification & Validation`.

**Why This Principle Matters**
Without measurement, retrieval quality degradation goes undetected (MR-F14). Systems that appear to work may be returning suboptimal results that users work around rather than report.

**When Human Interaction Is Needed**
- When establishing initial benchmark queries and ground truth.
- When metrics conflict (high MRR but low content-type precision, or vice versa).

**Common Pitfalls or Failure Modes**
- **The Vanity Metric:** Tracking only total queries served, not relevance of results.
- **The Stale Benchmark:** Benchmark queries that no longer represent actual usage patterns.
- **The Missing Baseline:** No pre-change measurements to compare against.

---

### EV2: Answer Faithfulness Assessment

**Definition**
Systems MUST assess whether generated responses are faithful to retrieved sources. Every claim in the response should be traceable to a retrieved document or image. Unsupported claims indicate hallucination.

**How the AI Applies This Principle (When Advising on System Design)**
- **Claim Extraction:** Decompose generated responses into individual claims.
- **Source Grounding:** For each claim, identify which retrieved source supports it.
- **Faithfulness Score:** Calculate the ratio of supported claims to total claims per RAG-Check methodology.
- **Ungrounded Claim Detection:** Flag claims that cannot be traced to any retrieved source.

**Constitutional Basis**
Derived from `Verification & Validation` and `Visible Reasoning & Traceability`.

**Why This Principle Matters**
The faithfulness gap (MR-F15) is the primary quality risk in RAG systems. A response that reads well but contains unsupported claims is worse than a response that explicitly states limitations, because it creates false confidence.

**When Human Interaction Is Needed**
- When establishing acceptable faithfulness thresholds for different use cases.
- When ungrounded claims represent legitimate inference vs. hallucination.

**Common Pitfalls or Failure Modes**
- **The Plausible Fabrication:** Response sounds correct and is well-written, but key details aren't in any source.
- **The Blended Source:** Combining facts from different sources in a way that creates a claim neither source makes.
- **The Implicit Assumption:** Treating common knowledge as grounded without verifying it appears in retrieved sources.

---

## CT-Series: Citation Principles

*Principles governing source attribution and traceability*

### CT1: Fragment-Level Source Attribution

*Aliases: Citation Completeness (former CT3)*

**Definition**
Every factual claim in a multimodal RAG response SHOULD be attributable to a specific fragment of a retrieved source—not just the source document as a whole, but the specific passage, paragraph, or image region that supports the claim. Target: 100% attribution for all factual claims attributable to retrieved sources.

**How the AI Applies This Principle**
- **Inline Attribution:** When presenting facts from retrieved sources, indicate which source (and ideally which section) supports each claim.
- **Granular References:** "According to [Document, Section 3.2]" rather than just "According to [Document]."
- **Multi-Source Transparency:** When a response synthesizes from multiple sources, indicate which source supports which part.
- **Completeness Check:** Before delivering a response, verify that all factual claims have source backing.
- **Unsupported Claim Flagging:** If a claim cannot be sourced from retrieved content, either remove it, mark it as general knowledge, or explicitly note it as unsupported.
- **Attribution Ratio Tracking:** Monitor the ratio of attributed to unattributed claims as a system-level quality metric. Use attribution coverage as a continuous quality indicator.

**Constitutional Basis**
Derived from `Visible Reasoning & Traceability`.

**Why This Principle Matters**
Document-level attribution is insufficient for verification (MR-F16). If a response cites a 50-page manual, users cannot efficiently verify the claim. Fragment-level attribution enables rapid verification and builds trust. Incomplete citation creates a trust gradient within a single response—some claims are verifiable and others are not, but users cannot tell which is which. Full citation at fragment-level granularity enables full verification.

**When Human Interaction Is Needed**
- When response format constraints limit attribution detail.
- When multiple sources make the same claim and attribution is ambiguous.
- When response contains legitimate general knowledge that doesn't require sourcing.
- When citation density makes the response unreadable.

**Common Pitfalls or Failure Modes**
- **The Broad Citation:** Citing an entire document for a specific fact.
- **The Missing Citation:** Presenting retrieved information without any source indication.
- **The False Citation:** Attributing a claim to a source that doesn't actually contain it.
- **The Partial Attribution:** Citing sources for some claims but not others in the same response.
- **The Citation-Free Summary:** Synthesizing information from sources without any attribution.
- **The Readability Trade-Off:** Citations make the response so cluttered that comprehension suffers.

---

### CT2: Spatial Attribution for Visual Content

**Definition**
When referencing specific elements within an image, the AI SHOULD identify the spatial location of the referenced element. For annotated images or screenshots, point to specific regions rather than referencing "the image" generically.

**How the AI Applies This Principle**
- **Region Identification:** "In the top-left of the dashboard screenshot, the metrics panel shows..." rather than "The screenshot shows..."
- **Element Labeling:** Reference specific UI elements by their visible labels when available.
- **VISA-Style Attribution:** When tooling supports it, use bounding box coordinates to pinpoint referenced regions within images.
- **Multiple Element Clarity:** When referencing several parts of one image, describe the spatial relationship.

**Constitutional Basis**
Domain-native principle addressing MR-F17 (Vague Visual Reference). Based on VISA (Visual Information Spatial Attribution, arxiv 2412.14457) methodology.

**Why This Principle Matters**
Vague visual references ("as shown in the image") force users to scan the entire image to find relevant information. Spatial attribution reduces cognitive load and speeds comprehension, especially for complex screenshots or diagrams.

**When Human Interaction Is Needed**
- When images are dense and multiple regions could be relevant.
- When spatial descriptions are ambiguous due to image layout.

**Common Pitfalls or Failure Modes**
- **The Generic Reference:** "See the image above" without indicating what to look at.
- **The Wrong Region:** Directing attention to the wrong part of the image.
- **The Assumption of Familiarity:** Referencing UI elements by name without spatial context for users unfamiliar with the interface.

---

## SEC-Series: Security Principles

*Principles governing knowledge base protection against multimodal-specific attacks*

**Cross-Domain Note:** SEC-Series covers security threats unique to multimodal knowledge bases (adversarial images, cross-modal injection, poisoned embeddings). For broader security concerns:
- **Agent memory injection and tool poisoning** — See multi-agent methods (title-20-multi-agent-cfr, Title 4)
- **Application security, supply chain integrity** — See AI-coding methods (title-10-ai-coding-cfr, Title 5)

### SEC1: Multimodal Poisoning Defense

**Definition**
Multimodal knowledge bases MUST include defenses against adversarial content that manipulates retrieval rankings or injects false information. Both localized attacks (targeting specific queries) and globalized attacks (broadly disrupting retrieval) must be addressed.

**How the AI Applies This Principle (When Advising on System Design)**
- **Input Sanitization:** Validate images and their metadata before ingestion into the knowledge base.
- **Embedding Anomaly Detection:** Monitor for embedding vectors that cluster unexpectedly or diverge from expected distribution patterns.
- **Content Provenance:** Track the source and modification history of every item in the knowledge base.
- **Multi-Signal Validation:** Do not rely solely on embedding similarity for retrieval; combine with metadata, recency, and source trust signals per A2.
- **Periodic Audit:** Regularly sample knowledge base content for unexpected changes, anomalous entries, or poisoned captions.

**Constitutional Basis**
Domain-native principle addressing MR-F18 (Knowledge Base Poisoning). Informed by MM-PoisonRAG (arxiv 2502.17832) and single-image attack research (arxiv 2504.02132).

**Why This Principle Matters**
Multimodal RAG systems inherit all text-based poisoning risks plus additional attack surfaces: adversarial images optimized to manipulate retrieval rankings, poisoned captions that inject false information via image metadata, and cross-modal attacks that exploit gaps between visual and textual understanding. The MM-PoisonRAG framework demonstrates that even a single poisoned image can redirect query results.

**When Human Interaction Is Needed**
- When establishing acceptable risk thresholds for knowledge base integrity.
- When anomaly detection flags content that may be legitimate edge cases.
- When deciding on quarantine vs. removal of suspicious content.

**Common Pitfalls or Failure Modes**
- **The Trusted Source Assumption:** Assuming all content from internal sources is safe.
- **The Metadata Blind Spot:** Validating image content but not image metadata (EXIF, captions).
- **The Single-Layer Defense:** Relying on one validation method that adversaries can specifically target.

---

### SEC2: Cross-Modal Input Validation

**Definition**
All inputs to the multimodal RAG pipeline—text queries, images, metadata—MUST be validated for each modality independently AND for cross-modal consistency. Malicious content in one modality must not be able to exploit processing in another.

**How the AI Applies This Principle (When Advising on System Design)**
- **Per-Modality Validation:** Validate text inputs (length limits, character restrictions, injection patterns) and image inputs (format validation, size limits, content screening) separately.
- **Cross-Modal Consistency:** Check that image metadata matches image content (e.g., a caption describing a network diagram should not accompany an image of a login screen).
- **Pipeline Isolation:** Processing of different modalities should not allow one to influence the other's security checks.
- **Injection Prevention:** Image metadata fields (EXIF, alt text in source documents) must be sanitized before being used in text processing pipelines.

**Constitutional Basis**
Domain-native principle addressing MR-F19 (Cross-Modal Injection). Extends general input validation to the multimodal context.

**Why This Principle Matters**
Cross-modal injection (MR-F19) exploits the boundary between modalities. For example, prompt injection hidden in image metadata can influence LLM behavior if metadata is fed into the prompt without sanitization. Each modality's input validation must assume the other modality's content is untrusted.

**When Human Interaction Is Needed**
- When establishing validation rules for new content types or modalities.
- When cross-modal inconsistencies are detected that may indicate either attack or legitimate error.

**Common Pitfalls or Failure Modes**
- **The Trusted Metadata:** Feeding raw image metadata into LLM prompts without sanitization.
- **The Format-Only Check:** Validating file format but not content (e.g., valid PNG with embedded malicious text).
- **The Shared Pipeline:** Using a single processing pipeline for all modalities, allowing cross-contamination.

---

## DG-Series: Data Governance Principles

*Principles governing access control, lineage, and provenance for multimodal knowledge bases*

### DG1: Access Control for Multimodal Knowledge Bases

**Definition**
Visual content in knowledge bases MUST respect access control policies. Users should only be able to retrieve images they are authorized to view. Role-based access control (RBAC) should extend to the retrieval layer, not just the storage layer.

**How the AI Applies This Principle (When Advising on System Design)**
- **Retrieval-Layer Enforcement:** Access control must be enforced at query time, not just at storage time. A user without permission should never see restricted images in search results.
- **Role Propagation:** User roles/permissions must propagate from the authentication layer through to the retrieval and presentation layers.
- **Metadata Filtering:** Apply access control filters to metadata queries, not just vector search.
- **Audit Trail:** Log which users accessed which visual content, including query context.

**Constitutional Basis**
Domain-native principle addressing MR-F21 (Unauthorized Visual Access). Aligned with general data governance best practices.

**Why This Principle Matters**
Visual content may contain sensitive information—internal screenshots, confidential diagrams, proprietary processes. If retrieval systems do not enforce access control, a user's query could surface content they are not authorized to see.

**When Human Interaction Is Needed**
- When defining access control policies for new content categories.
- When a user requests access to restricted content and escalation is needed.

**Common Pitfalls or Failure Modes**
- **The Storage-Only Lock:** Content is access-controlled in storage but returned freely by the retrieval system.
- **The Embedding Leak:** Embeddings derived from restricted content are searchable by unauthorized users.
- **The Metadata Exposure:** Image metadata reveals restricted information even when the image itself is blocked.

---

### DG2: Data Lineage and Provenance

**Definition**
Every item in the multimodal knowledge base MUST have traceable lineage: where it came from, when it was added, who added it, and what transformations have been applied. This enables audit, debugging, and trust assessment.

**How the AI Applies This Principle (When Advising on System Design)**
- **Ingestion Tracking:** Record source, timestamp, and ingestion method for every item.
- **Transformation Log:** If images are resized, compressed, OCR-processed, or re-embedded, record each transformation.
- **Version History:** Maintain previous versions of items that are updated, enabling rollback.
- **Provenance in Responses:** When citing retrieved content, include provenance metadata (source document, date, version).

**Constitutional Basis**
Derived from `Visible Reasoning & Traceability`.

**Why This Principle Matters**
Without lineage tracking, it is impossible to determine whether retrieved content is current, whether it has been tampered with, or where errors originated. Provenance enables both trust assessment and debugging.

**When Human Interaction Is Needed**
- When establishing lineage tracking requirements for regulatory compliance.
- When lineage records indicate potential data integrity issues.

**Common Pitfalls or Failure Modes**
- **The Origin Gap:** Content in the knowledge base with no record of where it came from.
- **The Transformation Blackbox:** Images that have been processed but the processing steps are not recorded.
- **The Orphaned Update:** Updated content that no longer links to its original version.

---

## O-Series: Operations Principles

*Principles governing system lifecycle management for multimodal RAG*

### O1: Index Version Management

**Definition**
Vector index rebuilds, embedding model changes, and knowledge base updates MUST be versioned, tested, and reversible. Changes to the retrieval pipeline that affect result quality must follow a controlled deployment process.

**How the AI Applies This Principle (When Advising on System Design)**
- **Version Tagging:** Every index build should have a version identifier tied to: embedding model version, content snapshot hash, and configuration parameters.
- **Pre-Deployment Testing:** Run benchmark queries against new index before promoting to production.
- **Rollback Capability:** Maintain the previous index version so that a failed deployment can be quickly reverted.
- **Change Log:** Document what changed between index versions (new content, removed content, model changes, parameter changes).

**Constitutional Basis**
Domain-native principle addressing MR-F22 (Silent Index Drift). Aligned with `Resource Efficiency & Waste Reduction` (proven operational patterns).

**Why This Principle Matters**
Index rebuilds can silently change retrieval behavior. A model update that improves average quality may degrade results for specific query patterns. Without versioning and testing, these regressions go undetected until users report problems.

**When Human Interaction Is Needed**
- When benchmark results show mixed changes (some queries better, some worse).
- When deciding on rollback vs. hotfix for a problematic index update.

**Common Pitfalls or Failure Modes**
- **The Overwrite Deploy:** Replacing the production index without keeping the previous version.
- **The Untested Rebuild:** Promoting a new index without running benchmarks.
- **The Model Drift:** Updating the embedding model without re-running quality benchmarks.

---

### O2: Continuous Monitoring & Observability

*Aliases: Operational Observability (former O2), Continuous Quality Monitoring (former EV3)*

**Definition**
Multimodal RAG systems MUST expose both operational and quality metrics sufficient to diagnose issues, track trends, detect drift, and alert on degradation — continuously, not just at deployment time.

**How the AI Applies This Principle (When Advising on System Design)**

*Operational Metrics:*
- **Latency Tracking:** Monitor p50, p95, and p99 query latency. Alert when latency exceeds targets.
- **Error Rate Monitoring:** Track retrieval failures, embedding generation failures, and response generation failures separately.
- **Index Freshness:** Monitor time since last successful index update. Alert when content may be stale.
- **Throughput Metrics:** Track queries per second, embeddings generated per minute, and index size over time.
- **Cost Monitoring:** Track embedding generation costs, storage costs, and inference costs to detect unexpected spending.

*Quality Metrics:*
- **Drift Detection:** Compare rolling retrieval metrics against established baselines. Alert when metrics drop beyond a threshold.
- **Query Pattern Tracking:** Monitor for shifts in query types that may indicate the benchmark set needs updating.
- **A/B Comparison:** When changing models or weights, run parallel evaluation before committing changes.
- **User Signal Integration:** Track implicit quality signals (follow-up queries suggesting first answer was insufficient, explicit negative feedback).

**Constitutional Basis**
Derived from `Verification & Validation` and `Discovery Before Commitment`.

**Why This Principle Matters**
Without observability, operational problems manifest as quality degradation that is difficult to diagnose. A slow embedding endpoint, a stale index, or a spike in retrieval errors all affect the user experience but are invisible without monitoring. RAG systems degrade silently — content gets stale, query patterns shift, and model updates change retrieval behavior. Without continuous monitoring, quality erosion accumulates until users lose trust (MR-F14, MR-F22).

**When Human Interaction Is Needed**
- When setting alerting thresholds for different operational metrics.
- When investigating anomalies flagged by monitoring.
- When drift alerts fire and root cause analysis requires human judgment.
- When setting threshold values for acceptable quality ranges.

**Common Pitfalls or Failure Modes**
- **The Black Box:** System runs but no one can see what's happening inside.
- **The Overloaded Dashboard:** Too many metrics with no clear hierarchy of importance.
- **The Missing Alert:** Metrics are collected but no alerting is configured for degradation.
- **The Set-and-Forget:** Deploying without ongoing quality monitoring.
- **The Alert Fatigue:** Too many low-signal alerts that get ignored, masking real issues.
- **The Lagging Indicator:** Detecting quality problems only after user complaints, not proactively.

---

## AG-Series: Agentic Retrieval Principles

*Principles governing agent-driven retrieval orchestration for multimodal RAG*

### AG1: Adaptive Retrieval Strategy

**Definition**
Multimodal RAG systems SHOULD support agent-driven retrieval that evaluates result sufficiency and adapts strategy, depth, and modality routing dynamically. Rather than executing a fixed retrieval pipeline, the agent selects and sequences retrieval operations based on query characteristics, available modalities, and intermediate results.

**How the AI Applies This Principle**
- **Dynamic Modality Routing:** Analyze query characteristics to determine which modalities to search (text index, image index, graph store, document-as-image index). Route sub-queries to the most appropriate index rather than searching all indexes uniformly.
- **Adaptive Depth:** Start with lightweight retrieval (top-K vector search). If results are insufficient, escalate to more expensive operations (cross-encoder reranking, multi-hop graph traversal, document-as-image matching).
- **Strategy Selection:** Maintain a repertoire of retrieval strategies (single-pass, iterative refinement, decompose-and-merge, graph-augmented) and select based on query complexity signals.
- **Feedback-Driven Adjustment:** Use retrieval result quality signals (relevance scores, coverage gaps, confidence levels) to adjust strategy mid-flight rather than committing to a single approach.

**Constitutional Basis**
Derived from `Discovery Before Commitment` (adapt approach based on evidence) and `Resource Efficiency & Waste Reduction` (don't over-retrieve when simple retrieval suffices).

**Why This Principle Matters**
Fixed retrieval pipelines apply the same strategy regardless of query complexity. Simple queries waste resources on unnecessary steps; complex queries get insufficient retrieval depth. MMA-RAG research demonstrates that agentic retrieval—where an agent plans and adapts its retrieval strategy—significantly outperforms static pipelines on complex multimodal queries.

**When Human Interaction Is Needed**
- When defining the available retrieval strategy repertoire and their cost profiles.
- When setting resource budgets that constrain how aggressively the agent can escalate.
- When retrieval strategy selection logic needs tuning based on production query patterns.

**Common Pitfalls or Failure Modes**
- **The One-Size Pipeline:** Applying the same retrieval depth and strategy to all queries regardless of complexity.
- **The Greedy Escalator:** Always escalating to the most expensive retrieval strategy without trying simpler approaches first.
- **The Modality Blind Spot:** Routing all queries to text retrieval even when the answer is primarily visual.

---

### AG2: Query Decomposition

**Definition**
Complex multimodal queries that contain multiple intents, reference multiple modalities, or require information synthesis SHOULD be decomposed into modality-aware sub-queries. Each sub-query targets a specific modality and intent, and results are recombined after independent retrieval.

**How the AI Applies This Principle**
- **Intent Detection:** Identify when a query contains multiple information needs (e.g., "Show me the architecture diagram for Service X and explain its failure modes from the incident report").
- **Modality-Aware Splitting:** Decompose into sub-queries that align with available modalities: one sub-query for visual content (architecture diagram), another for text content (failure modes).
- **Sub-Query Independence:** Each sub-query should be self-contained and independently retrievable. Add context from the parent query as needed to maintain semantic completeness.
- **Result Recombination:** After retrieving results for each sub-query, synthesize a unified response that addresses the original compound query. Maintain attribution for which sub-query produced which result.

**Constitutional Basis**
Derived from `Discovery Before Commitment` (break complex problems into manageable parts) and `Structured Output Enforcement`.

**Why This Principle Matters**
Overloaded queries (MR-F25) that conflate multiple intents perform poorly as single retrieval operations because no single document fragment satisfies all sub-intents simultaneously. Decomposition enables each sub-intent to find its best match independently. MMhops-R1 research shows that decomposition with modality-aware routing substantially improves accuracy on complex multimodal questions.

**When Human Interaction Is Needed**
- When query decomposition is ambiguous (multiple valid ways to split).
- When sub-query results conflict and recombination requires judgment.
- When the user's original query intent is unclear and decomposition may lose nuance.

**Common Pitfalls or Failure Modes**
- **The Concatenation Fallacy:** Submitting a compound query as-is to a single retrieval index instead of decomposing.
- **The Over-Decomposer:** Splitting simple queries into unnecessary sub-queries, adding latency without quality benefit.
- **The Context-Free Split:** Decomposing in a way that strips necessary context from sub-queries, making them ambiguous.
- **The Lost Thread:** Failing to recombine sub-query results into a coherent unified response.

---

### AG3: Retrieval Sufficiency Evaluation

**Definition**
Agentic retrieval systems MUST evaluate whether retrieved results meet quality thresholds before proceeding to generation. The agent must determine if the retrieved context is sufficient to answer the query faithfully, and either proceed, re-retrieve with adjusted parameters, or report insufficiency.

**How the AI Applies This Principle**
- **Quality Thresholds:** Define minimum thresholds for retrieval quality: relevance score floor, minimum number of supporting sources, and coverage of query intents.
- **Coverage Assessment:** Evaluate whether retrieved results address all aspects of the query. Flag gaps where no retrieved content supports a specific sub-intent.
- **Confidence Scoring:** Compute an aggregate confidence score for the retrieved result set. Below a configured threshold, trigger re-retrieval with adjusted parameters (broader query, different index, expanded scope).
- **Termination Controls:** Set maximum retrieval iterations (default: 3) to prevent infinite loops (MR-F26). After max iterations, proceed with best available results and explicitly note coverage gaps.

**Constitutional Basis**
Derived from `Failure Recovery & Resilience` (handle insufficient results gracefully) and `Verification & Validation` (define what "good enough" looks like).

**Why This Principle Matters**
Without sufficiency evaluation, agentic retrieval either proceeds with inadequate context (producing unfaithful responses) or loops indefinitely trying to achieve perfection (MR-F26). MMA-RAG research demonstrates that self-reflective retrieval agents—those that evaluate their own results before generation—produce significantly more faithful and complete responses than single-pass retrieval.

**When Human Interaction Is Needed**
- When retrieval sufficiency thresholds need calibration for a specific domain.
- When the agent reaches max iterations without sufficient results and needs guidance on whether to proceed or escalate.
- When the balance between retrieval thoroughness and response latency needs adjustment.

**Common Pitfalls or Failure Modes**
- **The Infinite Loop:** Agent never deems results "sufficient" and keeps re-retrieving, consuming resources without producing a response.
- **The Uncritical Pass:** Agent always deems results sufficient regardless of quality, defeating the purpose of evaluation.
- **The Threshold Cliff:** Hard threshold causes binary behavior—slightly below threshold triggers full re-retrieval when results are nearly adequate.
- **The Latency Explosion:** Each re-retrieval iteration adds significant latency, making the system too slow for interactive use.

---

## Implementation Guidance

### When AI Retrieves and Presents Images

1. **Query Analysis** — Understand what the user is asking and what visual support would help
2. **Image Retrieval** — Select best image using A2 (Relevance Scoring)
3. **Verification** — Verify cross-modal consistency (V1, V2), source fidelity (V3), and multi-hop chain integrity (V4)
4. **Placement Planning** — Determine where image belongs in response (P1)
5. **Natural Integration** — Present without permission-asking (P2)
6. **Selection Validation** — Verify unique value for additional images per P3
7. **Accessibility Check** — Ensure alt text and text alternatives per P5
8. **Text Calibration** — Match text complexity to audience (P4)
9. **Citation** — Attribute claims to specific source fragments (CT1, CT2)
10. **Failure Handling** — If retrieval fails, apply F1 and F2

### When AI Advises on Document Structure

Apply **R-Series** principles to guide reference document organization:
- Collocate images with supporting text (R1)
- Ensure all images have alt text and contextual descriptions (R2)
- Establish consistent metadata/tagging scheme (R3)

### When AI Advises on System Design

Apply **A-Series**, **AG-Series**, **SEC-Series**, **DG-Series**, and **O-Series** principles:
- Recommend unified embedding approaches (A1)
- Define multi-signal relevance scoring (A2)
- Use vision-guided chunking for multimodal documents (A3)
- Evaluate document-as-image retrieval for layout-rich content (A4)
- Integrate knowledge graphs for complex multimodal knowledge bases (A5)
- Design agentic retrieval with adaptive strategy and query decomposition (AG1, AG2, AG3)
- Implement poisoning defense and input validation (SEC1, SEC2)
- Design access control and lineage tracking (DG1, DG2)
- Plan for index versioning, observability, and continuous quality monitoring (O1, O2)
- Consider platform-specific constraints (see Methods Appendix A)

### When AI Evaluates or Monitors Quality

Apply **EV-Series** principles to establish measurement:
- Define retrieval quality benchmarks (EV1)
- Assess answer faithfulness (EV2)
- Monitor for quality drift continuously (O2)

---

## Relationship to Methods

This Domain Principles document establishes WHAT governance applies to multimodal RAG. The companion methods document establishes HOW to implement these principles.

### Available Methods Documents

| Document | Version | Coverage |
|----------|---------|----------|
| **title-40-multimodal-rag-cfr.md** | v2.1.1 | Presentation patterns, document structuring, retrieval architecture, failure handling, verification procedures, evaluation framework, citation methods, security procedures, data governance, operational management, agentic retrieval patterns |

**Methods document includes:**
- Title 1: Presentation Patterns (image placement workflows, selection algorithms, accessibility checklist)
- Title 2: Reference Document Structuring (templates, metadata schemas)
- Title 3: Retrieval Architecture (4-layer architecture, embedding selection, vision-guided chunking, cross-modal linking, late interaction retrieval, graph-based retrieval)
- Title 4: Failure Handling (degradation procedures, error classification)
- Title 5: Verification & Hallucination Prevention (cross-modal consistency, scene graph validation, conflict resolution, multi-hop verification)
- Title 6: Evaluation Framework (RAG-Check metrics, multimodal MRR, drift detection, benchmark construction)
- Title 7: Citation & Attribution (fragment-level tracking, VISA spatial attribution, citation formatting, verification checklist)
- Title 8: Security for Multimodal Knowledge Bases (poisoning taxonomy, input validation pipeline, defense assessment, cross-domain references)
- Title 9: Data Governance (RBAC configuration, encryption, audit trail schema, lineage tracking)
- Title 10: Operational Management (index versioning, embedding lifecycle, prompt template versioning, cost monitoring, observability)
- Title 11: Agentic Retrieval Patterns (adaptive retrieval loops, query decomposition, sufficiency evaluation, agent coordination, termination controls)
- Appendix A: Claude-Specific Implementation
- Appendix B: Infrastructure Landscape (current solutions, evaluation criteria)
- Appendix C: Research References

---

## Changelog

### v2.4.2 (Current)
- PATCH: Constitutional rename note (upstream change at constitution v6.0.0). Constitutional principle `meta-quality-effective-efficient-communication` renamed and rescoped to `meta-quality-effective-efficient-outputs` — generalized from communication-only to all AI output forms. Alias preserved (`meta-quality-effective-efficient-communication` resolves to new principle for backwards-compatible retrieval). **No crosswalk row added in this domain** per scope carve-out: existing multimodal-rag principles (Presentation, Citation, Evaluation series) already cover the joint-quality discipline for retrieval outputs; adding a parallel crosswalk row would duplicate without sharpening. Precedent for this changelog-only treatment: v1.0.1 entry below (phantom-citation correction — note that v1.0.1 was a citation fix, not a rename; this v2.4.2 IS a rename and adds an alias). Constitutional Basis: Single Source of Truth (alias mechanism preserves canonical retrieval), Visible Reasoning & Traceability (rename surfaced in version history).

### v2.4.1
- **Template alignment (#31).** "Research-Based" → "Evidence-Based" in derivation formula. Added Truth Source Hierarchy. Added Cross-Domain Dependencies section (UI/UX accessibility, Storytelling accessibility, AI Coding security).

### v2.4.0
- **Cross-domain references.** Added cross-domain reference to P5 Accessibility Compliance ↔ UI/UX ACC-Series, Storytelling A3, KM&PD TL1.

### v2.3.0
- **Principle consolidation: 35 → 32 principles.** Three merges reducing redundancy while preserving all guidance:
  - **MERGE:** P4 (Readability Optimization) into P5 (Audience Adaptation) → new P4: Audience Adaptation. P4's readability defaults (9th grade, 15-20 words, plain language, Image-Text Harmony) become the "default readability case" subsection within P4. P6 renumbered to P5.
  - **MERGE:** CT3 (Citation Completeness) into CT1 (Fragment-Level Source Attribution). CT3's completeness metrics (attribution ratio, coverage tracking, 100% attribution target) added to CT1.
  - **MERGE:** EV3 (Continuous Quality Monitoring) + O2 (Operational Observability) → O2: Continuous Monitoring & Observability. Combines quality metrics (drift detection, query patterns, A/B testing, user signals) with operational metrics (latency, error rates, index freshness, throughput, cost).
- **Hygiene fixes:**
  - Fixed 4 duplicate derivation citations: V1 and V4 corrected to cite `Verification & Validation` as distinct second principle; V3 and CT3 (now in CT1) deduplicated to single `Visible Reasoning & Traceability` citation.
  - A2: Added note that scoring formula weights (0.6/0.25/0.1/0.05) are a recommended starting point, not binding.
  - Crosswalk table line: "Visible Reasoning" → "Visible Reasoning & Traceability".
  - Methods version column: "v2.1.0" → "v2.1.1".
  - Footer: Version 2.3.0, Constitution v3.0.0.

### v2.2.0
- **Constitutional principle reference consolidation (Phase 5).** Updated stale principle names in meta-principle crosswalk table: Minimal Relevant Context → Context Engineering, Foundation-First Architecture → Structural Foundations, Transparent Reasoning & Traceability → Visible Reasoning & Traceability, Measurable Success Criteria → Verification & Validation, Accessibility & Inclusiveness → Bias Awareness & Fairness.

### v2.1.0
- Content expansion addressing 6 gap areas identified by 2025-2026 literature review (MMA-RAG, MMhops-R1, ColPali/ColQwen2, RAG-Anything, ACL 2025 survey).
- **One new series:** AG-Series (Agentic Retrieval) — AG1 (Adaptive Retrieval Strategy), AG2 (Query Decomposition), AG3 (Retrieval Sufficiency Evaluation)
- **Three extended series:** V4 (Cross-Modal Reasoning Chain Integrity), A4 (Document-as-Image Retrieval), A5 (Knowledge Graph Integration)
- **Four new failure modes:** MR-F24 (Cross-Modal Error Propagation), MR-F25 (Overloaded Retrieval Query), MR-F26 (Infinite Retrieval Loop), MR-F27 (Retrieval Paradigm Mismatch)
- Updated framework overview from "Ten Series" to "Eleven Series", "Twenty-Nine" to "Thirty-Five" principles
- Updated implementation guidance to include AG-Series, A4, A5 references
- Updated methods document reference to include Title 11

### v2.0.0
- MAJOR: Content expansion addressing 8 gap areas identified by 2025-2026 best practices research.
- **Six new series:** V-Series (Verification), EV-Series (Evaluation), CT-Series (Citation), SEC-Series (Security), DG-Series (Data Governance), O-Series (Operations)
- **Seventeen new principles:** P6, A3, V1-V3, EV1-EV3, CT1-CT3, SEC1-SEC2, DG1-DG2, O1-O2
- **Thirteen new failure modes:** MR-F11 through MR-F23
- Expanded scope to include verification, evaluation, citation, security, accessibility, data governance, and operations
- Updated evidence base with 2025-2026 research references
- Added cross-domain reference notes (SEC-Series → multi-agent, ai-coding)
- Updated framework overview from "Four Series" to "Ten Series"
- Updated implementation guidance to include new principle series
- Updated methods document reference to v2.0.0

### v1.0.1
- PATCH: Coherence audit remediation. (1) Fixed 2 phantom constitutional IDs: `meta-operational-graceful-degradation` → `meta-quality-failure-recovery-resilience`, `meta-governance-resource-efficiency` → `meta-operational-resource-efficiency-waste-reduction`. (2) Corrected meta-principle name "Graceful Degradation" → "Failure Recovery & Resilience" in contextual table. (3) Fixed "Constitution Title 12" → "Governance Methods Title 12 (RAG Optimization Techniques)". (4) Removed ungrounded "30%" threshold from Implementation Guidance (P3 defines qualitative test, not numeric threshold). (5) Added version to methods file cross-reference. (6) Updated methods document version reference in Relationship to Methods table.

### v1.0.0
- Initial release
- **Four series:** P-Series (Presentation), R-Series (Reference), A-Series (Architecture), F-Series (Fallback)
- **Twelve principles:** P1-P5, R1-R3, A1-A2, F1-F2
- **Ten failure modes:** MR-F1 through MR-F10
- Scope: Retrieval-only (image generation out of scope)
- Platform-agnostic principles with Claude-first methods

---

*Version 2.4.1*
*Derived from: AI Coding Domain Principles v2.3.2, Multi-Agent Domain Principles v2.1.1, Storytelling Domain Principles v1.1.2, Constitution v3.0.0*
