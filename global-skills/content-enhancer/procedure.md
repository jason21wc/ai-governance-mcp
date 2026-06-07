# Content Enhancer — Procedure

Transform raw content into enhanced reference documents that are easier to use than the informal original, calibrated to the target audience.

> **Trigger:** Invoke via `/content-enhancer`. Read this file and work through each step.
>
> **Input:** Raw content — transcript, article, lecture notes, informal post, or other text.
>
> **Output:** Enhanced reference document, formatted for the identified audience and use context.

---

## Step 1: Triage

Before processing, answer three questions. If you cannot answer them from the provided content and context, ask the user.

### 1.1 Competence check

**Can I enhance this content without domain expertise I lack?**

Proceed if:
- The content is self-contained enough to identify its core claims
- You can distinguish facts from opinions in the material
- The domain is one where you can verify claims against known sources

STOP and escalate if:
- The content is in a domain where errors are dangerous (medical procedures, legal advice, safety-critical operations) AND you cannot verify claims against authoritative sources
- The content is heavily dependent on proprietary knowledge you do not have
- The source material is so fragmentary that enhancement would require more invention than organization

When stopping: tell the user what specific gap prevents enhancement, and what additional context would unblock it.

### 1.2 Audience identification

**Who will use this document, and what is their skill level?**

| Level | Who | Enhancement approach |
|-------|-----|---------------------|
| Training to proficiency | Cannot yet do the work independently | Preserve all explanation, add context for prerequisites |
| Expanding / filling gaps | Experienced, learning something new | Trim known foundations, emphasize what is new or different |
| Awareness / refresher | Knows this, needs reminder or update | Aggressive compression, highlight deltas |

If the user does not specify, infer from the content itself. State your inference explicitly: "I'm treating the audience as [level] because [reason]. Let me know if this is wrong."

### 1.3 Use context

**Where and how will this document be used?**

- Desktop reference (read on screen, search within) — optimize for scannability, use headers/anchors
- Quick reference (consulted during work) — aggressive compression, scannable in <30 seconds
- Study material (read sequentially to learn) — logical flow, progressive complexity
- Reference library entry (entered mid-document via search) — every section self-contained

If unstated, default to **desktop reference** and note the assumption.

### 1.4 Visual content assessment

**Does the source contain images, charts, screenshots, or diagrams?**

Scan the source material for visual elements: embedded images, referenced figures, inline screenshots, charts, or diagrams. Classify the visual situation:

Identify the source type and its **strategy** (SKILL.md Step 3 has the mechanics and escalation branches for each):

| Situation | Action |
|-----------|--------|
| Source is a file with embedded images (PDF, DOCX) | **Extract** per SKILL.md Step 3, then process per Steps 2.5, 3.5, 4.4, 5.4 |
| Source has inline/referenced images (HTML, Markdown) | **Copy/download** per SKILL.md Step 3, then process per Steps 2.5, 3.5, 4.4, 5.4 |
| Native-rendered deck (PPTX with shapes/charts, empty `ppt/media/`) | **Render** if LibreOffice present, **else escalate** to user PDF export (SKILL.md Step 3) |
| Legacy binary (`.doc`, `.ppt`) | **Convert first** (`textutil`/`soffice`), then re-assess on the converted file |
| Tabular source (XLSX / spreadsheet) | **Tabularize** → Markdown tables, not image extraction (SKILL.md Step 3); applies to §4.4 as tables, not §3.5 alt-text |
| Multi-file folder | **Orchestrate**: md5-dedup, global figure numbering, content-driven selection (SKILL.md Step 3) |
| Visual gap with no provided-source image (a concept/data the source never illustrates) | **Fill per the Gap-Filling Protocol visual lane**: re-express data as a Markdown table/prose, or link+describe an external source. Never embed or synthesize a third-party image. |
| Source references images you cannot access | Mark with `[Visual content referenced but not available: description]` and proceed with text |
| Unknown / encrypted / corrupt source | **Escalate** (SKILL.md Step 3 terminal branches); skip the file, continue with the rest |
| Source is text-only | Skip visual subsections (2.5, 3.5, 4.4, 5.4) — they do not apply |

If the source has visual content and the output format cannot support images (e.g., plain text requested), tell the user: "The source includes visual content that would be lost in plain text format. Proceed with text-only, or use a format that supports images?"

---

## Step 2: Analyze

### 2.1 Content-type classification

Identify the content type. This determines which cleaning and restructuring operations apply.

| Content type | Key signal | Primary challenge |
|-------------|-----------|------------------|
| **Transcript** | Speech patterns, filler words, repetition, temporal ordering | Linearize non-linear discussion, remove speech artifacts, reconstruct implicit structure |
| **Article / blog post** | Written prose, author voice present, may have gaps or opinions | Preserve voice, distinguish facts from opinions, fill genuine gaps |
| **Lecture / presentation notes** | Fragmentary, assumes shared context, may reference slides | Expand fragments into complete thoughts, supply missing context |
| **Informal post** | Casual tone, incomplete reasoning, valuable insights buried in noise | Extract signal from noise, preserve the insight while adding rigor |

### 2.2 Separate core facts from presentation

For every claim or piece of information in the source, classify it:

**Core facts** (preserve verbatim or near-verbatim):
- Definitions, technical terms, named concepts
- Specific numbers, measurements, dates, proper nouns
- Causal claims the author makes ("X causes Y")
- Sequences and procedures ("do A before B")
- The author's original insights, frameworks, or models
- Direct quotes from other sources

**Presentation** (enhance freely):
- How information is ordered and grouped
- Transitional language between ideas
- Examples and illustrations (can be improved or supplemented)
- Formatting, headings, visual hierarchy
- Repetition used for emphasis in speech (collapse in text)

**The boundary rule:** If changing it would make the author say "that's not what I said," it is a core fact. If the author would say "sure, that's a better way to present it," it is presentation.

### 2.3 Voice fingerprinting

Before enhancing, identify the source author's voice characteristics:

- **Vocabulary level:** Technical jargon density, colloquialisms, formality range
- **Sentence patterns:** Short declarative vs complex compound, active vs passive tendency
- **Characteristic phrases:** Recurring expressions, domain-specific shorthands
- **Reasoning style:** Evidence-to-conclusion or conclusion-then-support? Analogies? First principles?
- **Tone:** Authoritative, conversational, cautionary, enthusiastic, clinical

Write 2-3 sentences summarizing the voice. This is your constraint for Step 3.

### 2.4 Structural analysis

Map the source material's structure:
- What topics does it cover?
- What is the logical dependency order? (What must be understood before what?)
- Where does the source deviate from logical order? (Tangents, callbacks, out-of-sequence mentions)
- What gaps exist? (Topics mentioned but not explained, assumed knowledge)

### 2.5 Visual content inventory

If visual content was identified in Step 1.4, catalog each visual element:

- **What it shows** — one-sentence factual description (what is visible)
- **What it means** — its purpose in the source (illustrates a concept, shows data, demonstrates a step)
- **Where it belongs** — which section or claim it supports (maps to structural analysis from 2.4)
- **Current state** — does it have alt text? A caption? Adequate resolution? Metadata?
- **Extraction status** — has the image been extracted to the output directory? File path if yes, reason if no.

This inventory drives placement decisions in Step 4.4 and verification in Step 5.4. *(Cross-ref: mrag R1 Image-Text Collocation, R2 Descriptive Context)*

---

## Step 3: Enhance

### 3.1 Restructure

Reorder the content into logical dependency order:
- Foundational concepts first
- Build complexity progressively
- Group related concepts that were scattered in the original
- Eliminate redundancy (say it once, say it well)

**Content-type-specific restructuring:**

**Transcripts:**
- Remove filler words (um, uh, you know, like, so, right)
- Remove false starts and self-corrections (keep the correction, drop the error)
- Collapse repetition — when the speaker makes the same point three ways, synthesize into the strongest version
- Convert temporal order ("and then I realized...") to logical order (conclusion first, context second)
- Reconstruct implicit paragraph breaks from topic shifts
- If the speaker references visuals or demos: preserve the original visual if available; otherwise note with `[Visual reference: description]` if inferable, or `[Visual reference not available]` if not. See §3.5 for full visual content enhancement (alt text, context descriptions, metadata).

**Articles / blog posts:**
- Preserve the author's argument structure if it is already logical
- Reorder only when the original structure genuinely impedes comprehension
- Do not rewrite clear prose into bullet points — respect the author's choice of form
- Tighten verbose passages, but preserve distinctive phrasing

**Lecture / presentation notes:**
- Expand telegraphic notes into complete sentences
- Supply missing articles, verbs, and connectors
- Reconstruct the implicit narrative from slide-style fragments
- Flag where expansion required inference: "The notes say [X]; this likely means [expanded interpretation]"

**Informal posts:**
- Extract the core insight and lead with it
- Reorganize stream-of-consciousness into structured argument
- Preserve the author's examples and anecdotes — these carry voice
- Remove platform-specific elements (hashtags, @mentions) unless they carry meaning

### 3.2 Clean and clarify

For all content types:
- Fix grammar, spelling, and punctuation errors
- Resolve ambiguous pronoun references
- Replace jargon with plain language ONLY when the audience level (Step 1.2) warrants it
- Add clarifying context for terms the audience may not know
- Convert passive voice to active where it improves clarity, but NOT where passive is the author's deliberate style

### 3.3 Fill gaps

See Gap-Filling Protocol below.

### 3.4 Voice preservation constraint

During all enhancement work, apply these guards:

**Do:**
- Match the author's vocabulary level — if they use technical terms, keep them
- Preserve the author's reasoning style — if they build inductively, do not restructure deductively
- Keep characteristic phrases and expressions verbatim
- Maintain the author's level of formality
- Preserve the author's examples, anecdotes, and analogies

**Do not:**
- Replace short declarative sentences with complex compound ones (or vice versa)
- Add hedging language the author did not use ("it could be argued that...")
- Remove colloquialisms to sound more "professional"
- Add transition phrases not in the author's style ("Furthermore," "It is worth noting that," "Importantly,")
- Replace the author's specific examples with "better" generic ones
- Smooth out rough edges that carry personality ("This is flat wrong" — do NOT change to "This approach has limitations")

**The cover test:** After enhancement, read a paragraph aloud. Could the original author have written it? If the paragraph sounds like it could have come from any textbook on the subject, you have lost the voice. Revert to the source and try again with lighter touch.

### 3.5 Visual content enhancement

Images should already be extracted to `enhanced/{slug}/` per SKILL.md Step 3. Enhance the supporting text — not the image itself:

- **Alt text:** If missing, write concise alt text (~125 characters) describing the image's purpose, not its appearance. Mark AI-generated alt text: `[Alt text (AI-generated, verify): description]`. *(Cross-ref: mrag P5 Accessibility Compliance)*
- **Context description:** If the image lacks a caption or surrounding explanation, add one per the Gap-Filling Protocol. Mark it with `[Editor's note: ...]` as with any gap-fill. *(Cross-ref: mrag R2 Descriptive Context)*
- **Retrieval metadata:** If the enhanced document will enter a RAG system, note relevant tags (concept, step, use case) in a comment or metadata block adjacent to each image. *(Cross-ref: mrag R3 Retrieval Metadata)*

**Do not:** generate, recreate, redraw, or alter any **provided source image** (its pixels). Re-expressing the underlying **data** as a Markdown **table or prose** is a separate, allowed operation governed by the Gap-Filling Protocol's visual lane (§2.2 facts, not pixels); synthesizing or redrawing a **chart image** stays prohibited unless the user explicitly requests it. Do not replace an image with a text description unless the image is genuinely inaccessible. Do not add decorative images.

---

## Gap-Filling Protocol

Gap-filling is the highest-risk enhancement operation. AI-added content that presents fabricated information as fact is worse than leaving a gap.

### When to fill a gap

Fill ONLY when ALL conditions are met:

1. **The gap is real.** The source mentions a concept, references a fact, or implies knowledge it does not explain. Not just something you think the document "should" cover.
2. **The gap impairs the audience.** A missing prerequisite definition, an unexplained acronym, a referenced concept with no context.
3. **You can fill from authoritative knowledge.** The information exists in established sources.
4. **The domain is not high-risk.** For medical, legal, safety-critical, or financial content: do NOT fill gaps. Flag them with `[Gap: description of what is missing]`.

### When NOT to fill

- The author deliberately omitted something (scoping decision, not oversight)
- The gap requires proprietary or domain-specific knowledge you do not have
- Filling would require generating claims the author did not make
- The content is high-risk (medical, legal, safety, financial)
- You are not confident in the accuracy of the fill

### How to mark AI-added content

All gap-filled content MUST be visually distinguishable. Use:

> **[Editor's note:** brief description of what was added and why **]**

Then provide the content normally. The editor's note signals "this was not in the original"; the reader decides what to do with it.

**Disclose the grounding of every fill — inside the same editor's note, no separate marker:**
- **Externally researched:** include the source inline, extending the citation form with a URL — `[Editor's note: … — [Source: <name>, <URL>]]`. (Citation format per `title-40-multimodal-rag-cfr.md` §7.3; principle `mrag-citation-ct1`. Verify the source actually states the claim before citing — never fabricate a citation.)
- **From model knowledge:** mark it — `[Editor's note: … — from general domain knowledge, not externally verified]`.

Keep your existing judgment about *when* to research; this contract governs *disclosure*, not whether to search. The source hierarchy below still bars blogs/forums as authoritative, so disclosure never licenses a weak-source citation. The disclosure applies to every gap-fill, including the §3.5 visual context-fills.

Example:
> **[Editor's note:** The source transcript does not define "a-unit-metric." Added standard industry definition below — from general domain knowledge, not externally verified. **]**
>
> a-unit-metric (Revenue Per Available Room) is calculated as occupancy rate multiplied by average daily rate (ADR), or equivalently, total room revenue divided by total available rooms.

### Source hierarchy for gap-filling

Prefer sources in this order:
1. The author's other published work on the same topic
2. Primary sources the author cites or references
3. Authoritative standards and specifications in the domain
4. Established textbooks and reference works
5. Peer-reviewed research

Do NOT use: blog posts, social media, forums, or AI-generated content as authoritative sources.

### Gap-filling limits

- No more than ~20% of the final document should be AI-added content. If gaps exceed this, the source is too fragmentary — escalate to the user.
- Each gap-fill should be self-contained. Do not build chains where fill B depends on fill A.
- When in doubt, leave the gap and mark it: `[Gap: description]`. The user can provide the information.

### Visual gap-filling

A visual gap (a concept or data that needs a figure the source lacks) is filled under the same gate as a textual gap (real + impairs audience + not high-risk), and **only when no provided-source image already covers it**. Two lanes — never embed or synthesize a third-party image:

1. **Re-express → table or prose (preferred, for information/data).** When the gap's value is the underlying *facts* (not copyrightable, per §2.2): rebuild a clean **Markdown table**, or describe it in prose. This is a §2.2 presentation operation on facts, not a generated image. **Do not synthesize or redraw a chart image** — that reads as fabrication in a voice-preserving document and reopens the §3.5 prohibition; a redrawn/synthesized chart is an explicit user opt-in, not an agent-authorized default. Mark the table as a gap-fill (`[Editor's note: …]`) with its data source cited per the contract above, and verify it **against the source data** (Step 5.4).
2. **Link + describe (when the specific image *is* the information).** A screenshot, or a specific drawing that cannot be faithfully tabularized: describe it and cite/link the source URL, marked `[Visual content referenced but not available: <description>]`. Pixels never enter the document.

Excluded outright: photos of artwork or people, and any image whose license is unknown — link only, never include. Copyright protects the *image*, not the facts inside it; internal-use docs err on excluding anything not known to be freely distributable. *(Cross-ref: mrag P3 three-test gates whether the visual is worth referencing at all; CT1/CT2 govern source attribution.)*

---

## Step 4: Assemble

### 4.1 Structural invariants

Every enhanced document includes:

**Document header:**
- Title (derived from content, or ask user)
- Source attribution: "Enhanced from [source description] by [author name if known]"
- Date of source material (if known) and enhancement date
- Audience level (from Step 1.2)

**Content body:**
- Organized by topic, not by source order (unless source order IS the logical order)
- Each section has a descriptive heading
- Each section is self-contained — a reader arriving via search should understand it without reading prior sections
- Core facts are present and unaltered
- AI-added content is marked per Gap-Filling Protocol

**No boilerplate.** Do not include:
- "Learning objectives" (unless the source was designed as training material)
- "Prerequisites" section (fold prerequisite context into sections that need it)
- "Summary" section (the document should be the right length without one)
- Retrieval practice questions
- Confidence scores, fidelity percentages, or quality metrics
- Enhancement tags ([SOURCE], [ENHANCEMENT], [REORGANIZED])

### 4.2 Format selection

Format follows use context:

| Use context | Format guidance |
|------------|----------------|
| Desktop reference | Generous headers (H2 major, H3 sub). Bold key terms on first use. Tables for comparisons. Bullet lists for enumeration. Prose only where narrative flow serves comprehension. |
| Quick reference | Maximum compression. Tables and bullets dominate. No prose paragraphs longer than 3 sentences. Bold the actionable content. Scannable in under 60 seconds. |
| Study material | Prose-dominant, progressive complexity. Use examples generously. Longer sections acceptable. |
| Reference library entry | Follow the project's reference library frontmatter format if `capture_reference` is available. Every section self-contained. |

**The scannability test:** Can the user find a specific fact in under 30 seconds by scanning headings and bold terms? If not, add more structural signaling.

### 4.3 Content-type-specific assembly

**Transcripts -> reference document:** Do not preserve temporal markers unless requested. The output is a reference document, not an annotated transcript. Attribute claims to speakers only when attribution matters for credibility.

**Articles -> enhanced article:** Preserve the article form. The output should read as a better version of the same article, not a restructured reference doc. Maintain paragraph structure; enhance, do not atomize.

**Lecture notes -> structured document:** The output should be a document someone could learn from without attending the lecture. Expand, do not just reformat. Mark expansions per Gap-Filling Protocol.

**Informal posts -> distilled document:** Lead with the core insight. Provide supporting evidence in structured form. Preserve the author's voice and examples. The reader should think "this person had a great point" — not "an AI summarized something."

### 4.4 Visual content assembly

If visual content was identified in Step 1.4, place each preserved visual element. Reference extracted images using relative Markdown syntax: `![Revenue comparison](fig-01-revenue-comparison.png)`

> **Re-expressed tables are not extracted images.** A table from the Gap-Filling visual lane is placed inline as Markdown and marked `[Editor's note: …]`; it has no `fig-*` file and is **not** subject to the §5.4 file-presence check. The `![](fig-*)` syntax and that check apply only to images extracted from a provided source.

1. **Position at the point of relevance.** The image appears immediately after the text it supports — not in an appendix, not clustered in a gallery. Use the inventory (Step 2.5) for placement mapping. *(Cross-ref: mrag P1 Inline Image Integration, R1 Image-Text Collocation)*
2. **Apply the three-test filter.** Before including each image, confirm: (a) it directly supports the surrounding text (Coherence), (b) it adds information the text alone does not convey (Unique Value), (c) it can be placed adjacent to the text it supports (Proximity). Drop images that fail any test. *(Cross-ref: mrag P3 Image Selection Criteria)*
3. **Ensure accessibility.** Every included image has alt text and a text summary of its key information. Complex charts or diagrams get a brief prose explanation of their main finding alongside the image. *(Cross-ref: mrag P5 Accessibility Compliance)*

If the enhanced document has significantly more or fewer images than the source, note this discrepancy for verification in Step 5.4.

---

## Step 5: Verify

Checks before delivering. All must pass (§5.1–§5.5).

### 5.1 Factual fidelity

Re-read the source material. For every core fact identified in Step 2.2:
- Is it present in the output?
- Is it stated accurately (same meaning as the original)?
- Has any core fact been altered, softened, or reframed?

If any core fact was dropped or altered: fix it before delivering.

### 5.2 Voice check

Compare a representative paragraph from your output against the voice fingerprint from Step 2.3. Check for:

- **Generic academic prose:** "It is important to note that..." / "One could argue..." / "In conclusion..." — if the source author did not write this way, neither should you
- **Hedging inflation:** Did you add more qualifications than the author used? If the author said "X is true," do not change it to "X appears to be generally accepted"
- **Vocabulary drift:** Are you using words the author would not use? Check 3-4 distinctive terms from the source
- **Transition word injection:** "Furthermore," "Moreover," "Additionally," "It is worth noting" — these are AI tells. Remove them if the author did not use them

If the voice has drifted: identify which paragraphs diverged and re-enhance with lighter touch.

### 5.3 Adoption fitness

"Is this enhanced document easier to use than the original for the target audience in their actual use context?"

- Would the target user reach for this document instead of the original?
- Can they find what they need faster than in the original?
- Is the format matched to their use context?

If the enhanced document is not clearly better: identify what is wrong and fix it before delivering.

### 5.4 Visual content verification

If the source contained visual elements (Step 1.4):

- **Presence check:** Every visual element from the inventory (Step 2.5) is either included in the output or explicitly noted as unavailable. No silent drops.
- **Position check:** Each image appears adjacent to the text it supports, not displaced to an appendix or unrelated section. *(Cross-ref: mrag P1, R1)*
- **Cross-modal consistency:** Text descriptions of images match what the images actually show. If the text says "the chart shows a downward trend" — verify the chart shows a downward trend. *(Cross-ref: mrag V1 Cross-Modal Consistency Verification)*
- **Re-expressed-table fidelity:** A table rebuilt from data (Gap-Filling visual lane) is verified **against the source data** — every value traces to the source, not merely to the table's own caption. *(Cross-ref: mrag V1)*
- **Accessibility check:** Every image has alt text. Complex visuals have text summaries. *(Cross-ref: mrag P5)*
- **File check:** Every image referenced in the document (`![...](fig-*.*)`) has a corresponding file in the output directory. No broken references.

If any check fails: fix it before delivering. A missing image with no explanation is worse than a `[Visual content not available]` placeholder.

### 5.5 Research disclosure

If any gap was filled (Step 3.3):

- **Researched fills carry their source:** every externally-researched fill has its source inline in the editor's note — `[Editor's note: … — [Source: <name>, <URL>]]`.
- **From-memory fills are marked:** every fill from model knowledge carries `— from general domain knowledge, not externally verified`.

This is a presence/format self-check (a skill runs no enforcement hook mid-task): an editor's note that states a fact with neither a source nor the from-memory marker fails it. Add the source or the marker before delivering.

---

## Human Escalation Rules

Stop and ask the user in these situations:

1. **Content is high-risk and you cannot verify claims.** "This content includes [medical/legal/safety/financial] claims I cannot independently verify. I can restructure and clean the presentation, but I should not fill gaps or modify factual claims in this domain. Proceed with structure-only enhancement?"

2. **Audience is ambiguous and the choice materially changes the output.** "This content could serve beginners (full explanation) or experts (key points only). The output would be substantially different. Who is this for?"

3. **Source material is too fragmentary.** "More than ~20% of a useful document would need to be AI-generated content. The source doesn't have enough to enhance — it would need to be written. Proceed with what's here, or do you have additional source material?"

4. **Voice preservation conflicts with clarity.** "The author's phrasing at [location] is ambiguous. I can clarify it, but that would change how they said it. Clarify, or preserve the original wording with an editor's note?"

5. **The author's claims appear incorrect.** "The source states [X], but established sources indicate [Y]. I can preserve the author's claim with an editor's note correction, or ask you to verify. Which do you prefer?"

6. **The content requires a capability you lack.** For example: diagrams, code, mathematical proofs, or foreign language text you cannot enhance. State what you cannot do and ask whether to skip, flag, or hand off.

7. **Visual content is critical but inaccessible.** "The source references [N] images/charts/diagrams that I cannot access or display. These appear to carry essential information (not just decoration). Proceed with text-only enhancement and visual placeholders, or can you provide the images?"

---

## Quick Reference: What Changes by Content Type

| | Transcript | Article | Lecture notes | Informal post |
|---|---|---|---|---|
| **Filler removal** | Aggressive | None | Light | Moderate |
| **Restructuring** | Heavy (temporal -> logical) | Light (preserve structure) | Heavy (fragments -> narrative) | Moderate (stream -> structure) |
| **Voice focus** | Speaker expertise & insight | Author's written style | N/A (notes lack voice) | Author's personality & examples |
| **Gap-filling** | Moderate (implicit context) | Low (already polished) | High (notes assume context) | Moderate (reasoning gaps) |
| **Format tendency** | Desktop reference | Enhanced article | Study material | Distilled reference |
| **Biggest risk** | Losing speaker expertise | Homogenizing prose | Inventing beyond notes | Sanitizing personality |
| **Visual handling** | Preserve if available; placeholder if referenced but missing | Preserve inline positioning | Expand slide references; preserve available images | Preserve screenshots/diagrams that carry the insight |

> **Visual gaps (any content type):** when a needed figure is missing from the source, fill per the Gap-Filling Protocol's visual lane — re-express data as a table/prose, or link+describe — and never embed or synthesize a third-party image (§3.5).
