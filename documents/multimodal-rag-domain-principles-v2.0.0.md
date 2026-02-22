# Multimodal RAG Domain Principles Framework v2.0.0
## Federal Statutes for AI Agents Retrieving and Presenting Visual Content

> **SYSTEM INSTRUCTION FOR AI AGENTS:**
> **This document represents the FEDERAL STATUTES (Domain Principles) for the Multimodal RAG jurisdiction.**
> * **Status:** Domain-specific laws derived from the Constitution (Meta-Principles). These principles govern AI agents that retrieve and present images inline with text responses.
> * **Hierarchy:** These statutes must comply with the Constitution (ai-interaction-principles.md). In case of conflict: **Bill of Rights (S-Series)** > **Constitution (Meta-Principles)** > **Domain Principles (This Document)** > **Methods/Tools (SOPs)**.
> * **Scope:** Retrieval and presentation of existing images alongside text responses—procedural documentation, training materials, customer support, and any context where visual reference materials enhance communication effectiveness. Also covers verification, evaluation, citation, security, data governance, and operational management of multimodal knowledge bases.
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
- **Agent memory injection attacks** — Multi-agent methods (multi-agent-methods, Title 4)
- **General application security** — AI-coding methods (ai-coding-methods, Title 5)
- **Platform-specific API implementation** — Methods documents (multimodal-rag-methods-v2.0.0.md)

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
| Visible Reasoning | "Articulate reasoning before output" | **Presentation:** HOW to weave images naturally into text flow? |
| Minimal Relevant Context | "Only load what's necessary" | **Threshold:** When does an additional image ADD vs. DISTRACT? |
| Failure Recovery & Resilience | "Handle failures appropriately" | **Fallback:** What specific information to provide when images fail? |
| Foundation-First Architecture | "Establish foundations before implementation" | **Structure:** HOW to organize reference documents for multimodal retrieval? |
| Transparent Reasoning & Traceability | "Make reasoning auditable" | **Citation:** HOW to attribute each claim to specific source fragments? |
| Measurable Success Criteria | "Define what good looks like" | **Evaluation:** WHICH metrics measure multimodal retrieval quality? |
| Accessibility & Inclusiveness | "Ensure access for all" | **Accessibility:** HOW to make visual content usable for all users? |

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

---

## Framework Overview: The Ten Principle Series

This framework organizes domain principles into ten series that address different functional aspects of multimodal RAG. This mirrors the Constitution's functional organization and groups principles by what they govern.

### The Ten Series

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

### The Twenty-Nine Domain Principles

**P-Series: Presentation Principles** — *How AI presents images with text*

| Principle | Primary Failure Mode Addressed |
|-----------|-------------------------------|
| P1: Inline Image Integration | MR-F1 (Image-Text Misalignment) |
| P2: Natural Integration | MR-F2 (Permission-Asking Pattern) |
| P3: Image Selection Criteria | MR-F3 (Visual Overwhelm), MR-F7 (Tangential Selection) |
| P4: Readability Optimization | MR-F6 (Complexity Mismatch) |
| P5: Audience Adaptation | MR-F6 (Complexity Mismatch) |
| P6: Accessibility Compliance | MR-F9 (Missing Alt Text), MR-F20 (Inaccessible Visual Content) |

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

**EV-Series: Evaluation Principles** — *How to measure and monitor quality*

| Principle | Primary Failure Mode Addressed |
|-----------|-------------------------------|
| EV1: Retrieval Quality Measurement | MR-F14 (Unmeasured Quality), MR-F23 (Retrieval-Limiting Caption) |
| EV2: Answer Faithfulness Assessment | MR-F15 (Faithfulness Gap) |
| EV3: Continuous Quality Monitoring | MR-F14 (Unmeasured Quality), MR-F22 (Silent Index Drift) |

**CT-Series: Citation Principles** — *Source attribution and traceability*

| Principle | Primary Failure Mode Addressed |
|-----------|-------------------------------|
| CT1: Fragment-Level Source Attribution | MR-F16 (Untraceable Claim) |
| CT2: Spatial Attribution for Visual Content | MR-F17 (Vague Visual Reference) |
| CT3: Citation Completeness | MR-F16 (Untraceable Claim) |

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
| O2: Operational Observability | MR-F22 (Silent Index Drift), MR-F14 (Unmeasured Quality) |

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

### P6: Accessibility Compliance

**Definition**
All visual content presented in multimodal responses MUST meet WCAG 2.1 AA standards. This includes alt text for every image, sufficient color contrast in referenced diagrams, and text-based alternatives for information conveyed solely through visual means.

**How the AI Applies This Principle**
- **Alt Text Required:** Every image in a response must have descriptive alt text that conveys the essential information the image provides.
- **Audio Description Guidance:** When advising on video or animated content, recommend audio descriptions for visual-only information.
- **Color Independence:** Never rely solely on color to convey meaning in diagrams or annotations.
- **Text Alternatives:** For complex visualizations (charts, graphs, diagrams), provide a text summary of key findings alongside the image.

**Constitutional Derivation**
Derived from `meta-governance-accessibility-and-inclusiveness`. Strengthened by DOJ 2026 mandate requiring digital accessibility compliance.

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
final_score = semantic_similarity * 0.6 + content_type_match * 0.25 + recency * 0.1 + step_alignment * 0.05
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

### A3: Vision-Guided Chunking

**Definition**
When chunking multimodal documents for indexing, tables, charts, diagrams, and other visual elements MUST be preserved as complete units. Chunk boundaries must respect visual element boundaries, not split them mid-element.

**How the AI Applies This Principle (When Advising on System Design)**
- **Visual Element Detection:** Use layout analysis or vision models to identify tables, charts, diagrams, and figures before chunking.
- **Boundary Respect:** Never split a table across two chunks. Never separate a diagram from its caption.
- **Context Preservation:** Include surrounding text context (title, caption, preceding paragraph) in the same chunk as the visual element.
- **Adaptive Chunk Size:** Allow larger chunks when needed to keep visual elements intact rather than enforcing rigid size limits.

**Constitutional Derivation**
Domain-native principle addressing the unique chunking requirements of multimodal documents. Aligned with `meta-core-context-engineering` (maintaining contextual integrity).

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

**Constitutional Derivation**
Derived from `meta-quality-visible-reasoning` (verify before committing) and `meta-governance-transparent-reasoning-and-traceability` (make reasoning auditable).

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

**Constitutional Derivation**
Domain-native principle addressing MR-F12 (Hallucinated Visual Description). Aligned with `meta-quality-visible-reasoning`.

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

**Constitutional Derivation**
Derived from `meta-governance-transparent-reasoning-and-traceability` and `meta-quality-visible-reasoning`.

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

**Constitutional Derivation**
Derived from `meta-governance-measurable-success-criteria`.

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

**Constitutional Derivation**
Derived from `meta-governance-measurable-success-criteria` and `meta-governance-transparent-reasoning-and-traceability`.

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

### EV3: Continuous Quality Monitoring

**Definition**
Multimodal RAG quality MUST be monitored continuously, not just at deployment time. Systems should detect drift in retrieval quality, changes in query patterns, and degradation from index or model updates.

**How the AI Applies This Principle (When Advising on System Design)**
- **Drift Detection:** Compare rolling retrieval metrics against established baselines. Alert when metrics drop beyond a threshold.
- **Query Pattern Tracking:** Monitor for shifts in query types that may indicate the benchmark set needs updating.
- **A/B Comparison:** When changing models or weights, run parallel evaluation before committing changes.
- **User Signal Integration:** Track implicit quality signals (follow-up queries suggesting first answer was insufficient, explicit negative feedback).

**Constitutional Derivation**
Derived from `meta-governance-measurable-success-criteria` and `meta-governance-periodic-re-evaluation-and-growth`.

**Why This Principle Matters**
RAG systems degrade silently. Content gets stale, query patterns shift, and model updates change retrieval behavior. Without continuous monitoring, quality erosion accumulates until users lose trust (MR-F14, MR-F22).

**When Human Interaction Is Needed**
- When drift alerts fire and root cause analysis requires human judgment.
- When setting threshold values for acceptable quality ranges.

**Common Pitfalls or Failure Modes**
- **The Set-and-Forget:** Deploying without ongoing quality monitoring.
- **The Alert Fatigue:** Too many low-signal alerts that get ignored, masking real issues.
- **The Lagging Indicator:** Detecting quality problems only after user complaints, not proactively.

---

## CT-Series: Citation Principles

*Principles governing source attribution and traceability*

### CT1: Fragment-Level Source Attribution

**Definition**
Every factual claim in a multimodal RAG response SHOULD be attributable to a specific fragment of a retrieved source—not just the source document as a whole, but the specific passage, paragraph, or image region that supports the claim.

**How the AI Applies This Principle**
- **Inline Attribution:** When presenting facts from retrieved sources, indicate which source (and ideally which section) supports each claim.
- **Granular References:** "According to [Document, Section 3.2]" rather than just "According to [Document]."
- **Multi-Source Transparency:** When a response synthesizes from multiple sources, indicate which source supports which part.

**Constitutional Derivation**
Derived from `meta-governance-transparent-reasoning-and-traceability`.

**Why This Principle Matters**
Document-level attribution is insufficient for verification (MR-F16). If a response cites a 50-page manual, users cannot efficiently verify the claim. Fragment-level attribution enables rapid verification and builds trust.

**When Human Interaction Is Needed**
- When response format constraints limit attribution detail.
- When multiple sources make the same claim and attribution is ambiguous.

**Common Pitfalls or Failure Modes**
- **The Broad Citation:** Citing an entire document for a specific fact.
- **The Missing Citation:** Presenting retrieved information without any source indication.
- **The False Citation:** Attributing a claim to a source that doesn't actually contain it.

---

### CT2: Spatial Attribution for Visual Content

**Definition**
When referencing specific elements within an image, the AI SHOULD identify the spatial location of the referenced element. For annotated images or screenshots, point to specific regions rather than referencing "the image" generically.

**How the AI Applies This Principle**
- **Region Identification:** "In the top-left of the dashboard screenshot, the metrics panel shows..." rather than "The screenshot shows..."
- **Element Labeling:** Reference specific UI elements by their visible labels when available.
- **VISA-Style Attribution:** When tooling supports it, use bounding box coordinates to pinpoint referenced regions within images.
- **Multiple Element Clarity:** When referencing several parts of one image, describe the spatial relationship.

**Constitutional Derivation**
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

### CT3: Citation Completeness

**Definition**
A multimodal RAG response MUST cite sources for all substantive claims. The proportion of cited vs. uncited claims serves as a quality indicator. Target: every factual claim attributable to a retrieved source should carry attribution.

**How the AI Applies This Principle**
- **Completeness Check:** Before delivering a response, verify that all factual claims have source backing.
- **Unsupported Claim Flagging:** If a claim cannot be sourced from retrieved content, either remove it, mark it as general knowledge, or explicitly note it as unsupported.
- **Attribution Ratio Tracking:** Monitor the ratio of attributed to unattributed claims as a system-level quality metric.

**Constitutional Derivation**
Derived from `meta-governance-transparent-reasoning-and-traceability` and `meta-quality-visible-reasoning`.

**Why This Principle Matters**
Incomplete citation creates a trust gradient within a single response—some claims are verifiable and others are not, but users cannot tell which is which. Full citation enables full verification.

**When Human Interaction Is Needed**
- When response contains legitimate general knowledge that doesn't require sourcing.
- When citation density makes the response unreadable.

**Common Pitfalls or Failure Modes**
- **The Partial Attribution:** Citing sources for some claims but not others in the same response.
- **The Citation-Free Summary:** Synthesizing information from sources without any attribution.
- **The Readability Trade-Off:** Citations make the response so cluttered that comprehension suffers.

---

## SEC-Series: Security Principles

*Principles governing knowledge base protection against multimodal-specific attacks*

**Cross-Domain Note:** SEC-Series covers security threats unique to multimodal knowledge bases (adversarial images, cross-modal injection, poisoned embeddings). For broader security concerns:
- **Agent memory injection and tool poisoning** — See multi-agent methods (multi-agent-methods, Title 4)
- **Application security, supply chain integrity** — See AI-coding methods (ai-coding-methods, Title 5)

### SEC1: Multimodal Poisoning Defense

**Definition**
Multimodal knowledge bases MUST include defenses against adversarial content that manipulates retrieval rankings or injects false information. Both localized attacks (targeting specific queries) and globalized attacks (broadly disrupting retrieval) must be addressed.

**How the AI Applies This Principle (When Advising on System Design)**
- **Input Sanitization:** Validate images and their metadata before ingestion into the knowledge base.
- **Embedding Anomaly Detection:** Monitor for embedding vectors that cluster unexpectedly or diverge from expected distribution patterns.
- **Content Provenance:** Track the source and modification history of every item in the knowledge base.
- **Multi-Signal Validation:** Do not rely solely on embedding similarity for retrieval; combine with metadata, recency, and source trust signals per A2.
- **Periodic Audit:** Regularly sample knowledge base content for unexpected changes, anomalous entries, or poisoned captions.

**Constitutional Derivation**
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

**Constitutional Derivation**
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

**Constitutional Derivation**
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

**Constitutional Derivation**
Derived from `meta-governance-transparent-reasoning-and-traceability`.

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

**Constitutional Derivation**
Domain-native principle addressing MR-F22 (Silent Index Drift). Aligned with `meta-operational-established-solutions-first` (proven operational patterns).

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

### O2: Operational Observability

**Definition**
Multimodal RAG systems MUST expose operational metrics sufficient to diagnose issues, track trends, and alert on degradation. Key metrics include query latency, retrieval error rates, index freshness, and embedding generation throughput.

**How the AI Applies This Principle (When Advising on System Design)**
- **Latency Tracking:** Monitor p50, p95, and p99 query latency. Alert when latency exceeds targets.
- **Error Rate Monitoring:** Track retrieval failures, embedding generation failures, and response generation failures separately.
- **Index Freshness:** Monitor time since last successful index update. Alert when content may be stale.
- **Throughput Metrics:** Track queries per second, embeddings generated per minute, and index size over time.
- **Cost Monitoring:** Track embedding generation costs, storage costs, and inference costs to detect unexpected spending.

**Constitutional Derivation**
Derived from `meta-governance-measurable-success-criteria` and `meta-governance-periodic-re-evaluation-and-growth`.

**Why This Principle Matters**
Without observability, operational problems manifest as quality degradation that is difficult to diagnose. A slow embedding endpoint, a stale index, or a spike in retrieval errors all affect the user experience but are invisible without monitoring.

**When Human Interaction Is Needed**
- When setting alerting thresholds for different operational metrics.
- When investigating anomalies flagged by monitoring.

**Common Pitfalls or Failure Modes**
- **The Black Box:** System runs but no one can see what's happening inside.
- **The Overloaded Dashboard:** Too many metrics with no clear hierarchy of importance.
- **The Missing Alert:** Metrics are collected but no alerting is configured for degradation.

---

## Implementation Guidance

### When AI Retrieves and Presents Images

1. **Query Analysis** — Understand what the user is asking and what visual support would help
2. **Image Retrieval** — Select best image using A2 (Relevance Scoring)
3. **Verification** — Verify cross-modal consistency (V1, V2) and source fidelity (V3)
4. **Placement Planning** — Determine where image belongs in response (P1)
5. **Natural Integration** — Present without permission-asking (P2)
6. **Selection Validation** — Verify unique value for additional images per P3
7. **Accessibility Check** — Ensure alt text and text alternatives per P6
8. **Text Calibration** — Match text complexity to audience (P4, P5)
9. **Citation** — Attribute claims to specific source fragments (CT1, CT2, CT3)
10. **Failure Handling** — If retrieval fails, apply F1 and F2

### When AI Advises on Document Structure

Apply **R-Series** principles to guide reference document organization:
- Collocate images with supporting text (R1)
- Ensure all images have alt text and contextual descriptions (R2)
- Establish consistent metadata/tagging scheme (R3)

### When AI Advises on System Design

Apply **A-Series**, **SEC-Series**, **DG-Series**, and **O-Series** principles:
- Recommend unified embedding approaches (A1)
- Define multi-signal relevance scoring (A2)
- Use vision-guided chunking for multimodal documents (A3)
- Implement poisoning defense and input validation (SEC1, SEC2)
- Design access control and lineage tracking (DG1, DG2)
- Plan for index versioning and observability (O1, O2)
- Consider platform-specific constraints (see Methods Appendix A)

### When AI Evaluates or Monitors Quality

Apply **EV-Series** principles to establish measurement:
- Define retrieval quality benchmarks (EV1)
- Assess answer faithfulness (EV2)
- Monitor for quality drift continuously (EV3)

---

## Relationship to Methods

This Domain Principles document establishes WHAT governance applies to multimodal RAG. The companion methods document establishes HOW to implement these principles.

### Available Methods Documents

| Document | Version | Coverage |
|----------|---------|----------|
| **multimodal-rag-methods-v2.0.0.md** | v2.0.0 | Presentation patterns, document structuring, retrieval architecture, failure handling, verification procedures, evaluation framework, citation methods, security procedures, data governance, operational management |

**Methods document includes:**
- Title 1: Presentation Patterns (image placement workflows, selection algorithms, accessibility checklist)
- Title 2: Reference Document Structuring (templates, metadata schemas)
- Title 3: Retrieval Architecture (4-layer architecture, embedding selection, vision-guided chunking, cross-modal linking)
- Title 4: Failure Handling (degradation procedures, error classification)
- Title 5: Verification & Hallucination Prevention (cross-modal consistency, scene graph validation, conflict resolution)
- Title 6: Evaluation Framework (RAG-Check metrics, multimodal MRR, drift detection, benchmark construction)
- Title 7: Citation & Attribution (fragment-level tracking, VISA spatial attribution, citation formatting, verification checklist)
- Title 8: Security for Multimodal Knowledge Bases (poisoning taxonomy, input validation pipeline, defense assessment, cross-domain references)
- Title 9: Data Governance (RBAC configuration, encryption, audit trail schema, lineage tracking)
- Title 10: Operational Management (index versioning, embedding lifecycle, prompt template versioning, cost monitoring, observability)
- Appendix A: Claude-Specific Implementation
- Appendix B: Infrastructure Landscape (current solutions, evaluation criteria)
- Appendix C: Research References

---

## Changelog

### v2.0.0 (Current)
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

*Version 2.0.0*
*Derived from: AI Coding Domain Principles v2.3.2, Multi-Agent Domain Principles v2.1.1, Storytelling Domain Principles v1.1.2, Constitution v2.4.1*
