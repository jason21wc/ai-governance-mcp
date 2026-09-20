# /architecture-review Procedure

Three phases: map the codebase structure, assess structural health against defined criteria, report with a structural map and prioritized recommendations. Phase 1 is the skill's core value — the structural map is the primary deliverable.

---

## Phase 1: Map

This phase builds a structural inventory of the codebase. Every claim must be backed by tool output (grep, file listing, import analysis).

### 1a. Module Structure

Enumerate the top-level modules, packages, or major directories:

```bash
# Top-level directory structure
find . -maxdepth 2 -type d -not -path './.git*' -not -path './node_modules*' -not -path './__pycache__*' -not -path './venv*' -not -path './.venv*' | sort

# File counts per top-level directory
for dir in $(ls -d */ 2>/dev/null); do echo "$(find "$dir" -type f -not -path '*/__pycache__/*' | wc -l | tr -d ' ') $dir"; done | sort -rn
```

For each module/package, identify its responsibility in one sentence based on:
- Directory name and README/docstring if present
- The types of files it contains (handlers, models, utils, tests)
- Its imports (what it depends on) and reverse imports (what depends on it)

### 1b. Entry Points

Identify how the codebase is invoked:

```bash
# Python entry points
grep -rn "def main\|if __name__\|entry_points\|console_scripts" . --include="*.py" --include="pyproject.toml" --include="setup.py" --include="setup.cfg"

# Node.js entry points
grep -n '"main"\|"bin"\|"scripts"' package.json 2>/dev/null

# Go entry points
find . -name "main.go" -type f

# Generic: Dockerfiles, Makefiles, CI configs
ls Dockerfile* Makefile* .github/workflows/*.yml docker-compose*.yml 2>/dev/null
```

### 1c. Dependency Graph

Build an import/dependency map showing which modules depend on which:

```bash
# Python imports between internal modules
grep -rn "^from \.\|^from src\|^import src" . --include="*.py" | grep -v __pycache__ | grep -v test

# JavaScript/TypeScript imports between internal modules
grep -rn "from ['\"]\\./\|from ['\"]\\.\\./" . --include="*.ts" --include="*.tsx" --include="*.js" --include="*.jsx" | grep -v node_modules | grep -v test

# Go internal imports
grep -rn "\"$(head -1 go.mod 2>/dev/null | awk '{print $2}')/" . --include="*.go" 2>/dev/null
```

Organize into a dependency direction table:

| Module | Depends On | Depended On By |
|--------|-----------|----------------|
| (fill from grep results) | | |

Flag any **circular dependencies** (A → B → A) or **layer violations** (if layers are identifiable).

### 1d. Layer Identification

If the codebase has discernible layers (presentation/API → business logic → data access), identify them:

- **By convention:** directories named `api/`, `handlers/`, `routes/`, `services/`, `models/`, `db/`, `repositories/`
- **By import direction:** if module A imports module B but B never imports A, A is a higher layer
- **By external dependency:** modules importing HTTP frameworks are presentation; modules importing ORMs are data

Not all codebases have layers. If the structure is flat or the organization principle is different (feature-based, plugin-based), describe what IS there rather than forcing a layer model.

### 1e. External Dependencies

```bash
# Python
grep -E "^[a-zA-Z]" requirements*.txt 2>/dev/null || grep -A100 "\[project\]" pyproject.toml 2>/dev/null | grep -E "^\s+\"" | head -20

# Node.js
cat package.json 2>/dev/null | grep -A50 '"dependencies"' | head -25

# Go
cat go.mod 2>/dev/null | grep -E "^\t" | head -20
```

Note any unusually heavy dependencies or version pins that suggest compatibility constraints.

---

## Phase 2: Assess

Using the map from Phase 1, evaluate structural health. Each assessment must reference specific modules or files from the map.

### 2a. Layering Integrity

If layers were identified in Phase 1d:
- Do higher layers import lower layers only (not the reverse)?
- Are there skip-layer imports (presentation directly accessing data, bypassing business logic)?
- Is each layer's responsibility clear, or do layers blur?

If no layers: skip this check and note "flat/non-layered organization."

### 2b. Module Cohesion

For each major module from Phase 1a:
- Does it have a single, clear responsibility?
- Could you describe what it does in one sentence without using "and"?
- Are there files that seem misplaced (a utility function in a handler module, a model definition in a routes file)?

Low cohesion indicators: modules with generic names (`utils`, `helpers`, `common`, `misc`), modules with >15 files spanning unrelated concerns, modules where most files don't import each other.

### 2c. Coupling Hotspots

From the dependency graph (Phase 1c):
- Which module is imported by the most other modules? (highest fan-in = most critical, hardest to change)
- Which module imports the most other modules? (highest fan-out = most coupled, hardest to understand)
- Are there module pairs with bidirectional dependencies?

```bash
# Find the most-imported internal modules (Python example)
grep -rhn "^from \|^import " . --include="*.py" | grep -v __pycache__ | sed 's/from //;s/import .*//' | sort | uniq -c | sort -rn | head -10
```

### 2d. Repeated Anti-Patterns

Scan across the codebase (not just one file) for systemic issues:

- **God objects:** classes/modules with >500 lines AND high fan-in
- **Utility explosion:** >3 files named `*util*`, `*helper*`, `*common*` — suggests missing abstractions
- **Naming drift:** inconsistent naming conventions across modules (camelCase in some, snake_case in others)
- **Dead code indicators:** files with zero imports from other files (excluding entry points and tests)
- **Configuration scatter:** config values defined in multiple locations rather than a single config module

### 2e. Cross-Cutting Concern Consistency

Check whether these concerns are handled consistently across modules:

- **Error handling:** same pattern everywhere, or different patterns per module?
- **Logging:** centralized or scattered? Consistent format?
- **Validation:** at boundaries only, or repeated at every layer?
- **Type safety:** consistent use of types/interfaces, or mixed typed/untyped?

### 2f. Growth Capacity

Based on the overall structure:
- Can a new feature be added without modifying existing modules? (open-closed)
- Is the test structure parallel to the source structure? (testability)
- Are there obvious bottleneck modules that would need splitting as the codebase grows?
- Is the dependency graph roughly tree-shaped (healthy) or web-shaped (tangled)?

---

## Phase 3: Report

Produce a structured assessment. The report is the deliverable — make it referenceable for future decisions.

### Output Format

```markdown
# Architecture Review: [project/module name]

## Structural Map

### Modules
| Module | Responsibility | Files | Fan-In | Fan-Out |
|--------|---------------|-------|--------|---------|
| (from Phase 1) | | | | |

### Entry Points
- (from Phase 1b)

### Dependency Direction
[Describe the import flow. If layered: name the layers top-to-bottom.
If not layered: describe the organization principle.]

### Key External Dependencies
- (from Phase 1e, only notable ones)

## Health Assessment

### Strengths
- [What's well-organized — be specific, cite modules]

### Coupling Hotspots
| Module Pair | Direction | Severity | Evidence |
|------------|-----------|----------|----------|
| (from Phase 2c) | | HIGH/MEDIUM/LOW | grep evidence |

### Cohesion Gaps
- [Modules that should be split or merged, from Phase 2b]

### Anti-Patterns
- [Systemic issues from Phase 2d, with counts and locations]

### Cross-Cutting Inconsistencies
- [From Phase 2e, if any]

## Growth Capacity
[From Phase 2f — can the architecture support continued development?]

## Refactoring Priorities
[Ordered list: highest-impact structural improvements.
For each: what to change, why, and which skill to use next
(/refactor-audit for readiness, /test-suite for coverage prerequisites).]
```

### Output Guidelines

- **Evidence over opinion.** Every finding cites file paths or grep output.
- **Strengths first.** Don't just list problems — acknowledge what's working.
- **Severity on coupling hotspots.** HIGH = bidirectional dependency or >10 fan-in. MEDIUM = skip-layer or >5 fan-in. LOW = minor.
- **Refactoring priorities are recommendations, not mandates.** The user decides what to act on.
- **Scale to codebase size.** A 10-file project gets a concise report. A 500-file project gets the full table format. Don't over-analyze small codebases.
