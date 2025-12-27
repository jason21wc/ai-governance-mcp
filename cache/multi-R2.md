### R2. Orchestration Pattern Selection

**Why This Principle Matters**

Different task types require different coordination patterns. Sequential patterns ensure dependencies are respected; parallel patterns maximize throughput; hierarchical patterns manage complexity. Applying the wrong orchestration pattern creates either unnecessary bottlenecks (over-serialization) or coordination failures (inappropriate parallelization). Pattern selection should match task characteristics, not developer preference. Additionally, the original multi-agent architecture research demonstrates that enforcing sequential dependencies prevents specification gaps that force AI to make architectural decisions during implementation.

**Domain Application (Binding Rule)**

Select orchestration pattern based on task characteristics: use sequential for dependent tasks, parallel for independent tasks, hierarchical for complex multi-level delegation. The orchestrator enforces the selected pattern and prevents pattern violations. For sequential dependencies: Phase N+1 cannot begin until Phase N validation passes. Upstream changes must trigger downstream re-validation.

**Constitutional Basis**

- MA5 (Coordination Protocols): Established protocols govern interaction
- O1 (Iterative Design): Appropriate workflow for task complexity
- C7 (Inversion of Control): Reason backward from goal to identify dependencies
- Q3 (Fail-Fast): Catch dependency violations early

**Truth Sources**

- Microsoft Azure: Sequential, concurrent, and group chat orchestration patterns
- Databricks: Continuum from chains to single-agent to multi-agent
- Confluent: Orchestrator-worker, hierarchical, blackboard, market-based patterns
- Original architecture: "Phase progression must be unidirectional with validation gates"

**How AI Applies This Principle**

1. Analyze task for dependencies between subtasks
2. Identify parallelization opportunities (independent subtasks)
3. Select pattern: Sequential (dependent), Parallel (independent), Hierarchical (complex delegation)
4. Configure orchestrator to enforce selected pattern
5. For sequential patterns: Block Phase N+1 until Phase N validation passes
6. When upstream changes occur, trigger downstream re-validation
7. Monitor for pattern violations and adjust as needed

**Success Criteria**

- Pattern selection documented with rationale
- Dependent tasks execute sequentially with validation gates
- Independent tasks execute in parallel where beneficial
- Complex tasks use hierarchical delegation appropriately
- No dependency violations (downstream before upstream)
- Upstream changes trigger appropriate downstream re-validation
- Orchestrator actively prevents out-of-order execution

**Human Interaction Points**

- Approve pattern selection for novel or ambiguous task structures
- Override automatic pattern selection when domain knowledge indicates different approach
- Define dependencies that may not be obvious from task description
- Approve phase transitions in sequential workflows

**Common Pitfalls**

- **Over-Serialization:** Sequential pattern for independent tasks (wastes time)
- **Unsafe Parallelization:** Parallel pattern for dependent tasks (produces errors)
- **Flat Hierarchy:** Single-level delegation for complex multi-level tasks
- **Gate Bypass:** Skipping validation to "save time" (causes rework cascades)
- **Ignored Re-validation:** Upstream changes not propagating to downstream phases

**Configurable Defaults**

- Default pattern: Sequential (safest; opt into parallel when dependencies confirmed)
- Dependency analysis: Required before parallel execution
- Validation gates: Required between sequential phases

---
