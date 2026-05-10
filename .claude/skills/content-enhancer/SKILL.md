---
description: Transform raw content (transcripts, articles, lectures, informal posts) into enhanced reference documents — removes noise, restructures for clarity, fills knowledge gaps with researched best practices, preserves the author's voice. Invoke when the user provides source content to enhance, clean up, or transform into a useful reference document.
disable-model-invocation: true
allowed-tools: Bash Read Edit Write WebSearch WebFetch
---

## Context Snapshot

**Today:** !`date "+%Y-%m-%d"`

## Instructions

You are running the content enhancer skill. Read `procedure.md` in this skill folder for the full 5-step protocol.

### Execution Protocol

1. **Call `evaluate_governance(planned_action="content enhancement")`** before any writes.

2. **Get the source content.** If the user has not already provided it, ask: "What content would you like me to enhance? You can paste text, provide a file path, or share a URL."

3. **Read `procedure.md`** — it contains the complete processing protocol.

4. **Execute all 5 steps in order:**
   - Step 1: **Triage** — assess competence, identify audience, determine use context. STOP and escalate if any triage gate fails.
   - Step 2: **Analyze** — classify content type, separate core facts from presentation, fingerprint the voice.
   - Step 3: **Enhance** — restructure, clean, fill gaps per the gap-filling protocol. Apply voice preservation constraint throughout.
   - Step 4: **Assemble** — build the output document in the right format for the audience and use context.
   - Step 5: **Verify** — factual fidelity, voice check, adoption fitness. Fix any failures before delivering.

5. **Deliver the enhanced document** to the user. If they want to store it as a reference, they can use `capture_reference` separately.

### Key Principles

- **Voice preservation is the #1 risk.** If the output sounds like generic AI prose, you have failed. Re-read Step 3.4 in the procedure.
- **Flag what you add, not what you reorganize.** Use `[Editor's note: ...]` for AI-added facts and context. Structural improvements are the expected value — don't annotate them.
- **Coherence over completeness.** Removing extraneous material improves comprehension more than adding material. When in doubt, cut.
- **When uncertain, ask.** Six explicit escalation conditions are defined in the procedure. Use them.

### Governance Citations

- `kmpd-quality-assurance-qa2-artifact-adoption-fitness` — output must be easier to use than the original
- `kmpd-training-tl1-audience-appropriate-design` — identify target audience before generating
- Storytelling `E1` Human Voice Preservation — augment, do not replace the author's voice
