# Storytelling Context Management Method v1.0.0
## Managing Narrative Persistence Beyond AI Context Windows

> **SYSTEM INSTRUCTION FOR AI AGENTS:**
> This method governs HOW to maintain story coherence when narrative scope exceeds AI context window capacity. It implements the constitutional principle `meta-core-context-engineering` for the storytelling domain.

---

## 1 The Context Threshold Problem

### Why This Method Exists

AI language models have **advertised** context windows of 100K-200K tokens, but **effective** context is much smaller. Research from Stanford and Meta AI ("Lost in the Middle," 2023) demonstrates:

- Performance degrades significantly when relevant information is positioned in the **middle** of context
- Attention follows a **U-shaped curve** — models recall best from the beginning and end
- Effective reliable context is approximately **32K tokens** before quality degradation begins
- Larger windows often waste context on irrelevant details rather than improving coherence

**Implication for Storytelling:** A novel of 80,000 words (~106K tokens) cannot fit in effective context. Even a novella of 30,000 words (~40K tokens) exceeds reliable attention. External reference documents ("Story Bibles") become **mandatory** for maintaining consistency.

### The Math

| Content Type | Word Range | Token Estimate | Context Strategy |
|--------------|------------|----------------|------------------|
| Social media post | 50-500 | 65-650 | In-context sufficient |
| Flash fiction | <1,000 | <1,300 | In-context sufficient |
| Short story | 1,000-7,500 | 1,300-10,000 | In-context likely sufficient |
| Novelette | 7,500-17,500 | 10,000-23,000 | **Threshold zone** — recommend external reference |
| Novella | 17,500-40,000 | 23,000-53,000 | **External reference required** |
| Novel | 40,000-100,000+ | 53,000-133,000+ | **External reference mandatory** |
| Series | Multiple novels | 200K+ | **External reference + series bible essential** |

**The Threshold Rule:**
- **Under 10,000 words:** AI can manage in-context with careful prompting
- **10,000-25,000 words:** External reference **recommended** for consistency
- **Over 25,000 words:** External reference **required** — in-context alone will cause continuity errors

---

## 2 The Story Bible Architecture

### Three-Tier Memory Model

Adapted from the AI Coding Methods memory architecture (which maps to cognitive memory types):

| Memory Type | File | Purpose | Update Frequency |
|-------------|------|---------|------------------|
| **Working Memory** | `STORY-SESSION.md` | Current scene, active characters, immediate tension | Every session |
| **Semantic Memory** | `STORY-BIBLE.md` | Permanent facts: characters, world rules, plot architecture | When facts established |
| **Episodic Memory** | `STORY-LOG.md` | What happened: scene summaries, chapter synopses | After each chapter/act |

### Why Three Tiers?

**Working Memory (Session State):**
- Prevents "where was I?" confusion when resuming
- Tracks emotional momentum that shouldn't reset
- Includes only what's needed for the CURRENT scene

**Semantic Memory (Story Bible):**
- Facts that **never change** once established
- Character eye color doesn't shift mid-story
- Magic system rules don't contradict themselves
- Loaded selectively (only relevant characters for current scene)

**Episodic Memory (What Happened):**
- Chronological record of events
- Enables "Previously on..." summaries
- Supports time-skip transitions
- Compressed summaries, not full text

---

## 3 Reference Items to Track

### Tier 1: MANDATORY (Track for Any Project Over 10K Words)

#### Characters
| Field | Purpose | Example |
|-------|---------|---------|
| **Name + Aliases** | Trigger recognition | "Elena, Lena, Dr. Vasquez" |
| **Physical Description** | Visual consistency | "5'6", black curly hair, scar on left palm" |
| **Core Motivation** | Drives decisions | "Prove she deserves her father's legacy" |
| **Speech Pattern** | Voice distinction | "Formal vocabulary, avoids contractions, uses medical metaphors" |
| **Relationships** | Interaction dynamics | "Mentor to Jake, rival to Marcus, fears Dr. Chen" |
| **Current State** | Working memory | "Last seen: injured, hiding in warehouse, unaware of betrayal" |

#### Settings
| Field | Purpose | Example |
|-------|---------|---------|
| **Name + Aliases** | Location recognition | "The Hollow, Old Henderson Place" |
| **Sensory Anchors** | Immersive consistency | "Smell of pine and diesel, constant wind, unreliable cell signal" |
| **Significance** | Narrative function | "Where Elena's father disappeared; climax location" |

#### Timeline
| Field | Purpose | Example |
|-------|---------|---------|
| **Story Calendar** | Temporal consistency | "Day 1 = March 15, 2024; story spans 3 weeks" |
| **Character Ages** | Age-appropriate behavior | "Elena: 34 at story start, turns 35 in Ch. 12" |
| **Key Events** | What happened when | "Day 3: Warehouse fire. Day 7: Jake's betrayal revealed" |

### Tier 2: RECOMMENDED (Track for Projects Over 25K Words)

#### World Rules
| Field | Purpose | Example |
|-------|---------|---------|
| **Magic/Technology Systems** | Consistency enforcement | "Telekinesis requires line of sight; exhaustion after 3 uses" |
| **Social Structures** | Cultural consistency | "Eldest child inherits; women control finances" |
| **Physics/Limitations** | Boundary enforcement | "FTL travel takes 1 week subjective, 1 year objective" |

#### Plot Architecture
| Field | Purpose | Example |
|-------|---------|---------|
| **Promises Made** | Payoff tracking | "Opening implies Elena will confront father's killer" |
| **Foreshadowing Planted** | Callback reference | "Ch. 2: Jake's hesitation at mention of Dr. Chen (reveals Ch. 18)" |
| **Subplots Active** | Thread management | "Romance arc: Elena/Marcus — currently at 'denial' stage" |
| **Unresolved Questions** | Reader expectations | "Who sent the warning letter? (answered Ch. 15)" |

#### Style Guide
| Field | Purpose | Example |
|-------|---------|---------|
| **Spelling Choices** | Consistency | "okay (not OK), email (not e-mail)" |
| **Formatting Rules** | Visual consistency | "Thoughts in italics, flashbacks in present tense" |
| **POV Rules** | Perspective discipline | "Third limited Elena; Ch. 7 and 14 are Jake POV" |

### Tier 3: OPTIONAL (Track for Series or Complex Worlds)

#### Extended Cast
- Secondary character sheets (abbreviated)
- Character relationship matrix
- Family trees / organizational charts

#### World Encyclopedia
- History timeline (backstory events)
- Geography / maps
- Languages / naming conventions
- Cultural practices
- Technology/magic progression

#### Series Continuity
- Cross-book character arcs
- Unresolved threads carried forward
- Reader knowledge state per book
- Retcon tracking (if any)

---

## 4 Story Bible Template

### Minimal Template (10K-25K Words)

```markdown
# Story Bible: [Project Name]
**Genre:** [Genre/Subgenre]
**Framework:** [Hero's Journey / Kishotenketsu / Problem-Solution / etc.]
**POV:** [First / Third Limited / Omniscient]
**Timeline:** [Start date] to [End date]

---

## Characters

### [Protagonist Name]
- **Aliases:** [Nicknames, titles, other names used]
- **Appearance:** [2-3 key visual details]
- **Voice:** [Speech pattern, vocabulary level, verbal tics]
- **Want:** [External goal]
- **Need:** [Internal growth required]
- **Key Relationships:** [Name: relationship type]
- **Current State:** [Last seen: location, emotional state, what they know]

### [Antagonist/Major Characters...]
[Same fields]

---

## Settings

### [Primary Location]
- **Aliases:** [Other names used for this place]
- **Sensory:** [Sight, sound, smell anchors]
- **Function:** [Why scenes happen here]

---

## Rules
- [Any world-specific rules that must remain consistent]

---

## Timeline
- **Character Ages:** [Name: age at story start]

| Day/Chapter | Event | Character Impact |
|-------------|-------|------------------|
| [When] | [What] | [Who changes how] |
```

### Full Template (25K+ Words)

```markdown
# Story Bible: [Project Name]
**Version:** [Increment when major facts change]
**Last Updated:** [Date]

---

## 1 Story Foundation (IMMUTABLE)

### Premise
[One sentence: Who wants what, and what stands in the way?]

### Theme
[What is this story ultimately ABOUT? The argument it makes?]

### Core Promise
[What does the opening make readers expect? This MUST be delivered.]

### Stakes
[What does protagonist lose if they fail?]

---

## 2 Characters

### Protagonist: [Name]

#### Identity
- **Full Name:** [Including aliases, nicknames]
- **Age:** [At story start]
- **Appearance:** [Height, build, hair, eyes, distinguishing marks]
- **Voice:** [Speech patterns, vocabulary, verbal tics, sample dialogue]

#### Psychology
- **Want (External):** [Conscious goal]
- **Need (Internal):** [Unconscious growth required]
- **Ghost (Wound):** [Past event driving current behavior]
- **Lie Believed:** [False belief they must overcome]

#### Arc
- **Starting State:** [Who they are at opening]
- **Ending State:** [Who they become by climax]
- **Key Transformation Moment:** [Scene where change crystallizes]

#### Relationships
| Character | Relationship | Dynamic |
|-----------|--------------|---------|
| [Name] | [Type] | [How they interact, tension source] |

#### Current State (Working Memory)
- **Last Scene:** [What happened]
- **Emotional State:** [Current mood/mindset]
- **Knowledge:** [What they know/don't know]
- **Physical State:** [Injuries, location, resources]

---

### [Additional Character Sheets...]

---

## 3 World

### Settings

#### [Location Name]
- **Aliases:** [Other names used]
- **Sensory Anchors:** [Smell, sound, texture, temperature]
- **Visual Key:** [What it looks like]
- **Narrative Function:** [Why scenes happen here]
- **Associated Characters:** [Who frequents this place]

### Rules

#### [System Name: Magic/Technology/Social]
- **What It Does:** [Capabilities]
- **Limitations:** [What it CANNOT do]
- **Cost:** [What using it requires]
- **Exceptions:** [Edge cases, if any]

---

## 4 Plot Architecture

### Structure
- **Framework:** [Hero's Journey / Three-Act / Kishotenketsu / etc.]
- **Act Breakdown:** [Where act breaks fall]

### Key Plot Points

| Plot Point | Chapter/Scene | What Happens | Promise/Payoff |
|------------|---------------|--------------|----------------|
| Opening Hook | Ch. 1 | [Event] | Promise: [What reader expects] |
| Inciting Incident | Ch. [X] | [Event] | [Character impact] |
| First Pinch Point | Ch. [X] | [Event] | [Stakes raised] |
| Midpoint | Ch. [X] | [Event] | [Reversal/revelation] |
| Second Pinch Point | Ch. [X] | [Event] | [Stakes raised] |
| Dark Night | Ch. [X] | [Event] | [All seems lost] |
| Climax | Ch. [X] | [Event] | [Core conflict resolved] |
| Resolution | Ch. [X] | [Event] | Payoff: [Promise delivered] |

### Subplots

| Subplot | Characters | Status | Resolution Chapter |
|---------|------------|--------|-------------------|
| [Name] | [Who] | [Active/Resolved] | Ch. [X] |

### Foreshadowing Registry

| Setup | Chapter Planted | Payoff | Chapter Delivered |
|-------|-----------------|--------|-------------------|
| [Hint] | Ch. [X] | [Revelation] | Ch. [Y] |

### Open Questions (Reader Expectations)

| Question | Raised In | Answered In | Answer |
|----------|-----------|-------------|--------|
| [Mystery] | Ch. [X] | Ch. [Y] | [Resolution] |

---

## 5 Style Guide

### Voice
- **Tense:** [Past / Present]
- **POV:** [First / Third Limited / Omniscient]
- **POV Characters:** [Who gets POV chapters]
- **Narrative Distance:** [Close / Medium / Distant]

### Formatting
- **Thoughts:** [Italics / Quotes / Unmarked]
- **Flashbacks:** [Tense shift / Section break / etc.]
- **Time Jumps:** [How indicated]

### Spelling/Usage
| Choice | NOT | Reason |
|--------|-----|--------|
| [okay] | [OK] | [Style preference] |

---

## 6 Timeline

### Story Calendar
- **Day 1:** [Real-world date if applicable]
- **Duration:** [How long story spans]

### Character Ages
| Character | Age at Start | Age Changes | Notes |
|-----------|--------------|-------------|-------|
| [Name] | [Age] | [If birthday occurs: Ch. X] | [Relevant age notes] |

### Chronological Events
| Story Day | Chapter | Event | Characters Present |
|-----------|---------|-------|-------------------|
| [Day] | Ch. [X] | [Event] | [Who] |

---

## 7 Session State (Working Memory)

*Updated each session. Overwritten, not appended.*

### Current Position
- **Chapter/Scene:** [Where we are]
- **POV Character:** [Whose head we're in]
- **Last Line Written:** [Exact quote for continuity]

### Active Tension
- **Immediate Conflict:** [What's happening NOW]
- **Scene Goal:** [What POV character wants this scene]
- **Obstacles:** [What's preventing it]

### Character States (This Scene)
| Character | Location | Emotional State | Knowledge State |
|-----------|----------|-----------------|-----------------|
| [Name] | [Where] | [Feeling] | [What they know/don't] |

### Unresolved From Last Session
- [ ] [Thread to pick up]
- [ ] [Decision to make]

---
```

---

## 5 Context Loading Protocol

### The "Lost in the Middle" Mitigation

Based on the research, follow this loading order to maximize attention:

```
[START OF CONTEXT — HIGH ATTENTION]
1. Current task instructions (what to write now)
2. Session state (where we are, immediate scene context)
3. Active character sheets (only characters IN this scene)

[MIDDLE OF CONTEXT — LOW ATTENTION]
4. Relevant world rules (only if applicable to scene)
5. Recent plot summary (last 2-3 chapters compressed)

[END OF CONTEXT — HIGH ATTENTION]
6. Style guide / voice notes
7. Specific constraints for this scene
8. The actual prompt/request
```

### Selective Loading Rules

**DO Load:**
- Characters appearing in the current scene
- Settings where current scene takes place
- Rules being used in current scene
- Recent events characters would reference
- Style guide for consistency

**DO NOT Load:**
- Full character sheets for characters not in scene
- Historical events not referenced
- World-building not relevant to scene
- Full chapter text (use summaries)
- Resolved subplots

### Token Budget Guideline

For optimal performance, keep loaded context under 15K tokens:

| Category | Token Budget | What to Include |
|----------|--------------|-----------------|
| Task Instructions | 500-1,000 | What to write, constraints |
| Session State | 500-1,000 | Current position, immediate context |
| Active Characters | 2,000-4,000 | Only characters in scene (500-800 each) |
| Settings | 500-1,000 | Current location only |
| Recent Plot | 1,000-2,000 | Last 2-3 chapters summarized |
| Rules | 500-1,000 | Only if relevant |
| Style Guide | 500-1,000 | Voice, formatting |
| **Generation Space** | **5,000-8,000** | Reserved for actual output |

---

## 6 When to Create New Reference Items

### Decision Framework

Create a new reference entry when:

1. **Named Entity Test:** Does this have a proper name that will recur?
   - Yes → Create entry
   - No → Probably not needed

2. **Recurrence Test:** Will this appear in 3+ scenes?
   - Yes → Create entry
   - No → Mention in scene notes only

3. **Consistency Test:** Does this have details that must remain consistent?
   - Yes → Create entry
   - No → Handle ad-hoc

4. **Relationship Test:** Does this interact with tracked entities?
   - Yes → Create entry (or add to existing entry's relationships)
   - No → Evaluate based on other tests

### Reference Item Tiers

| Tier | Criteria | Entry Depth |
|------|----------|-------------|
| **Primary** | POV characters, main antagonist, primary setting | Full template |
| **Secondary** | Supporting characters, recurring locations | Abbreviated (name, key traits, relationship to primary) |
| **Tertiary** | One-scene characters, mentioned-only places | Single line in "Minor Elements" list |
| **Ambient** | Background details, unnamed characters | No entry needed |

### Adding Items Mid-Project

When a new element emerges during writing:

1. **Immediate:** Add to Session State as "New element introduced: [brief note]"
2. **End of session:** Evaluate against Decision Framework
3. **If entry needed:** Create at appropriate tier, back-fill any established facts
4. **Update cross-references:** Add to relevant character/setting relationship fields

---

## 7 Platform-Specific Adaptations

### Long-Form (Novels, Series)

- Use **full Story Bible template**
- Maintain **chapter-by-chapter episodic log**
- **Summarize previous acts** rather than loading full text
- Consider **per-POV character state** if multiple viewpoints

### Medium-Form (Novelettes, Novellas)

- Use **minimal Story Bible template**
- **Scene summaries** instead of chapter summaries
- Load **all characters** if cast is small (<6 major)

### Short-Form (Short Stories, Flash Fiction)

- **No separate Story Bible needed** if under 10K words
- Use **in-prompt character notes** instead
- Example: "Characters: Maya (protagonist, 28, anxious, wants approval), Jon (her brother, 32, dismissive)"

### Social Media / Very Short Form

- **No Story Bible** — content fits in single context
- For **series of posts** (thread, multi-part), use minimal tracking:
  - Hook established
  - Key points covered
  - Call-to-action planned

### Serialized Content (Web Fiction, Episodes)

- Treat like **short-form per episode** PLUS **series bible**
- Track **reader knowledge state** (what has been revealed)
- Maintain **"Previously on..." summaries** for each episode

---

## 8 Voice Preservation Integration

When AI assists a human storyteller (vs. generating independently), add this section to Story Bible:

### Voice Fingerprint

```markdown
## Voice Preservation

### Authentic Patterns
- **Sentence Structure:** [Short/long tendency, fragments used?]
- **Vocabulary Level:** [Simple/complex, jargon used?]
- **Rhythm:** [Staccato/flowing, paragraph length tendency]
- **Signature Phrases:** [Recurring expressions unique to this author]

### Sample Passages
[2-3 short excerpts that exemplify the author's authentic voice]

### What to Preserve
- [Specific element 1]
- [Specific element 2]

### What AI May Enhance (With Permission)
- [Area where assistance is welcome]

### What AI Must NOT Change
- [Non-negotiable voice elements]
```

---

## 9 Recovery Protocol

### If Story Bible Becomes Inconsistent

1. **Identify conflict:** Note what contradicts what
2. **Determine canon:** Which version is "true" for the story?
3. **Update Bible:** Correct the entry
4. **Track change:** Note in changelog what was corrected and why
5. **Check propagation:** Does this conflict appear in written text?
6. **Decide remedy:** Revise text, or retcon Bible to match text?

### If Context Overflows Mid-Scene

1. **Save immediately:** Export current session state
2. **Compress:** Summarize what's been written this session
3. **Reset context:** Start fresh session with:
   - Updated session state
   - Relevant Bible entries
   - Summary of recent output
4. **Continue:** Resume from documented position

### If Resuming After Long Gap

1. **Read Session State:** Where were we?
2. **Read Episodic Log:** What's happened in the story?
3. **Scan Recent Chapters:** (summaries, not full text)
4. **Load Relevant Characters:** Who's active in current arc?
5. **Verify Voice:** Re-read voice fingerprint or sample passages

---

## 10 Governance Integration

### Principle Mapping

This method implements:

| Principle | How Implemented |
|-----------|-----------------|
| `meta-core-context-engineering` | Three-tier memory architecture |
| `meta-operational-minimal-relevant-context` | Selective loading protocol |
| `coding-context-context-window-management` | Token budgets, overflow recovery |
| `multi-architecture-context-engineering-discipline` | Write/Select/Compress/Isolate strategies |
| `E1: Human Voice Preservation` | Voice Fingerprint section |

### Before Writing Sessions

Query governance for relevant storytelling principles based on current task:
- Generating new content → A-Series, ST-Series, C-Series
- Editing existing content → E1 (Voice Preservation)
- Platform-specific content → M-Series
- Emotional/persuasive content → E2 (Persuasion-Manipulation Boundary)

---

## 11 Auto-Tracking Protocol

### Why Auto-Tracking?

Manual Story Bible maintenance is tedious and error-prone. Writers forget to update entries, facts drift from source text, and the reference material becomes stale. **Auto-tracking** means the AI automatically extracts and maintains reference material as you write, reducing cognitive overhead while ensuring accuracy.

Tools like [Mythril](https://www.mythril.io/), [Novelcrafter](https://www.novelcrafter.com/), and [Sudowrite](https://www.sudowrite.com/) have pioneered this approach. This protocol adapts their patterns for AI-assisted writing without specialized software.

### Extraction Timing: When to Update

Three trigger types determine when to extract/update Story Bible entries:

| Trigger Type | When It Fires | What Gets Updated |
|--------------|---------------|-------------------|
| **Session-Based** | End of every writing session | Session State (mandatory), new entities flagged |
| **Milestone-Based** | Scene/chapter completion, act breaks | Episodic Log, character arcs, plot points |
| **Token-Based** | At ~60% context consumption | Proactive compression, entity extraction |

#### Recommended Cadence

```
DURING SESSION:
├── Continuous: Flag new named entities as they appear
├── Scene boundary: Quick entity check, state snapshot
└── 60% context: Proactive extraction before overflow

END OF SESSION (MANDATORY):
├── Session State: Current position, active tension, character states
├── Entity Review: Confirm new entities added to Bible
├── Episodic Update: Summarize what happened this session
└── Consistency Check: Flag any potential conflicts

MILESTONE (Chapter/Act Complete):
├── Full character arc review
├── Plot point verification
├── Foreshadowing registry update
├── Subplot status update
└── Version snapshot (see §12)
```

### What to Auto-Extract

#### Always Extract (Automatic)

| Element Type | Extraction Trigger | Destination |
|--------------|-------------------|-------------|
| **Named Characters** | First appearance with proper noun | Characters section |
| **Named Locations** | First description or scene set there | Settings section |
| **Stated Rules** | "The magic only works when..." | Rules section |
| **Key Events** | Major plot developments | Episodic Log |
| **Time Markers** | "Three days later...", dates | Timeline |
| **Relationship Changes** | Betrayal, alliance, romance milestone | Character relationships |

#### Extract on Confirmation (Semi-Automatic)

| Element Type | Prompt User? | Why |
|--------------|--------------|-----|
| **Character Traits** | Yes | May be situational vs. permanent |
| **Backstory Reveals** | Yes | Confirm this is "canon" not speculation |
| **Rule Exceptions** | Yes | Exceptions need explicit acknowledgment |
| **Subplot Introduction** | Yes | Distinguish from minor threads |

### Auto-Extraction Procedure

At each extraction trigger:

```
1. SCAN recent output for:
   - New proper nouns (potential characters/places)
   - Physical descriptions attached to known characters
   - Statements about world rules or limitations
   - Time indicators or chronological markers
   - Relationship-defining moments

2. CATEGORIZE each finding:
   - NEW ENTITY: Needs Story Bible entry
   - UPDATE: Modifies existing entry
   - CONFLICT: Contradicts existing entry (flag for §12)
   - TRANSIENT: Session-relevant only, no Bible entry

3. FOR NEW ENTITIES:
   - Apply Decision Framework (§6) to determine tier
   - Create entry at appropriate depth
   - Cross-reference with existing entries

4. FOR UPDATES:
   - Locate existing entry
   - Append or modify (not overwrite without tracking)
   - Log change in entry's changelog field

5. FOR CONFLICTS:
   - Flag immediately
   - Do not auto-resolve—requires human decision
   - Queue for revision management (§12)
```

### Session End Protocol (Auto-Tracking Version)

Every session must end with this sequence:

```markdown
## Session End Checklist

### 1. Session State Update
- [ ] Current chapter/scene position
- [ ] Last line written (exact quote)
- [ ] Active POV character
- [ ] Immediate tension/conflict
- [ ] Character emotional states (those in scene)

### 2. Entity Extraction Review
- [ ] New characters introduced? → Add to Bible
- [ ] New locations introduced? → Add to Bible
- [ ] New rules established? → Add to Bible
- [ ] Existing entries need updates? → Update with changelog

### 3. Episodic Log Update
- [ ] One-paragraph summary of session events
- [ ] Key plot developments noted
- [ ] Character changes documented

### 4. Conflict Check
- [ ] Any contradictions with Bible entries?
- [ ] Any timeline inconsistencies?
- [ ] Any character behavior OOC without explanation?
→ If yes to any: Flag for revision management

### 5. Next Session Prep
- [ ] What scenes are next?
- [ ] Which characters need to be loaded?
- [ ] Any unresolved questions to address?
```

---

## 12 Revision Management Protocol

### The Revision Problem

Stories change. You write Chapter 5 and realize the betrayal should have happened earlier. You revise Chapter 3, and now:
- The Story Bible is wrong (it reflects old Chapter 3)
- Chapters 4-5 may have continuity issues
- Character states are inconsistent

Revision management ensures changes **propagate correctly** through both the story text AND the reference material.

### Version Control for Narrative

Adapted from software development patterns (Git), but designed for prose:

#### Key Concepts

| Concept | Software Analogy | Narrative Application |
|---------|------------------|----------------------|
| **Commit** | Save point with message | Snapshot of story + bible at milestone |
| **Branch** | Parallel development line | "What if" alternate plot exploration |
| **Merge** | Combine branches | Integrate chosen plot direction |
| **Diff** | Show changes | Compare drafts side-by-side |
| **Rollback** | Undo to previous state | Restore earlier version when revision fails |

#### Version Snapshot Protocol

Create snapshots at these points:

| Milestone | What to Snapshot | Naming Convention |
|-----------|------------------|-------------------|
| **Chapter Complete** | Chapter text + relevant Bible entries | `v1.0-ch03-complete` |
| **Act Complete** | All chapters in act + full Bible | `v1.0-act1-complete` |
| **Draft Complete** | Entire manuscript + full Bible | `v1.0-draft1` |
| **Before Major Revision** | Current state before changes | `v1.1-pre-revision-ch03` |
| **After Major Revision** | New state after changes | `v1.1-post-revision-ch03` |

#### Practical Implementation

**Option A: File-Based (Simple)**
```
project/
├── drafts/
│   ├── v1.0/
│   │   ├── chapter-01.md
│   │   ├── chapter-02.md
│   │   └── STORY-BIBLE-v1.0.md
│   └── v1.1/
│       ├── chapter-01.md (unchanged, linked)
│       ├── chapter-02.md (unchanged, linked)
│       ├── chapter-03.md (REVISED)
│       └── STORY-BIBLE-v1.1.md
├── current/ (symlinks to latest)
└── REVISION-LOG.md
```

**Option B: Git-Based (Advanced)**
```bash
# After completing chapter
git add chapter-03.md STORY-BIBLE.md
git commit -m "Complete Ch3: Elena discovers the warehouse"

# Before major revision
git checkout -b revision/ch03-earlier-betrayal

# After revision complete
git checkout main
git merge revision/ch03-earlier-betrayal
```

**Option C: Tool-Integrated**
- Scrivener: Use Snapshots feature
- Novelcrafter: Built-in versioning
- Google Docs: Version History

### Revision Types and Handling

#### Type 1: Cosmetic Revision
**What:** Prose polish, dialogue improvement, pacing adjustments
**Bible Impact:** None
**Propagation:** None needed

**Protocol:**
1. Make changes to text
2. No Bible update required
3. Note in session log: "Polished Ch3 dialogue"

#### Type 2: Fact Revision
**What:** Changing established facts (eye color, age, location name)
**Bible Impact:** Update affected entries
**Propagation:** Search for all uses of old fact

**Protocol:**
1. Create version snapshot (pre-revision)
2. Update Story Bible entry with change + reason
3. Search entire manuscript for old fact
4. Update all occurrences
5. Create version snapshot (post-revision)
6. Log in REVISION-LOG.md

```markdown
## Fact Revision Log Entry

**Date:** [Date]
**Revision:** Changed Elena's scar location from "left palm" to "right forearm"
**Reason:** Right forearm more visible in planned climax scene
**Bible Entry Updated:** Characters > Elena > Physical Description
**Text Locations Updated:**
- Ch. 2, para 14: Description of scar
- Ch. 7, para 8: Jake notices scar
- Ch. 12, para 22: Elena hides forearm
**Version:** v1.0 → v1.1
```

#### Type 3: Event Revision (Retcon)
**What:** Changing when/how events happened
**Bible Impact:** Update timeline, plot points, character states
**Propagation:** All downstream content may be affected

**Protocol:**
1. Create version snapshot (pre-revision)
2. Map the "blast radius" — what's affected?
3. Decide: Revision (work with existing) or Rewrite (replace)?
4. Update Story Bible:
   - Timeline entries
   - Character "Current State" history
   - Plot Architecture
   - Episodic Log
5. Update affected chapters
6. Verify continuity across all affected sections
7. Create version snapshot (post-revision)
8. Detailed log in REVISION-LOG.md

```markdown
## Event Revision Log Entry

**Date:** [Date]
**Revision:** Moved Jake's betrayal from Ch. 7 to Ch. 4
**Type:** Rewrite (replacing original events)
**Reason:** Pacing—needed tension earlier, midpoint felt late

**Blast Radius:**
- Ch. 4: [Complete rewrite — betrayal scene]
- Ch. 5: [Major revision — Elena's reaction shifted here]
- Ch. 6: [Minor revision — remove foreshadowing now unnecessary]
- Ch. 7: [Major revision — was betrayal, now aftermath]

**Bible Updates:**
- Timeline: Betrayal moved from Day 7 to Day 4
- Elena > Current State: Aware of betrayal from Ch. 4 forward
- Jake > Current State: Revealed as traitor from Ch. 4
- Plot Architecture: Midpoint now = betrayal reveal
- Foreshadowing Registry: Remove Ch. 5-6 hints (now resolved)

**Continuity Verified:** [Date]
**Version:** v1.0 → v2.0 (major structural change)
```

#### Type 4: Structural Revision
**What:** Changing POV, tense, framework, act structure
**Bible Impact:** Style guide, potentially plot architecture
**Propagation:** Entire manuscript affected

**Protocol:**
1. Create FULL backup (this is irreversible territory)
2. Document current structure in revision log
3. Plan new structure before executing
4. Update Style Guide section of Bible
5. Execute changes systematically (chapter by chapter)
6. Full continuity review after completion
7. Create new major version

### The Revision Log

Maintain a dedicated `REVISION-LOG.md` file:

```markdown
# Revision Log: [Project Name]

## Version History

| Version | Date | Type | Summary |
|---------|------|------|---------|
| v1.0 | [Date] | Initial | First draft complete |
| v1.1 | [Date] | Fact | Elena's scar relocated |
| v2.0 | [Date] | Event | Jake betrayal moved to Ch. 4 |

## Detailed Entries

### v2.0 — Jake Betrayal Restructure
[Full entry as shown above]

### v1.1 — Elena Scar Location
[Full entry as shown above]

## Pending Revisions

- [ ] Consider moving warehouse scene to night (atmosphere)
- [ ] Marcus backstory may need expansion in Ch. 8

## Rejected Revisions (and why)

- **Elena's age change (34→28):** Would break mentor dynamic with Jake
- **First-person POV:** Lost omniscient foreshadowing capability
```

### Conflict Resolution

When Story Bible and story text contradict:

```
1. IDENTIFY THE CONFLICT
   - What does the Bible say?
   - What does the text say?
   - Which appeared first?

2. DETERMINE CANONICAL SOURCE
   Option A: Text is authoritative (Bible was outdated)
   Option B: Bible is authoritative (text has error)
   Option C: Neither (this needs a decision)

3. RESOLVE
   - If Option A: Update Bible to match text
   - If Option B: Update text to match Bible
   - If Option C: Escalate to human decision

4. DOCUMENT
   - Log the conflict and resolution
   - Note why this source was chosen as canonical
   - Update both text and Bible to align

5. PREVENT RECURRENCE
   - How did this conflict arise?
   - What extraction or update was missed?
   - Adjust protocol to catch this earlier
```

### Integration with Auto-Tracking

When auto-tracking detects a conflict:

1. **Pause extraction** — do not auto-update
2. **Flag the conflict** with:
   - What Bible says
   - What new text says
   - Where the conflict is
3. **Queue for resolution** — add to "Pending Revisions" in log
4. **Continue session** — conflict doesn't block writing
5. **Resolve at session end** — must address before next session

---

## 13 Non-Linear Writing Protocol

### The Inspiration-First Workflow

Many writers work best by writing scenes that inspire them, regardless of chronological or narrative order. This "discovery writing" (also called "pantsing" or "gardening") captures creative momentum when it strikes, then assembles fragments into coherent narrative later.

**When to Use Non-Linear Writing:**
- A future scene is vivid and demanding to be written now
- You know your ending but not the middle
- Writer's block on current scene, but another scene is clear
- Exploring characters through pivotal moments regardless of position
- Building a story from disconnected ideas that haven't connected yet

**The Core Challenge:** Maintaining continuity and context across scenes written weeks apart, in different orders, with evolving understanding of the story.

### Scene Fragment Tracking

Track each fragment independently with enough metadata to enable later assembly.

#### Fragment Registry

Add to Session State or create dedicated tracking:

```markdown
## Scene Fragments

| Fragment ID | Status | Title/Description | Narrative Position | Chronological Position | Dependencies |
|-------------|--------|-------------------|-------------------|------------------------|--------------|
| F001 | Draft | Marcus discovers betrayal | Ch. 12 (est.) | Day 7 | Requires F003 (setup) |
| F002 | Idea | Opening hook - warehouse | Ch. 1 | Day 1 | None |
| F003 | Complete | Sarah's warning | Ch. 8 (est.) | Day 4 | None |
| F004 | Draft | Final confrontation | Ch. 20 (est.) | Day 14 | Requires F001, F008 |
```

**Fragment Statuses:**
- **Idea** — Concept only, not yet written
- **Draft** — Written but not reviewed for consistency
- **Complete** — Written and verified against Story Bible
- **Integrated** — Connected to adjacent scenes, transitions written
- **Locked** — Part of continuous manuscript, changes trigger revision protocol

#### Per-Fragment Context Card

For each fragment, capture the context needed to write it in isolation:

```markdown
### Fragment: [F001] Marcus Discovers Betrayal

**Scene Goal:** Marcus finds evidence that [Character] has been working against him
**POV:** Marcus (third limited)
**Emotional Arc:** Confusion → Investigation → Devastating realization

**Character States at Scene Start:**
| Character | Location | Knows | Doesn't Know | Emotional State |
|-----------|----------|-------|--------------|-----------------|
| Marcus | Sarah's office | Sarah warned him | Who the traitor is | Suspicious but hopeful |
| [Other] | [Where] | [What] | [What] | [State] |

**Must Be True Before This Scene:**
- Sarah's warning has happened (F003)
- Marcus has access to [location]
- [Evidence item] exists

**This Scene Establishes:**
- Marcus knows about betrayal
- His relationship with [Character] is broken
- He now has motivation for [later action]

**Connection Points:**
- **Incoming:** Needs transition from [prior scene/situation]
- **Outgoing:** Sets up [later scene], character state changes cascade
```

### Dual-Order Tracking

Non-linear stories require tracking two distinct orderings:

1. **Narrative Order** — The sequence readers experience (Chapter 1, 2, 3...)
2. **Chronological Order** — When events occur in story time (Day 1, Day 7, Day 3...)

#### Dual-Order Matrix

```markdown
## Narrative vs. Chronological Order

| Narrative Position | Fragment ID | Chronological Position | Notes |
|--------------------|-------------|------------------------|-------|
| Ch. 1 | F002 | Day 1 | Linear opening |
| Ch. 2 | F006 | Day 3 | Time skip |
| Ch. 3 | F009 | Day 1 (flashback) | Returns to opening day |
| Ch. 4 | F003 | Day 4 | Back to "present" |
```

**Use Cases:**
- **Linear story:** Narrative order = Chronological order (simple)
- **Flashback structure:** Narrative jumps backward in chronology
- **In medias res:** Narrative starts mid-chronology, fills in earlier events
- **Parallel timelines:** Multiple chronological threads interweaved in narrative

### Assembly Protocol (Stitching Fragments)

When fragments are ready for assembly into continuous narrative:

#### Readiness Checklist

Before attempting to connect fragments:

- [ ] All involved fragments at "Complete" status minimum
- [ ] Dependencies satisfied (prerequisite scenes written)
- [ ] Character states verified consistent across fragments
- [ ] No Story Bible conflicts flagged

#### The Stitching Procedure

**1. Identify the Seam**

The connection point between two fragments. Document:
- **Exit state** of Fragment A (where/who/what/emotional state)
- **Entry state** of Fragment B (expected starting conditions)
- **Gap** — What needs to happen between them

**2. Write the Transition**

Transitions can be:
- **Direct cut** — Fragment A ends, Fragment B begins (cinematic)
- **Bridging scene** — Short scene covering the gap
- **Summary passage** — "Three days later..." narrative bridge
- **Implied transition** — Reader infers the connection

**3. Verify Continuity**

After stitching, verify:
- [ ] Character locations make sense (how did they get from A to B?)
- [ ] Emotional continuity (reaction to A's events present in B)
- [ ] Knowledge states updated (characters know what they learned)
- [ ] Physical continuity (injuries, items, weather)
- [ ] Timeline consistency (time passage is plausible)

**4. Update Fragment Status**

Both fragments → "Integrated"

#### Assembly Patterns

**Sequential Assembly:**
Write all fragments, then assemble in order. Best when story structure is known.

**Incremental Assembly:**
Write fragment, immediately connect to existing manuscript. Best for "growing" a story outward from key scenes.

**Hub-and-Spoke Assembly:**
Write a central pivotal scene first, then write scenes radiating forward and backward from that hub.

### Continuity Verification Across Fragments

#### The Fragment Consistency Check

Before marking a fragment "Complete":

1. **Pull character states** from Story Bible for all characters in scene
2. **Verify entry states** match what Bible says at this chronological point
3. **Document exit states** — how characters change during this scene
4. **Flag cascades** — what later fragments are affected by these changes

#### Cross-Fragment Character Tracking

For characters appearing in multiple fragments:

```markdown
## Character State Across Fragments

### Marcus

| Fragment | Chronological Day | Knows | Doesn't Know | Emotional State | Physical State |
|----------|-------------------|-------|--------------|-----------------|----------------|
| F002 | Day 1 | Mission parameters | Who betrayed team | Confident | Healthy |
| F003 | Day 4 | Sarah's warning | Identity of traitor | Worried | Healthy |
| F001 | Day 7 | Who betrayed him | Why they did it | Devastated, angry | Minor injury from Ch. 6 |
| F004 | Day 14 | Everything | - | Resolved, grim | Recovering |
```

**Use this to:**
- Verify states flow logically across chronology
- Catch contradictions (Marcus "healthy" in Day 7 but injured in Day 6)
- Ensure fragments don't have characters know things too early

#### When Fragments Contradict

If you write Fragment B and it contradicts Fragment A:

1. **Stop and assess** — Which version serves the story better?
2. **If A is "Locked"** — Fragment B needs revision (see §12 Revision Management)
3. **If both are "Draft"** — Choose preferred version, update the other
4. **If contradiction improves story** — Revision Protocol applies to earlier fragment
5. **Document the decision** — Add to Revision Log

### AI Integration for Non-Linear Writing

#### Session Context for Fragment Work

When starting a session to work on a fragment:

**Load:**
1. The fragment's Context Card
2. Story Bible sections for characters, locations, rules involved
3. Any prerequisite fragments (for reference)
4. The Dual-Order Matrix (to understand where this fits)

**Don't Load:**
- The full manuscript (irrelevant noise)
- Unrelated fragments
- Future scenes the character doesn't know about yet

#### AI Prompts for Non-Linear Work

**Starting a new fragment:**
> "I'm writing [Fragment ID/description] which occurs at [chronological position] and will appear around [narrative position]. Here's the context card: [paste]. Help me write this scene while maintaining consistency with: [paste relevant Bible sections]."

**Stitching fragments:**
> "I need to connect [Fragment A] to [Fragment B]. Fragment A ends with [exit state]. Fragment B begins with [entry state]. Help me write a transition that bridges these while maintaining continuity."

**Consistency check:**
> "Review this fragment against the Story Bible. Flag any contradictions with character states, timeline, established facts, or rules. Here's the fragment: [paste]. Here's the relevant Bible: [paste]."

### Fragment-First Workflow Summary

```
┌─────────────────────────────────────────────────────────────┐
│                    INSPIRATION STRIKES                       │
│            (Future scene, key moment, ending)                │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                  CREATE FRAGMENT CARD                        │
│     Context Card + Fragment Registry entry + Dual-Order      │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                     WRITE THE FRAGMENT                       │
│          Load minimal context, capture the inspiration       │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   VERIFY CONSISTENCY                         │
│      Cross-reference Story Bible, update character states    │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              UPDATE BIBLE WITH NEW FACTS                     │
│    New characters, locations, rules established in fragment  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                  WHEN READY: ASSEMBLE                        │
│        Stitch fragments, write transitions, verify flow      │
└─────────────────────────────────────────────────────────────┘
```

---

## Appendix A: Worked Example — "The Safehouse"

This appendix demonstrates the Non-Linear Writing Protocol (§13) with a complete thriller example, showing fragment tracking, dual-order management, and assembly.

### Scenario

A writer has three vivid scenes for a thriller but doesn't know the full plot yet:
1. A betrayal reveal mid-story (the emotional core)
2. The opening hook (how it all begins)
3. The confrontation (the climax)

The writer decides to capture inspiration as it strikes.

---

### Step 1: First Inspiration — The Betrayal Scene

The betrayal scene demands to be written first. Before writing, create the tracking artifacts.

#### Fragment Registry (Initial)

```markdown
## Scene Fragments

| Fragment ID | Status | Title/Description | Narrative Position | Chronological Position | Dependencies |
|-------------|--------|-------------------|-------------------|------------------------|--------------|
| F001 | Idea | Elena discovers Marcos is the mole | Ch. 8-10 (est.) | Day 5, evening | Unknown yet |
```

#### Fragment Context Card: F001

```markdown
### Fragment: [F001] Elena Discovers Marcos is the Mole

**Scene Goal:** Elena discovers undeniable proof that Marcos has betrayed her
**POV:** Elena (third limited)
**Emotional Arc:** Routine moment → Accidental discovery → Horrified certainty → Cold resolve

**Character States at Scene Start:**
| Character | Location | Knows | Doesn't Know | Emotional State |
|-----------|----------|-------|--------------|-----------------|
| Elena | Safehouse kitchen | They're being hunted, something feels wrong | Source of the leak | Exhausted, vaguely uneasy |
| Marcos | Safehouse bathroom (shower) | He's the mole, extraction is coming | That Elena will find the phone | Falsely confident |

**Prerequisites (Must Be True):**
- Elena and Marcos are hiding together in a safehouse
- They've been running for several days (establishes exhaustion)
- Marcos's mother died years ago (makes the "Mom" contact damning)

**This Scene Establishes:**
- Elena knows Marcos betrayed her
- Their 3-year partnership is destroyed
- 24-hour deadline creates urgency
- Elena must act alone

**Connection Points:**
- **Incoming:** How did they get to the safehouse? (needs F002)
- **Outgoing:** What does Elena do next? (future fragment)
```

---

### Step 2: Write the Fragment

With the Context Card complete, write the scene.

#### Fragment F001 — DRAFT

> Elena found it while Marcos was in the shower.
>
> She hadn't been looking—just needed a phone charger, and his bag was right there. The burner phone was wedged between socks and a folded map, its screen cracked but functional.
>
> Three messages. All from a number saved as "Mom."
>
> *Package still at location. Confirm extraction window.*
>
> *Why aren't you responding? The client is getting impatient.*
>
> *24 hours. Then we come regardless.*
>
> Marcos's mother had been dead for six years. Elena had been at the funeral.
>
> The shower cut off. Steam curled under the bathroom door.
>
> She photographed the messages, returned the phone exactly as she'd found it, and sat back down at the kitchen table. The coffee in her hands had gone cold twenty minutes ago. She raised it to her lips anyway.
>
> When he emerged, towel around his shoulders, he smiled at her. That same easy smile she'd trusted for three years.
>
> "Couldn't sleep either?" he asked.
>
> "No." She kept her voice level. "Too quiet out here. Makes me nervous."
>
> "We're safe." He opened the refrigerator, his back to her. "No one knows this location."
>
> *Someone does*, she thought. *You made sure of it.*
>
> "I was thinking," she said, "we should move tomorrow. Somewhere more remote."
>
> He turned, and for just a moment—a fraction of a second—something flickered behind his eyes. Calculation. Then the mask returned.
>
> "Good idea. I know a place near the border."
>
> *I bet you do.*
>
> Elena sipped her cold coffee and began planning how to survive the night.

---

### Step 3: Post-Write Updates

After writing, extract facts for the Story Bible and update tracking.

#### Story Bible Additions

```markdown
## Characters

### Elena
- **Role:** Protagonist, field operative
- **Partnership:** 3 years with Marcos
- **Traits:** Observant, calm under pressure, drinks coffee when stressed
- **Current State:** [F001] Knows about betrayal, planning escape

### Marcos
- **Role:** Antagonist (revealed), Elena's partner
- **Secret:** Working with the cartel
- **Backstory:** Mother died 6 years ago (Elena attended funeral)
- **Traits:** Easy smile, good at hiding tension
- **Current State:** [F001] Doesn't know Elena discovered him

## Locations

### The Safehouse
- **Features:** Kitchen, bathroom, refrigerator, remote location
- **Atmosphere:** Quiet, isolated ("too quiet")
- **Near:** Border (Marcos mentions knowing a place)

## Plot Points

- **The Leak:** Marcos has been feeding location to cartel
- **The Client:** Cartel wants "extraction" — Elena is the target
- **The Deadline:** 24 hours until they come regardless
```

#### Updated Fragment Registry

```markdown
| Fragment ID | Status | Title/Description | Narrative Position | Chronological Position | Dependencies |
|-------------|--------|-------------------|-------------------|------------------------|--------------|
| F001 | Draft | Elena discovers Marcos is the mole | Ch. 8-10 (est.) | Day 5, evening | Needs: safehouse arrival (F002) |
```

---

### Step 4: Second Inspiration — The Opening

Now the opening scene becomes clear. Create its tracking artifacts.

#### Fragment Context Card: F002

```markdown
### Fragment: [F002] Opening — The Job Goes Wrong

**Scene Goal:** Establish Elena and Marcos as partners; routine job turns to chaos
**POV:** Elena (third limited)
**Emotional Arc:** Professional confidence → Sudden chaos → Survival mode

**Character States at Scene Start:**
| Character | Location | Knows | Doesn't Know | Emotional State |
|-----------|----------|-------|--------------|-----------------|
| Elena | Surveillance position | Mission parameters | Ambush is coming | Focused, competent |
| Marcos | With Elena | Everything (including ambush) | That Elena will survive | Tense (hidden) |

**Prerequisites:** None (cold open)

**This Scene Establishes:**
- Elena and Marcos are partners (3 years)
- They work surveillance on cartel operations
- An ambush forces them to run
- Sets up the journey to the safehouse

**Connection Points:**
- **Incoming:** None (Chapter 1)
- **Outgoing:** Escape leads to safehouse (Days 1-4 can be montaged)
```

#### Updated Fragment Registry

```markdown
| Fragment ID | Status | Title/Description | Narrative Position | Chronological Position | Dependencies |
|-------------|--------|-------------------|-------------------|------------------------|--------------|
| F001 | Draft | Elena discovers Marcos is the mole | Ch. 8-10 (est.) | Day 5, evening | Needs: F002 |
| F002 | Idea | Opening — The job goes wrong | Ch. 1 | Day 1, morning | None |
```

---

### Step 5: Build the Dual-Order Matrix

With two fragments, map the story structure.

```markdown
## Narrative vs. Chronological Order

| Narrative Position | Fragment ID | Chronological Position | Notes |
|--------------------|-------------|------------------------|-------|
| Ch. 1 | F002 | Day 1, morning | Cold open — job goes wrong |
| Ch. 2-7 | [Gap] | Days 1-5 | Escape, journey, safehouse arrival |
| Ch. 8-10 | F001 | Day 5, evening | Betrayal discovery |
| Ch. 11+ | [Future] | Days 5-6 | Elena's response, confrontation |
```

---

### Step 6: Cross-Fragment Continuity Check

Before writing F002, verify it will support F001.

```markdown
## Character State Across Fragments

### Elena

| Fragment | Chron. Day | Knows | Doesn't Know | Emotional State |
|----------|------------|-------|--------------|-----------------|
| F002 | Day 1 | Mission parameters | About ambush, about Marcos | Confident |
| F001 | Day 5 | Marcos is the mole | His motivation, full plan | Cold, resolved |

### Marcos

| Fragment | Chron. Day | Knows | Doesn't Know | Emotional State |
|----------|------------|-------|--------------|-----------------|
| F002 | Day 1 | Ambush is coming | That Elena survives | Tense (hidden) |
| F001 | Day 5 | Extraction timeline | Elena discovered him | Falsely confident |
```

**Continuity Requirements for F002:**
- Must show Elena trusting Marcos (so F001's betrayal has impact)
- Marcos should have subtle tension before ambush (foreshadowing for re-reads)
- Their partnership dynamic must feel genuine

---

### Step 7: Assembly Demonstration

Once F002 is written (assume "Complete" status), demonstrate stitching.

#### The Seam: F002 → F001

**Exit State of F002:**
- Elena and Marcos escaping ambush
- Heading for safety
- Trust intact (from Elena's perspective)

**Entry State of F001:**
- At safehouse, Day 5 evening
- Exhausted from days of running
- Elena vaguely uneasy

**The Gap:** Days 1-5 (arrival at safehouse, settling in, growing unease)

#### Transition Options

**Option A: Summary Passage**
> Four days of back roads and cold diners brought them to the safehouse. Four days of Marcos insisting they were safe, while Elena's instincts whispered something she couldn't name.

**Option B: Bridging Scene**
A short scene on Day 3 showing a close call that heightens Elena's paranoia.

**Option C: Direct Cut**
```
CHAPTER 8 — DAY 5

Elena found it while Marcos was in the shower.
```

**Chosen:** Option A (summary passage) — efficient, establishes time passage and mounting unease.

#### Post-Stitch Registry Update

```markdown
| Fragment ID | Status | Title/Description | Narrative Position | Chronological Position | Dependencies |
|-------------|--------|-------------------|-------------------|------------------------|--------------|
| F001 | Integrated | Elena discovers Marcos is the mole | Ch. 8 | Day 5, evening | Connected via summary |
| F002 | Integrated | Opening — The job goes wrong | Ch. 1 | Day 1, morning | Leads to F001 |
```

---

### Step 8: Session End Checklist

Following §11 Auto-Tracking Protocol:

```markdown
## Session End — [Date]

### Extraction Complete
- [x] New characters added to Bible: Elena, Marcos
- [x] New locations added: Safehouse
- [x] Plot points captured: Leak, Client, Deadline
- [x] Timeline entries: Day 1 (job), Day 5 (discovery)

### Fragment Status
- F001: Integrated (connected to F002)
- F002: Integrated (connected to F001)

### Continuity Check
- [x] Character names consistent (Elena, Marcos throughout)
- [x] Timeline consistent (Day 1 → Day 5)
- [x] No knowledge-state violations

### Next Session
- [ ] Write confrontation scene (F003)
- [ ] Develop Days 2-4 if needed
- [ ] Consider Marcos POV scene for dramatic irony
```

---

### Key Takeaways

This example demonstrated:

1. **Fragment-First Workflow:** Write what inspires you, track everything
2. **Context Cards:** Capture scene requirements before writing
3. **Dual-Order Tracking:** Separate narrative order from chronology
4. **Cross-Fragment Continuity:** Verify character states flow logically
5. **Assembly Protocol:** Stitch fragments with explicit transitions
6. **Session End Discipline:** Extract, update, verify before closing

The fragments can be written in any order. The tracking system ensures they connect correctly when assembled.

---

## Changelog

### v1.0.0 (Current)
- **Promoted to production** — moved from drafts/ to documents/
- All features from v0.2.0 stable and validated

### v0.2.0
- **Added Auto-Tracking Protocol (§11)** — automatic extraction of story elements
- **Added Revision Management Protocol (§12)** — version control for narrative
- **Added Non-Linear Writing Protocol (§13)** — scene fragment tracking and assembly for discovery writing
  - Fragment Registry and per-fragment Context Cards
  - Dual-Order Tracking (narrative order vs. chronological order)
  - Assembly/stitching procedure with continuity verification
  - Cross-fragment character state tracking
  - Three assembly patterns: Sequential, Incremental, Hub-and-Spoke
  - AI integration prompts for non-linear work
- **Added Appendix A: Worked Example** — "The Safehouse" thriller demonstrating full protocol
- Extraction timing: session-based, milestone-based, token-based triggers
- Entity extraction procedure with categorization
- Session end checklist for auto-tracking
- Version snapshot protocol adapted from Git patterns
- Four revision types: Cosmetic, Fact, Event, Structural
- Revision Log template
- Conflict resolution procedure
- Integration between auto-tracking and revision management
- **Fixed templates** to include all mandatory fields from §3:
  - Added Aliases and Current State to character sections
  - Added Aliases to settings sections
  - Added Character Ages table to timeline sections

### v0.1.0
- Established threshold rules (~10K/25K word boundaries)
- Defined three-tier memory model (Session/Bible/Log)
- Created reference item taxonomy (Tier 1/2/3)
- Included minimal and full Story Bible templates
- Added context loading protocol based on "Lost in the Middle" research
- Platform-specific adaptations
- Voice preservation integration
- Recovery protocols

---

## Sources

### Context & Attention Research
- Liu et al. (2023). "Lost in the Middle: How Language Models Use Long Contexts." Stanford/Meta AI. [arXiv:2307.03172](https://arxiv.org/abs/2307.03172)
- Towards AI. "Lost in the Middle: How Context Engineering Solves AI's Long-Context Problem." [pub.towardsai.net](https://pub.towardsai.net/why-language-models-are-lost-in-the-middle-629b20d86152)

### Story Bible Best Practices
- Novel Smithy. "How to Create a Story Bible for Your Novel." [thenovelsmithy.com](https://thenovelsmithy.com/create-a-story-bible/)
- Jane Friedman. "The Story Bible: What It Is and Why You Need One." [janefriedman.com](https://janefriedman.com/the-story-bible/)
- Tasha L. Harrison. "How to Create a Series Bible for Your Fiction Series." [tashalharrisonbooks.com](https://www.tashalharrisonbooks.com/home/how-to-create-a-series-bible-for-your-fiction-series)
- Atmosphere Press. "Creating a Story Bible for Your Book or Series." [atmospherepress.com](https://atmospherepress.com/creating-a-story-bible/)

### AI Writing Tools
- Novelcrafter. "The Codex - Help Documentation." [novelcrafter.com](https://www.novelcrafter.com/help/docs/codex/the-codex)
- Mythril. "Automated Story Bible & Character Visualization." [mythril.io](https://www.mythril.io/)
- Future Fiction Academy. "Using AI for Series Bibles." [futurefictionacademy.com](https://futurefictionacademy.com/using-ai-for-series-bibles/)

### Version Control for Writers
- Invisible Publishing. "My friend Git: Applying software version control principles to creative writing." [invisiblepublishing.com](https://invisiblepublishing.com/2017/07/12/my-friend-git/)
- DigitalOcean. "How To Use Git to Manage Your Writing Project." [digitalocean.com](https://www.digitalocean.com/community/tutorials/how-to-use-git-to-manage-your-writing-project)
- Ink & Switch. "Upwelling: Combining real-time collaboration with version control for writers." [inkandswitch.com](https://www.inkandswitch.com/upwelling/)

### Revision & Retcon
- TCK Publishing. "What is Retroactive Continuity? Definition, Types, and Examples." [tckpublishing.com](https://www.tckpublishing.com/retroactive-continuity/)
- TV Tropes. "Retcon." [tvtropes.org](https://tvtropes.org/pmwiki/pmwiki.php/Main/Retcon)
- Janice Hardy / Fiction University. "Plot Problem? Fix It Fast with a Retcon." [janicehardy.com](http://blog.janicehardy.com/2018/05/plot-problem-fix-it-fast-with-retcon.html)

### Non-Linear Writing & Discovery Writing
- Anne R. Allen. "The Non-Linear Writing Process." [annerallen.com](https://annerallen.com/2025/06/non-linear-writing-process/)
- K.M. Weiland / Helping Writers Become Authors. "3 Reasons to Write Scenes Out of Order (and 5 Not to)." [helpingwritersbecomeauthors.com](https://www.helpingwritersbecomeauthors.com/5-reasons-to-write-your-scenes-in-order/)
- The Creative Penn. "Outlining/Plotting Vs Discovery Writing/Pantsing." [thecreativepenn.com](https://www.thecreativepenn.com/2022/09/30/outlining-plotting-discovery-writing-pantsing/)
- Dabble Writer. "To Pants Or To Plot: Which One is Best For Your Story?" [dabblewriter.com](https://www.dabblewriter.com/articles/to-pants-or-to-plot-which-one-is-best-for-your-story)
- Literature & Latte. "Two Ways of Creating a Timeline for Your Scrivener Project." [literatureandlatte.com](https://www.literatureandlatte.com/blog/two-ways-of-creating-a-timeline-for-your-scrivener-project)
- Literature & Latte. "Keep Track of Point-of-View Characters and Timelines in Scrivener's Corkboard." [literatureandlatte.com](https://www.literatureandlatte.com/blog/keep-track-of-point-of-view-characters-and-timelines-in-scriveners-corkboard)
- Aeon Timeline. "Novel Outline." [aeontimeline.com](https://www.aeontimeline.com/solutions/novel-outlines)

---

*Version 1.0.0*
*Companion to: Storytelling Domain Principles v1.0.0*
