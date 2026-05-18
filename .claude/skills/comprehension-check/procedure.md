# Comprehension Check — Procedure

On-demand comprehension check for AI-generated work. Generates three-layer scaffolds per §16.8 and collects human response.

> **Trigger:** Invoke via `/comprehension-check`. Read this file and work through each step.
>
> **Input:** Scope — uncommitted changes, specific commit(s), file(s), or accumulated session work.
>
> **Output:** Comprehension scaffolds per §16.8 format + human response handling.

---

## Step 1: Determine Scope

Identify what work to check. Three scope modes:

### 1.1 User-specified scope

If the user named specific files, commits, or topics, use exactly that.

### 1.2 Automatic scope (recommended default)

Read the Context Snapshot in SKILL.md. Apply this priority:

| State | Scope |
|-------|-------|
| Uncommitted changes exist | Uncommitted changes (staged + unstaged) |
| No uncommitted, unpushed commits exist | Last unpushed commit (or batch if logically related) |
| Everything pushed, within active session | Last commit |
| User says "session" or "everything" | All commits since session start |

### 1.3 Scope sizing

- **Single logical unit** (1 feature, 1 fix, 1 refactor): one scaffold
- **Multiple logical units** (multi-phase work, several independent changes): one scaffold per unit
- **Large scope** (>500 lines changed, >10 files): consolidate into architectural themes, not file-by-file

If the scope is genuinely ambiguous (no changes, unclear intent), ask the user: "What would you like me to check? I see [state]. Options: [suggested scopes]."

---

## Step 2: Analyze Work Product

Read the actual files and diffs. Do not scaffold from commit messages or file names alone.

### 2.1 For code changes

- Read the diff (`git diff` or `git show`)
- Read enough surrounding context to understand the architectural purpose
- Identify: what problem was solved, what approach was chosen, what alternatives existed, what assumptions were made

### 2.2 For content/document changes

- Read the changed sections in full
- Identify: what was added/modified, why (from context, commit message, or session history), what the change means for the broader document structure

### 2.3 For mixed changes

- Group by logical unit, not by file type
- A feature that touches code + docs + config is one logical unit

### 2.4 Domain identification

Identify which domain(s) the work falls under. This determines scaffold technique:

| Domain | Scaffold source | Technique |
|--------|----------------|-----------|
| ai-coding | CFR §5.13.7, §4.1.2.1 | Linear Walkthrough + chunk-size awareness |
| ui-ux | CFR §10 | Component hierarchy + accessibility + design system |
| multimodal-rag | CFR §6.5 | Embedding/retrieval/threshold/KG scaffolding |
| kmpd | CFR §8.2 | Content scaffolding to comprehension scaffolding link |
| governance (constitution, rules-of-procedure) | §16.8 universal | Three-layer scaffold |
| other | §16.8 universal | Three-layer scaffold |

---

## Step 3: Generate Scaffolds

For each logical unit, generate a scaffold per §16.8.4 format.

### 3.1 Code outputs

```
COMPREHENSION SCAFFOLD — [logical unit name]
├─ INTENT: [what goal, why this approach — include key decisions where alternatives existed]
├─ BOUNDARIES: [assumptions, exclusions, scope limits]
└─ HANDOFF: [what to verify, where to debug, what breaks if assumptions change]
```

### 3.2 Content/document outputs

Integrate the three layers into a natural-language summary:

**[Logical unit name]**
- **Intent:** [what and why]
- **Boundaries:** [scope, assumptions, what is excluded]
- **Handoff:** [what to verify, what to check against other documents]

### 3.3 Depth scaling (per §16.8.3)

| Stakes | Scaffold depth |
|--------|---------------|
| Trivial (formatting, typos) | Skip — note "trivial, no scaffold needed" |
| Low (prototype, throwaway) | Single sentence covering all three layers |
| Standard (internal tools, iterative work) | Full three-layer scaffold (3-5 sentences total) |
| High (production, external-facing, irreversible) | Full scaffold + explicit assumption enumeration + verification checklist |

### 3.4 Anti-pattern self-check

Before presenting, verify each scaffold passes:

- [ ] **Not Scaffold Theater** — could this scaffold apply to a different output? If yes, rewrite with specifics.
- [ ] **Not Wall of Disclaimers** — is the scaffold shorter than the work product it describes? If longer, compress.
- [ ] **Not Post-Hoc Justification** — does the scaffold describe the intent that guided construction, or just what was built?
- [ ] **Specific to this output** — does the scaffold name actual files, functions, decisions, or constraints from this work?

---

## Step 4: Present to User

### 4.1 Presentation format

Group scaffolds by logical unit:

```
## Comprehension Check — [scope description]

### [Logical Unit 1 name]

[scaffold]

### [Logical Unit 2 name] (if multiple)

[scaffold]

---

**Response:** For each unit, you can respond:
- **Understood** — you have got it
- **Acknowledged** — proceeding without full comprehension (valid)
- **Explain** — you want a detailed walkthrough
- Or just **continue** with your next request (treated as Acknowledged)
```

### 4.2 Consolidation rule

If all logical units share one overarching intent, present one consolidated scaffold with sub-bullets for each unit, not separate scaffolds.

---

## Step 5: Handle Response

### 5.1 Response taxonomy (per §16.8.5)

| Response | Action |
|----------|--------|
| **Understood** | Acknowledge. No further action. |
| **Acknowledged** | Acknowledge. Note in session context. |
| **Explain** (for specific unit) | Produce detailed walkthrough — see §5.2 |
| **Explain** (general) | Walkthrough for all units, starting with highest-stakes |
| **Continue** (new prompt without addressing scaffold) | Treat as Acknowledged. Proceed with new request. |
| **Questions** (user asks specific questions) | Answer the questions. Maps to canonical "Explain" per §16.8.5 — targeted at their specific uncertainty. |

### 5.2 Explain walkthrough

When the user requests explanation, produce a detailed walkthrough using the domain-appropriate technique:

**For code (ai-coding domain):**
Use Linear Walkthrough (§5.13.7):
1. Entry point, execution flow, key decision points, exit
2. At each decision point: what alternatives existed, why this path
3. At each boundary: what assumptions hold, what breaks if they change

**For UI/UX:**
Walk through component hierarchy top-down:
1. Page/view structure, component tree, state management, accessibility
2. Design system alignment: which tokens/components, why these over alternatives

**For content/documents:**
Walk through the change narrative:
1. What triggered the change, what was added/modified, how it connects to existing content
2. Cross-references: what other documents are affected, what consistency constraints apply

**For governance changes:**
Walk through the normative impact:
1. What rule changed, what behavior changes, what enforcement chain is affected
2. Version implications: what downstream documents need updates

### 5.3 Scope boundary

If during analysis you discover issues with the work product itself (bugs, inconsistencies, missing pieces), note them in the scaffold's HANDOFF layer — but do not fix them. This is a comprehension tool, not a review tool. Say: "I noticed [issue] during the comprehension check. This is outside the scope of this check — address it separately."

---

## Quick Reference

```
/comprehension-check
  │
  ├─ Scope (Step 1)
  │   └─ User-specified OR auto-detect from git state
  │
  ├─ Analysis (Step 2)
  │   └─ Read actual files/diffs, identify logical units + domain
  │
  ├─ Scaffold generation (Step 3)
  │   └─ §16.8 format, domain-specific technique, depth by stakes
  │
  ├─ Presentation (Step 4)
  │   └─ Grouped by logical unit, response options shown
  │
  └─ Response handling (Step 5)
      ├─ Understood → done
      ├─ Acknowledged → noted
      ├─ Explain → domain-specific walkthrough
      └─ Continue → treated as Acknowledged
```
