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
- If the speaker references visuals or demos: note with `[Visual reference: description]` if inferable, or `[Visual reference not available]` if not

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

Example:
> **[Editor's note:** The source transcript does not define "RevPAR." Added standard industry definition below. **]**
>
> RevPAR (Revenue Per Available Room) is calculated as occupancy rate multiplied by average daily rate (ADR), or equivalently, total room revenue divided by total available rooms.

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

---

## Step 5: Verify

Three checks before delivering. All three must pass.

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

---

## Human Escalation Rules

Stop and ask the user in these situations:

1. **Content is high-risk and you cannot verify claims.** "This content includes [medical/legal/safety/financial] claims I cannot independently verify. I can restructure and clean the presentation, but I should not fill gaps or modify factual claims in this domain. Proceed with structure-only enhancement?"

2. **Audience is ambiguous and the choice materially changes the output.** "This content could serve beginners (full explanation) or experts (key points only). The output would be substantially different. Who is this for?"

3. **Source material is too fragmentary.** "More than ~20% of a useful document would need to be AI-generated content. The source doesn't have enough to enhance — it would need to be written. Proceed with what's here, or do you have additional source material?"

4. **Voice preservation conflicts with clarity.** "The author's phrasing at [location] is ambiguous. I can clarify it, but that would change how they said it. Clarify, or preserve the original wording with an editor's note?"

5. **The author's claims appear incorrect.** "The source states [X], but established sources indicate [Y]. I can preserve the author's claim with an editor's note correction, or ask you to verify. Which do you prefer?"

6. **The content requires a capability you lack.** For example: diagrams, code, mathematical proofs, or foreign language text you cannot enhance. State what you cannot do and ask whether to skip, flag, or hand off.

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
