---
version: "1.2.0"
status: "active"
effective_date: "2026-03-29"
domain: "kmpd"
governance_level: "federal-regulations"
---

# Knowledge Management & People Development Methods v1.2.0
## Operational Procedures for AI-Assisted Organizational Knowledge and Capability

> **SYSTEM INSTRUCTION FOR AI AGENTS:**
> This methods document provides HOW-TO procedures for implementing KM&PD domain principles. It is subordinate to the domain principles document (title-25-kmpd.md), which establishes WHAT governance applies.

**Version:** 1.2.0
**Status:** Active
**Effective Date:** 2026-03-29
**Governance Level:** Methods (SOPs) — subordinate to KM&PD Domain Principles
**Access:** Proprietary

---

### Governance Hierarchy

```
Constitution (Meta-Principles)
  └─ KM&PD Domain Principles (Federal Statutes)
       └─ KM&PD Methods (This Document — Operational Procedures)
```

**Two Pillars:**
- **Manage Process** → Sections 1-4, 8 (Knowledge Architecture, Document Types, Scaffolded Complexity)
- **Lead People** → Sections 5-7 (People Development, Assessment, Training Delivery)

**Cross-Domain:**
- For narrative engagement in knowledge content → Storytelling domain
- For software process documentation → AI-Coding domain (process gates) + this domain (knowledge architecture)

### Legal System Analogy

| Legal Concept | Framework Equivalent | Purpose |
|---------------|---------------------|---------|
| Bill of Rights | S-Series (constitution.md) | Immutable safety guardrails with veto authority |
| Constitution | Meta-Principles (constitution.md) | Universal reasoning laws |
| Federal Statutes | title-25-kmpd.md | Domain-specific binding law |
| Rules of Procedure | rules-of-procedure.md | How the framework evolves and maintains itself |
| **Federal Regulations (CFR)** | **This document** | **Operational rules implementing statutes** |
| Agency SOPs | Tool-specific guides | Platform-specific execution |
| Case Law | Reference Library | Precedent from real application |

---

### Importance Tags Legend

| Tag | Meaning |
|-----|---------|
| **CRITICAL** | Must follow in all KM&PD work. Skipping creates safety, compliance, or knowledge integrity failures. |
| **IMPORTANT** | Should follow in most cases. Exceptions require documented rationale. |
| **OPTIONAL** | Recommended for quality. Apply when scope and timeline permit. |

---

## 1 Knowledge Architecture & Document Spectrum

**Importance: CRITICAL — Foundation for all knowledge artifacts**

**Implements:** KA1 (Single Source Architecture), KA2 (Derivation Chain Integrity), KA3 (Progressive Abstraction)

### 1.1 First Interaction Protocol

**Applies To:** first time a user asks for help with knowledge management, process documentation, training materials, or people development artifacts

When a user first engages the KM&PD domain, determine scope:

**Ask:** "Are you building a full knowledge management system for a process area, or do you need a specific artifact (checklist, SOP, training material)?"

- **Full system** → Start with §1.2 (maturity assessment) then §1.3 (Detailed KB scaffold)
- **Specific artifact** → Ask if a Detailed Knowledge Base exists as the source. If yes, derive from it. If no, flag the gap and proceed with the specific artifact while noting derivation is not possible.

### 1.2 Maturity Self-Assessment

**Applies To:** scoping a knowledge management initiative, determining where to start with process documentation, routing users to the right methods based on organizational readiness

Present the maturity model and ask the user to self-identify:

| Level | Name | Key Question |
|-------|------|-------------|
| 0 | **Tribal** | "Is the process knowledge mostly in people's heads?" |
| 1 | **Ad Hoc** | "Do some documents exist but they're scattered or outdated?" |
| 2 | **Structured** | "Is there a central, organized knowledge base for core processes?" |
| 3 | **Extracted** | "Do practitioners have quick references and job aids derived from the knowledge base?" |
| 4 | **Managed** | "Do you track document currency and training effectiveness with metrics?" |
| 5 | **Optimizing** | "Is continuous improvement embedded in your knowledge management?" |

**Routing:**
- Level 0-1 → Start with §2 (Detailed Knowledge Base Authoring) for core processes
- Level 2 → Start with §3 (Quick Reference Design) to create purpose-driven extractions
- Level 3 → Start with §5 (People Development Artifacts) to build competency systems
- Level 4-5 → Focus on specific gaps the user identifies

### 1.3 Detailed Knowledge Base Scaffold

**Applies To:** building a new process knowledge base from scratch, structuring captured tribal knowledge, creating the initial table of contents for a process area

When building a new Detailed KB, create the table of contents first (the "destination map"):

**Template — Detailed Knowledge Base Structure:**

```markdown
# [Process Area Name] — Detailed Knowledge Base

**Version:** 0.1 (MVP)
**Status:** [Current State — Pending Validation | Standard Operating Procedure]
**Last Verified:** [Date]
**Process Owner:** [Name/Role]

## 1. Core Workflow
[The main process flow covering ~80% of daily work]
### 1.1 [First major step]
### 1.2 [Second major step]
...

## 2. Branching Procedures
[Variations that fork from the main flow]
### 2.1 [Branch scenario]
...

## 3. Advanced / Edge Cases
[Less common scenarios, complex situations]

## 4. Troubleshooting
[Decision trees, problem resolution — extractable to Troubleshooting Guide]

## 5. Maintenance & Periodic Tasks
[Upkeep, scheduled activities, preventive actions]

## 6. Safety, Warnings & Hazards
[Critical cautions embedded at relevant steps]
⚠️ SAFETY DISCLAIMER: This document has not been reviewed for regulatory
compliance. Verify all safety and regulatory requirements with a qualified
professional before operational use.

## 7. Quality Checks & Inspection Points
[Verification steps embedded in the workflow]

## 8. Tools & Materials Required
[Prerequisites per section — software, equipment, access, materials]

## 9. Regulatory & Compliance Requirements
[Where applicable — OSHA, EPA, FDA, industry-specific]

## 10. History & Rationale
[Why the process is designed this way — institutional knowledge]

---
Cross-Training Matrix Items: [List major items derived from this KB]
Derived Artifacts: [List Quick Refs, VWIs, etc. derived from this KB]
```

**MVP approach:** Fill Section 1 (Core Workflow) first. Stub remaining sections with descriptions of what goes there. Expand based on need.

**Organization rule:** Structure by process flow order (how the work happens) or foundation-first (basics before advanced). Never alphabetical or by system menu.

### 1.4 Derivation Chain Tracking

**Applies To:** creating quick references, visual work instructions, or training materials derived from a detailed knowledge base; updating downstream artifacts when the source KB changes

Every artifact derived from a Detailed KB must include:

```markdown
---
**Derived from:** [KB Name] v[Version], Section [X.Y]
**Last synced:** [Date]
**Derivation type:** [Quick Reference | Visual Work Instruction | Troubleshooting Guide | SIPOC | Process Flow | Cross-Training Matrix Item]
---
```

When updating a Detailed KB section, list all downstream artifacts that may need updating:

```markdown
## Change Log
| Date | Section | Change | Downstream Artifacts Affected |
|------|---------|--------|-------------------------------|
| [Date] | 1.3 | Updated step 4 per new software version | Quick Ref v2.1, VWI-003, Training Module 1.3 |
```

### 1.5 Knowledge Conflict Prevention

**Applies To:** creating documentation for processes that may already have existing SOPs, work instructions, or informal documentation; consolidating multiple knowledge sources

Before creating new documentation for any process:

1. **Ask:** "What documentation already exists for this process? Are there SOPs, work instructions, or training materials anywhere — even outdated ones?"
2. **If existing docs found:** Review them first. Use as starting material per the build approach (§2.2).
3. **If creating alongside existing docs:** Flag the conflict risk. Recommend consolidating to one source or explicitly superseding the old documentation.
4. **Include in generated artifacts:** "This document supersedes: [list] as of [date]" when replacing existing documentation.

### 1.6 Knowledge Base Update Procedure

**Applies To:** process changes requiring documentation updates, keeping knowledge bases current after workflow modifications, propagating changes through the derivation chain

When a user needs to update an existing Detailed KB because the process has changed:

1. **Identify changed sections** — ask the user what changed and which KB sections are affected
2. **Check derivation chain** — before editing, identify all downstream artifacts derived from the affected sections (Quick Refs, VWIs, Cross-Training Matrix items, Job Description responsibilities)
3. **Update the KB content** — make the changes in the source KB
4. **Update the change log** — record what changed, when, and which downstream artifacts are affected (per §1.4)
5. **Flag downstream artifacts** — list all affected extractions and mark them as "pending sync" with the updated KB
6. **Update or regenerate** downstream artifacts as needed — or flag for the user to update manually

**Rule:** Never update a downstream artifact without first updating the source KB. The derivation chain flows one direction: source → extraction.

---

## 2 Detailed Knowledge Base Authoring

**Importance: CRITICAL — The single source of truth for process knowledge**

**Implements:** KA1 (Single Source Architecture), QA1 (Safety & Compliance Completeness), QA2 (Artifact Adoption Fitness), PD1 (Verification Guidance Responsibility)

### 2.1 Design Principles for the Detailed Knowledge Base

**Applies To:** writing process documentation, structuring detailed knowledge bases, applying Lean and Six Sigma principles to documentation quality

**Thorough ≠ Wordy.** Apply Lean and Six Sigma to the documentation itself:
- **Lean (eliminate waste):** Don't write 50 words when 10 will do. Don't write a paragraph when a screenshot communicates better. Every word earns its place.
- **Six Sigma (eliminate variability):** Write so it cannot be misinterpreted. Ambiguity in instructions IS a defect. Consistent structure, terminology, formatting throughout.

**The Detailed Knowledge Base should tell a story.** It takes the reader down the process path — foundations first, then building complexity. When done well, you engage the reader because you provide what they need in the most effective way. Cross-reference: apply Storytelling domain principles for narrative engagement.

### 2.2 Build Approach

**Applies To:** starting a new detailed knowledge base, incorporating existing documentation and tribal knowledge, structuring the interview and observation process

1. **Gather existing materials** — printed, digital, whatever exists. Fastest way to get up to speed before talking to practitioners.
2. **Build initial draft** from existing materials. Structure per §1.3 template.
3. **Validate through interviews and observation (gemba)** — talk to and watch the people doing the work. Confirm, fill gaps, correct errors. The gap between documented process and actual process is itself a primary finding.
4. **Iterate** — incorporate feedback, refine, expand.

**AI assists with steps 1-2** (ingesting existing materials, structuring into the framework) **and step 4** (incorporating feedback). **Step 3 is inherently human** — you have to go watch.

### 2.3 Step Writing Standards

**Applies To:** writing individual process steps in knowledge bases, deciding between text and visual formats, structuring step-key point-reason patterns

Each step in the Detailed Knowledge Base follows a consistent format:

| Element | Purpose | Example |
|---------|---------|---------|
| **Step number** | Sequence | "Step 3:" |
| **Action** | What to do (one action per step) | "Click 'Create New Order' in the toolbar" |
| **Key Point** | Critical detail that affects success | "Key Point: The order type must be 'Standard' — selecting 'Repair' triggers a different workflow" |
| **Reason** | Why this matters (builds understanding) | "Reason: Repair orders bypass the material reservation step, which would cause a shortage for standard builds" |
| **Visual** | Screenshot, diagram, or image | [Screenshot showing the toolbar with 'Create New Order' highlighted] |

**When to use visuals instead of text:**
- Screen interactions → screenshot with annotations
- Physical layouts → diagram or photo
- Process flows → flowchart
- Decision points → decision tree diagram
- Equipment → labeled photo

**Rule:** If you're writing more than 3 sentences to describe something visual, use an image instead.

### 2.4 Verification Recommendation

**Applies To:** finalizing any generated knowledge artifact, adding validation disclaimers, recommending self-test/SME review/novice test verification steps

Every Detailed Knowledge Base must end with a verification section:

```markdown
## Verification Status

**Document Status:** [Current State — Pending Validation | Validated Standard]
**Created by:** [Name/Role]
**Creation method:** [From existing materials | From interviews | From observation | Combined]

### Recommended Verification Steps
1. **Self-test:** Have someone unfamiliar with the process follow this document step-by-step. Note where they get stuck.
2. **SME review:** Walk through with [Subject Matter Expert name/role]. Verify technical accuracy, completeness, and key points.
3. **Novice test:** Have a new team member attempt to follow the procedures. Note terminology gaps, assumed knowledge, and missing context.

⚠️ This document has NOT been verified through [self-test / SME review / novice test] as of [date].
Treat as [Current State — Pending Validation] until verification is completed.
```

---

### 2.5 Adoption Fitness Check

**Applies To:** evaluating whether a knowledge artifact will actually be used, matching document format to use context, preventing artifacts that add friction rather than reducing it

Before finalizing any artifact, apply the adoption fitness checklist:

| Check | Question | Fail Signal |
|-------|----------|-------------|
| **Use context** | Where will this be used? (desk, workstation, mobile, field, classroom) | Format doesn't match context (e.g., multi-page document for workstation use) |
| **Format match** | Is the format optimized for the use context? | Paragraphs where bullets/tables would serve better; text where diagrams would communicate faster |
| **Scannability** | Can the user find what they need in under 30 seconds? | No headings, no bold key terms, no visual hierarchy; user must read linearly to find information |
| **Competition** | Is this easier to use than the current alternative (memory, asking Bob, existing habit)? | The artifact adds friction rather than removing it |
| **Cognitive load** | Does the artifact minimize unnecessary mental effort? | User must translate, interpret, or cross-reference to get what they need |

**The adoption rule:** If the artifact is harder to use than NOT using it, redesign the format before delivering. Content accuracy does not compensate for poor usability.

**Common format fixes:**
- Dense paragraphs → bulleted lists or numbered steps
- Text descriptions of layouts/screens → annotated screenshots
- Linear prose for reference lookups → searchable tables
- Multi-page documents for point-of-work → single-page laminated cards
- Same format for all contexts → format matched to use environment

---

## 3 Quick Reference & Checklist Design

**Importance: IMPORTANT — The practitioner's tool at the point of work**

**Implements:** KA3 (Progressive Abstraction), TL1 (Audience-Appropriate Design)

### 3.1 The Checklist Manifesto Principle

**Applies To:** designing checklists and quick references, determining what to include vs exclude, applying cognitive load limits to checklist length

**Include only what gets missed. Exclude what practitioners already do.**

Source: Atul Gawande, *The Checklist Manifesto* (2009). Focus on "killer items" — steps most dangerous to skip yet sometimes overlooked by experienced practitioners.

**Design rules:**
- 5-9 items per pause point (cognitive load limit)
- 60-90 seconds max to complete a section
- If the checklist takes more than 5 minutes total, it's too long — split into sections or re-evaluate what's included

**The inclusion test for each item:** "Would a trained practitioner reliably do this without the reminder?" If YES → remove it. If NO → keep it.

**Example — what to EXCLUDE:**
- "Log into the system" (everyone does this)
- "Open the correct form" (obvious from context)
- "Save your work" (habitual for practitioners)

**Example — what to INCLUDE:**
- "Verify the order type is 'Standard' not 'Repair'" (easy to miss, different workflows)
- "Use your ERP username, NOT your Microsoft username" (common confusion point)
- "Check for material holds BEFORE releasing the order" (step that gets skipped under time pressure)

### 3.2 Quick Reference Template

**Applies To:** creating point-of-work reference cards, single-page job aids, laminated quick guides for workstation or field use

```markdown
# [Process Name] — Quick Reference

**For:** [Role/audience — must have completed training on [prerequisite]]
**Derived from:** [KB Name] v[Version]
**Last synced:** [Date]

## [Phase/Section 1]
- [ ] [Critical step or check — the one that gets missed]
- [ ] [Critical step or check]
- [ ] [Critical step or check]

## [Phase/Section 2]
- [ ] [Critical step or check]
- [ ] [Critical step or check]

## Common Mistakes
- [Mistake]: [What to do instead]
- [Mistake]: [What to do instead]

## If Something Goes Wrong
- [Symptom] → [Quick fix or who to contact]
```

### 3.3 Visual Work Instructions

**Applies To:** documenting physical workstation tasks, screen-based procedures needing annotated screenshots, shop floor or field work requiring posted instructions

For steps performed at a physical workstation or on a specific screen:

**Format:** Photo/screenshot + numbered callouts + minimal text
**Location:** Posted at the point of work (physical or digital)
**Design:** Large images, numbered steps overlaid on the image, maximum 7 steps per page

**Best practices (established — reference, don't reinvent):**
- One action per image frame
- Use arrows, circles, and highlights to draw attention
- Red for warnings/don'ts, green for correct actions
- Include the "why" only for steps where skipping causes problems
- Laminate or protect if used in shop floor environments

### 3.4 Other Extraction Types

**Applies To:** creating Job Instruction Cards for TWI training, troubleshooting guides with decision trees, SIPOC diagrams for strategic process views, process flow charts

**Job Instruction Card (TWI format):**
| Important Step | Key Point | Reason |
|---------------|-----------|--------|
| [What to do] | [How to do it / critical detail] | [Why it matters] |

One card per task. Used during training delivery (§7.2).

**Troubleshooting Guide:**
Decision tree format: Symptom → Check → If X → Do Y / If not X → Check Z.
Extracted from Detailed KB Section 4 (Troubleshooting).

**Decision Tree:**
Flowchart for branching decisions. Used when a process has multiple valid paths depending on conditions.

**SIPOC (Strategic view):**
| Supplier | Input | Process | Output | Customer |
|----------|-------|---------|--------|----------|
One row per major process step. Shows where this process fits in the larger system.

**Process Flow:**
Box-and-arrow diagram showing process areas and their connections. Strategic view for leadership and cross-functional understanding.

---

## 4 Strategic Process Documentation

**Importance: OPTIONAL — For organizations at maturity Level 2+ needing strategic views**

**Implements:** KA3 (Progressive Abstraction)

### 4.1 SIPOC Creation

**Applies To:** management reviews needing process overview, cross-functional alignment discussions, new leader onboarding to process areas

**When to create:** When stakeholders need to understand where a process fits without the operational detail. Useful for management reviews, cross-functional alignment, and new leader onboarding.

**Procedure:**
1. Start from the Detailed KB's core workflow
2. Identify the major process steps (5-8 typically)
3. For each step: Who supplies the inputs? What are the inputs? What's the output? Who receives it?
4. Map suppliers and customers (may be internal departments, external vendors, or systems)

### 4.2 Process Flow Mapping

**Applies To:** visualizing connections between multiple process areas, creating swim lane diagrams for cross-functional workflows, strategic process overview for leadership

**When to create:** When multiple processes connect and leadership needs to see the relationships.

**Procedure:**
1. Identify all process areas in scope
2. Map the flow between them (what triggers each, what output feeds the next)
3. Use standard flowchart notation or swim lanes for cross-functional views
4. Keep at strategic level — this is the neighborhood map, not the street-by-street directions

---

## 5 People Development Artifacts

**Importance: IMPORTANT — Connects knowledge to people capability**

**Implements:** KA4 (Empowerment Completeness), KA2 (Derivation Chain Integrity)

### 5.1 Cross-Training Matrix

**Applies To:** building team skill inventories, identifying training gaps, tracking employee progression through skill levels, workforce planning and succession

**Purpose:** Track who knows what across the team. Derived from Detailed KB major sections.

**Template:**

```
Process/Work Area: [Name]

Skill Key:
  0 = Untrained
  1 = In Training
  2 = Trained (can do with reference)
  3 = Seasoned (independent)
  4 = Trainer (can teach others)

                    | [Skill 1] | [Skill 2] | [Skill 3] | ...
--------------------|-----------|-----------|-----------|----
[Employee Name]     |     3     |     2     |     1     |
[Employee Name]     |     4     |     3     |     0     |
```

**Derivation rule:** Each skill column MUST map to a major section in the Detailed KB. If a skill appears in the matrix but has no corresponding KB section, the derivation chain is broken.

**Empowerment check:** Beyond Knowledge (the matrix), verify:
- **Tools:** Does each person have the tools listed in KB Section 8?
- **Responsibility:** Does the Job Description (§5.2) include these skills?
- **Accountability:** Are there quality checks or performance reviews covering these skills?
- **Authority:** Does the person have the authority to perform the work independently?

### 5.2 Job Description Derivation

**Applies To:** writing or updating job descriptions, aligning role responsibilities with documented skills, connecting job requirements to the knowledge base and training matrix

**Derivation:** Job Description responsibilities → Cross-Training Matrix skills → Detailed KB sections.

**Template structure:**

```markdown
# [Role Title] — Job Description

## Responsibilities
[Each responsibility maps to one or more Cross-Training Matrix skills]

- [Responsibility 1] — Maps to: [Skill from matrix]
- [Responsibility 2] — Maps to: [Skill from matrix]
...

## Required Qualifications
[Derived from the training requirements for Level 2+ skills in the matrix]

## Empowerment Components
- Tools required: [From KB Section 8]
- Training plan: [From Cross-Training Matrix progression path]
- Authority level: [What this role can approve/decide independently]
- Accountability: [How performance is measured for each responsibility]
```

### 5.3 Onboarding Program Design

**Applies To:** designing new employee onboarding plans, structuring training progression from orientation through proficiency, connecting onboarding activities to cross-training matrix skills

**Structure onboarding around the three learning levels:**

| Phase | Learning Level | Activities | Duration |
|-------|---------------|------------|----------|
| **Week 1: Setup & Context** | Awareness | Badge, computer, permissions, software setup. Company/team overview. Tours. Meet the team. | 1-2 days |
| **Weeks 1-2: Core Training** | Proficiency | Hands-on training on core workflow using Detailed KB. Follow TWI method (§7.2). | 1-2 weeks |
| **Weeks 3-4: Expanding** | Expanding | Branch procedures, edge cases. Shadowing experienced practitioners. | 1-2 weeks |
| **Ongoing: Deepening** | Proficiency/Expanding | Advanced skills per Cross-Training Matrix progression. | Continuous |

**Derivation:** Onboarding plan → Job Description responsibilities → Cross-Training Matrix skills → Detailed KB sections. Each onboarding activity should trace to a specific skill and KB section.

---

## 6 Assessment & Evaluation

**Importance: IMPORTANT — Verifies knowledge transfer effectiveness**

**Implements:** TL2 (Learning Objective Alignment), TL4 (Assessment Validity)

### 6.1 Assessment Design by Bloom's Level

**Applies To:** creating training assessments and quizzes, matching question types to learning objective levels, ensuring assessments test application rather than just recall

| Objective Level | Question Types | Example |
|----------------|---------------|---------|
| **Remember** | Multiple choice, matching, fill-in | "What is the first step in creating a shop order?" |
| **Understand** | Explain, describe, summarize | "Explain why the order type matters for the downstream workflow." |
| **Apply** | Scenario-based, guided task | "Given this scenario: a customer needs an expedited order. Walk through the steps you would take." |
| **Analyze** | Troubleshooting, root cause | "The system shows a material shortage. What are the possible causes and how would you investigate each?" |
| **Evaluate** | Decision-making, trade-off | "Two approaches could resolve this issue. Compare them and recommend which to use, explaining your reasoning." |
| **Create** | Build, design, develop | "Design a checklist for the monthly inventory reconciliation process." |

**Rule:** Match assessment level to learning objective level. If the objective says "apply independently," the assessment must include Apply-level items, not just Remember.

### 6.2 Training Effectiveness Evaluation (Kirkpatrick)

**Applies To:** measuring whether training programs achieved their goals, evaluating training ROI, choosing the appropriate evaluation level based on organizational capability

| Level | What It Measures | How to Measure | When |
|-------|-----------------|----------------|------|
| **1: Reaction** | Did the learner find the training useful? | Post-training survey | Immediately after |
| **2: Learning** | Did the learner acquire the knowledge/skill? | Assessment (§6.1) | End of training |
| **3: Behavior** | Is the learner applying it on the job? | Observation, quality metrics, manager feedback | 30-90 days after |
| **4: Results** | Did it improve organizational outcomes? | KPIs, error rates, productivity metrics | 3-6 months after |

Most organizations only measure Level 1 (satisfaction surveys). Measuring Level 2-3 is where training ROI becomes visible. Level 4 is ideal but requires organizational metrics infrastructure.

---

## 7 Training Delivery & Learning Levels

**Importance: IMPORTANT — Matches delivery method to learning need**

**Implements:** TL1 (Audience-Appropriate Design), TL2 (Learning Objective Alignment)

### 7.1 Training Value Optimization

**Applies To:** choosing the right training delivery method, matching investment to return, avoiding over-training or under-training for different skill needs

**Match the method to the return. Not maximum intensity for everything.**

| Need | Method | Investment | Return |
|------|--------|------------|--------|
| Learn it from scratch | Hands-on with mentor, TWI method | High | High — person can't work without it |
| Build on what they know | Demonstration + practice on new parts | Moderate | Moderate — expanding capability |
| Periodic reminder | E-learning, email, refresher meeting | Low | Maintenance — preventing skill decay |

**The anti-patterns:**
- Classroom training for something that only needs an email reminder = waste
- An email reminder for something that needs hands-on practice = undertrained people making mistakes
- Same training intensity for everyone regardless of experience = disrespecting people's time

### 7.2 TWI Job Instruction Method

**Applies To:** training someone on a hands-on operational task, structured skill transfer from experienced to novice practitioner, progressive 4-step teaching methodology

The established method for training someone on a specific task. Four-step progressive transfer:

**Step 1: Prepare the learner**
- Put them at ease
- State the job
- Find out what they already know
- Get them interested in learning

**Step 2: Present the operation**
- Show them how to do it, explaining ONE thing at a time:
  - First pass: Important steps only
  - Second pass: Important steps AND key points
  - Third pass: Important steps, key points, AND reasons

**Step 3: Try out performance**
- Have the learner do the job
- Have them explain the important steps as they work
- Have them explain the key points
- Have them explain the reasons
- Continue until YOU (the trainer) are confident they know it

**Step 4: Follow up**
- Put them on their own
- Designate who to go to for help
- Check frequently, then taper off
- Encourage questions

**Source:** Training Within Industry (1940s), adapted by Toyota. Proven effective for 80+ years.

### 7.3 Best Practice Discovery (Referenced Method)

**Applies To:** identifying the current best approach before documenting a process, comparing different practitioner methods, building standard work from multiple existing approaches

**This is a process step, not a domain principle.**

Before documenting a process, identify the current best practice:

1. **Gather all existing approaches** — different people may do the same task differently
2. **Test and compare** — which approach produces the best results with the least waste?
3. **Combine the best elements** — the best practice may be a hybrid
4. **Validate with practitioners** — build WITH them, not FOR them
5. **Address anchor bias** — "that's how we've always done it" is not a reason to continue

**Reference:** Lean/Six Sigma improvement methodology. This domain does not govern the improvement methodology itself — only the documentation of its results.

### 7.4 Implementation Context for Human Leaders

**Applies To:** rolling out knowledge management systems in an organization, gaining buy-in from practitioners, addressing resistance to process documentation, change management for KM&PD initiatives

**This section provides change management guidance for humans implementing KM&PD systems. It is advisory context, not AI governance.**

When building a knowledge management and people development system, the technical side (Manage Process) is only half the work. The human side (Lead People) determines whether the system is adopted or ignored:

1. **Context before mechanics.** Help people understand WHAT you're trying to accomplish and WHY before diving into the HOW.

2. **Build WITH people, not FOR them.** Standard work created with practitioners is adopted. Standard work imposed on practitioners is resisted. Include the people doing the work in the documentation process.

3. **Don't create fear.** When documenting processes, people worry: "Are they documenting my job so they can replace me?" Address this directly. Make clear: this is about organizational resilience and their development, not elimination.

4. **Address anchor bias.** "That's how we've always done it" is the enemy of improvement. When establishing best practices, start with a clean slate.

5. **Use the parking lot.** People have grievances not directly related to the task. Capture them, route them to the right people, and show the employee they were heard. You sometimes have to let them air out before you get their best contribution.

6. **Lead THEN manage.** Address the human side first, then the process side. If people aren't bought in, the best documentation in the world won't be followed.

**AI role:** When the AI assists someone in building a KM&PD system, it should remind them of these considerations — not just generate documents, but prompt: "Have you gotten buy-in from the people doing this work? Are you building this WITH them?"

---

## 8 Scaffolded Complexity

**Importance: IMPORTANT — Ensures knowledge content follows a learnable progression**

**Implements:** KA1 (Single Source Architecture — scaffolded structure within the KB)

> **Origin:** Demoted from PD3 (Scaffolded Complexity principle) in principles v1.3.0. The concept is procedural — it describes HOW to organize content, not WHAT governance applies. KA1 now includes a validation criterion for scaffolded complexity; this method provides the procedure.

**Constitutional Basis:** `Structural Foundations` + `Atomic Task Decomposition`

**Addresses:** KM-F1 (Information Dump) — undifferentiated walls of text without scaffolding

### 8.1 The Scaffolding Procedure

**Applies To:** organizing knowledge content in learnable progression, structuring detailed KBs and training materials by complexity, applying foundation-first content architecture

When organizing knowledge content (Detailed KBs, training materials, onboarding programs), structure by scaffolded complexity:

1. **Identify the core workflow** — the 80% of daily work that covers the most common path
2. **Start with foundations** — what does someone need to know FIRST to make sense of everything else?
3. **Build progressively** — add common variations and branching procedures after core is established
4. **Layer in advanced topics** — edge cases, exception handling, and complex scenarios come after the reader has a solid foundation
5. **Ask the teaching question** — "If you were training a new person, what would you teach them first? What comes after that?" Use the answer to validate the structure.
6. **Apply the MVP approach** — document core first, expand progressively. The reader can stop at any point and have a coherent (if incomplete) understanding.

### 8.2 Scaffolding Validation

**Applies To:** verifying that knowledge content follows a learnable progression, checking prerequisite ordering, validating that readers can stop at any point with coherent understanding

After organizing content, verify:

- [ ] Content begins with foundational concepts before advanced topics
- [ ] Prerequisites are clearly stated before dependent content
- [ ] The reader can stop at any point and have a coherent (if incomplete) understanding
- [ ] The structure mirrors the natural learning path for the role

### 8.3 When Content Arrives Out of Order

**Applies To:** processing user-provided content that arrives in non-logical order, restructuring edge-case-first content into foundation-first architecture, handling stream-of-consciousness knowledge capture

When the user provides content in a non-scaffolded order (e.g., starting with edge cases before core workflow):

1. Accept the content as-is — capture everything
2. Propose a restructured order that follows the scaffolding procedure
3. Confirm the restructured order with the user before reorganizing
4. The user may have valid reasons for a different order — defer to their judgment if they explain why

---

## Appendix A: Maturity Model Reference

See principles document §Implementation Guidance for the full 6-level maturity model (Tribal → Ad Hoc → Structured → Extracted → Managed → Optimizing).

AI-driven maturity assessment deferred to v2. In v1, present the model and let the user self-identify.

---

## Appendix B: Evidence Base Quick Reference

| Source | What It Provides | Use When |
|--------|-----------------|----------|
| **TWI Job Instruction** | 4-step training method | Teaching someone a hands-on task (§7.2) |
| **Bloom's Taxonomy** | Learning objective levels | Writing objectives (§6.1) or assessments (§6.1) |
| **Kirkpatrick** | Training effectiveness levels | Evaluating whether training worked (§6.2) |
| **Dreyfus Model** | Skill acquisition stages | Determining audience level (§7.1) |
| **Checklist Manifesto** | Checklist design discipline | Creating Quick References (§3.1) |
| **Mayer's Multimedia** | Cognitive load principles | Deciding text vs. visual (§2.3) |
| **Lean/Six Sigma** | Waste elimination, variability reduction | Writing clean documentation (§2.1) |
| **Luftig/BPE** | 5-component empowerment model | Building people artifacts (§5.1) |

---

## Situation Index

For quick routing of common scenarios to relevant methods:

| Situation | Relevant Sections |
|-----------|-------------------|
| "Building a knowledge base from scratch" | §1.1 (First Interaction), §1.2 (Maturity Assessment), §1.3 (KB Scaffold), §2.1 (Design Principles), §2.2 (Build Approach) |
| "Creating a checklist or quick reference" | §3.1 (Checklist Manifesto Principle), §3.2 (Quick Ref Template), §1.4 (Derivation Tracking), §2.5 (Adoption Fitness) |
| "Documenting a process someone described to me" | §2.2 (Build Approach), §2.3 (Step Writing Standards), §2.4 (Verification Recommendation), §1.5 (Knowledge Conflict Prevention) |
| "Building visual work instructions" | §3.3 (Visual Work Instructions), §2.3 (Step Writing — visuals), §2.5 (Adoption Fitness) |
| "Creating a cross-training matrix" | §5.1 (Cross-Training Matrix), §1.4 (Derivation Tracking), KA4 (Empowerment Completeness) |
| "Writing a job description" | §5.2 (Job Description Derivation), §5.1 (Cross-Training Matrix — source), KA4 (Empowerment Completeness) |
| "Designing an onboarding program" | §5.3 (Onboarding Program Design), §7.1 (Training Value Optimization), §7.2 (TWI Method) |
| "Creating a training assessment or quiz" | §6.1 (Bloom's Assessment Design), §6.2 (Kirkpatrick Evaluation), TL4 (Assessment Validity) |
| "Training someone on a hands-on task" | §7.2 (TWI Job Instruction Method), §7.1 (Training Value Optimization), §3.4 (Job Instruction Card) |
| "Updating existing documentation" | §1.6 (KB Update Procedure), §1.4 (Derivation Chain Tracking), §1.5 (Knowledge Conflict Prevention) |
| "Creating a SIPOC or process flow" | §4.1 (SIPOC Creation), §4.2 (Process Flow Mapping), KA3 (Progressive Abstraction) |
| "Getting buy-in from the team" | §7.4 (Implementation Context for Human Leaders), §7.3 (Best Practice Discovery) |
| "Assessing organizational maturity" | §1.2 (Maturity Self-Assessment), Appendix A (Maturity Model Reference) |
| "Making an artifact people will actually use" | §2.5 (Adoption Fitness Check), QA2 (Artifact Adoption Fitness), §3.1 (Checklist Manifesto) |
| "Process involves safety or regulatory requirements" | §2.4 (Verification Recommendation), QA1 (Safety & Compliance Completeness) |
| "Engaging narrative structure in knowledge content" | §2.1 (Detailed KB should tell a story), Storytelling domain A-Series (Audience), Storytelling domain ST-Series (Structure Principles) |
| "Creating a troubleshooting guide or decision tree" | §3.4 (Other Extraction Types), §1.3 (KB Scaffold — Section 4: Troubleshooting) |
| "Organizing content in learnable order" | §8.1 (The Scaffolding Procedure), §8.2 (Scaffolding Validation), §8.3 (When Content Arrives Out of Order) |

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.2.0 | 2026-03-29 | Added §8 Scaffolded Complexity (demoted from PD3 principle). Updated principle references: TL3+QA1 merged → QA1 (Safety & Compliance Completeness), PD2 merged into KA3. |
| 1.1.0 | 2026-03-25 | Added Situation Index (17 routing entries). Added storytelling domain cross-reference in situation index. |
| 1.0.0 | 2026-03-25 | Initial release. 7 sections covering both pillars (Manage Process: §1-§4, Lead People: §5-§7). Templates for Detailed KB, Quick Reference, Cross-Training Matrix, Job Description, Onboarding. TWI Job Instruction method. Kirkpatrick evaluation framework. Maturity model as reference. Implementation Context for Human Leaders as advisory appendix. |

---

*Version 1.2.0*
*Derived from: KM&PD Domain Principles v1.3.0, Constitution v2.6.0, AI Coding Methods v2.27.0*
*Framework: Jason Collier's Knowledge Management & People Development Framework (novel synthesis)*
*Access: Proprietary — see framework owner for access*
