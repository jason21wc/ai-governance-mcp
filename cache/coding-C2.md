#### C2. Context Window Management (The Token Economy Act)

**Failure Mode(s) Addressed:**
- **A3: Context Window Overflow → Quality Degradation** — Performance degrades as context approaches limits ("context rot"), characterized by hallucinations, contradictions, and loss of earlier decisions.

**Constitutional Basis:**
- Derives from **O4 (Context Optimization):** Minimize context consumption while maintaining effectiveness
- Derives from **C1 (Context Engineering):** Load only necessary information—strategic selection, not exhaustive loading
- Derives from **G3 (Documentation):** Keep information current, accessible, and retrievable from external storage

**Why Meta-Principles Alone Are Insufficient:**
Meta-Principle O4 states "minimize context consumption" but doesn't address what happens when context **overflows despite optimization**—a scenario unique to AI coding where sessions can span hours and touch hundreds of files. Traditional development has no equivalent constraint. This domain principle establishes: (1) proactive monitoring thresholds, (2) prioritization hierarchies for what stays vs. what goes, and (3) recovery protocols when overflow occurs.

**Domain Application:**
AI coding assistants operate within finite context windows (typically 100K-200K tokens). Despite large theoretical limits, research shows performance degrades significantly around 32K tokens due to the "lost in the middle" phenomenon. Effective development requires strategic context management: loading essential information while keeping less-critical details in external, retrievable storage. Context overflow causes information loss, hallucinations, contradicting earlier decisions, and degraded code quality.

**Context Priority Hierarchy (What to Load First):**
1. **Critical (Always Load):** Current task requirements, directly relevant code files, active specifications
2. **Important (Load if Space):** Architecture docs, related module interfaces, recent decisions
3. **Reference (External Storage):** Historical decisions, detailed documentation, inactive code areas
4. **Archive (Never Load):** Completed task details, superseded specifications, resolved discussions

**Truth Sources:**
- Context window size for current AI tool (Claude: 200K, GPT-4: 128K, Gemini: 1M)
- Token consumption tracking (tool-specific metrics)
- Structured external documentation (CLAUDE.md, session logs, decision records)
- Context priority hierarchies (project-specific)

**How AI Applies This Principle:**
- **Priority Loading:** Load context in priority order: (1) Current task requirements, (2) Directly relevant code files, (3) Architecture constraints, (4) Supporting context. Stop loading when task can be completed.
- **Selective Inclusion:** NEVER load entire codebase. Load only files/modules directly relevant to current task. Use directory listings and file summaries to identify what's needed.
- **External References:** Store detailed documentation, historical decisions, and reference materials externally. Load summaries only; retrieve details on-demand.
- **Proactive Monitoring:** Track approximate token consumption. When approaching 60% capacity, evaluate what can be pruned. When approaching 80%, actively summarize and offload.
- **Context Pruning Protocol:** When approaching limits, prune in reverse priority order:
  * First: Detailed explanations already acted upon
  * Second: Code files no longer being modified
  * Third: Documentation already incorporated into implementation
  * Last resort: Summarize critical context rather than losing it entirely
- **State Offloading:** Store session state, decision logs, and progress tracking in external files (CLAUDE.md, session logs). These persist beyond context window.
- **"Lost in the Middle" Awareness:** Place most critical information at the START and END of context, not buried in the middle where attention degrades.

**Why This Principle Matters:**
Memory is finite; forgetting is fatal. *This corresponds to "Judicial Economy"—a court must manage its docket to function effectively. When context overflows, AI doesn't gracefully degrade—it hallucinates, contradicts earlier decisions, and loses architectural coherence. Proactive management prevents the crisis that reactive management cannot fix.*

**When Product Owner Interaction Is Needed:**
- ⚠️ Context limits prevent loading ALL necessary information—prioritization decision required
- ⚠️ Task complexity exceeds single-session context capacity—session decomposition needed
- ⚠️ Context overflow has caused quality issues (detected contradictions, hallucinations)
- ⚠️ Priority conflicts: multiple "critical" items compete for limited context space

**Common Pitfalls or Failure Modes:**
- **The "Load Everything" Trap:** Loading entire codebase, all documentation, full git history—causing immediate overflow. *Prevention: Load incrementally by priority; stop when task is completable.*
- **The "Context Amnesia" Trap:** Not tracking token consumption until quality visibly degrades. By then, damage is done. *Prevention: Proactive monitoring at 60%/80% thresholds.*
- **The "Middle Burial" Trap:** Placing critical specifications in the middle of context where attention is weakest. *Prevention: Critical info at start and end; summaries in middle.*
- **The "Orphaned State" Trap:** Session state stored only in context—lost when context resets or overflows. *Prevention: Always externalize to CLAUDE.md or session files.*
- **The "False Capacity" Trap:** Trusting large context window numbers (200K tokens) without understanding quality degradation begins much earlier. *Prevention: Treat 32K as effective limit for quality; beyond that, actively manage.*

**Success Criteria:**
- ✅ Token consumption tracked throughout sessions (at least awareness of approximate level)
- ✅ Context prioritization strategy documented for project
- ✅ Critical information always available; supporting details retrievable from external storage
- ✅ No quality degradation attributable to context overflow
- ✅ Session state persisted externally, not dependent on context window
- ✅ Proactive pruning occurs BEFORE overflow, not after quality degrades

---
