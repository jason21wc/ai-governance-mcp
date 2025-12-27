### Q1. Validation Independence

**Why This Principle Matters**

Agents cannot objectively validate their own work—confirmation bias causes self-assessment to skew positive regardless of actual quality. The constitutional principle Q1 (Verification) requires validation against requirements; for multi-agent systems, this means dedicating separate agents to validation with fresh context and explicit criteria. The Generator-Critic pattern separates creation from validation, ensuring independent quality assessment. Additionally, MA4 (Blameless Error Reporting) requires that outputs include confidence indication so reviewers can calibrate their scrutiny.

**Domain Application (Binding Rule)**

Validation must be performed by a dedicated agent separate from the agent that produced the output. The validation agent operates with fresh context, explicit acceptance criteria, and no access to the generator's reasoning or justifications. Validation results are pass/fail with specific findings, not subjective assessments. All significant outputs must include confidence indication from the producing agent to guide validation intensity.

**Constitutional Basis**

- Q1 (Verification): Validate outputs against requirements
- MA1 (Role Segregation): Validation is a distinct cognitive function from generation
- MA4 (Blameless Error Reporting): Confidence scoring on critical outputs; accuracy over completion
- Q3 (Fail-Fast): Flag low-confidence outputs for enhanced review

**Truth Sources**

- Google ADK: Generator-Critic pattern separates creation from validation
- Enterprise patterns: Independent validation agents for quality assurance
- MA4: "Every critical output must be accompanied by a confidence score"
- Research: Confirmation bias documented in self-assessment scenarios

**How AI Applies This Principle**

1. Define validation agent with critic/reviewer cognitive function
2. Spawn validation agent with fresh context (not generator's context)
3. Producing agent includes confidence indication with output
4. Low-confidence outputs receive enhanced validation scrutiny
5. Provide explicit acceptance criteria—not "is this good?" but specific checkpoints
6. Receive structured validation results: pass/fail + specific findings
7. Route failures back to appropriate agent for correction

**Success Criteria**

- Every significant output passes through independent validation
- Validation agent has no access to generator's internal reasoning
- All outputs include confidence indication from producing agent
- Low-confidence outputs flagged for enhanced review
- Validation criteria are explicit and checkable
- Validation failures include specific, actionable findings

**Human Interaction Points**

- Define validation criteria for novel output types
- Review validation findings for high-stakes outputs
- Review all low-confidence outputs regardless of validation pass
- Resolve disagreements between generator and validator

**Common Pitfalls**

- **Self-Validation:** Generator agent assessing its own work
- **Context Pollution:** Validator loaded with generator's reasoning and justifications
- **Missing Confidence:** Outputs delivered without confidence indication
- **Vague Criteria:** "Validate this is good" instead of specific acceptance criteria
- **Rubber Stamping:** Validator always passing due to insufficient criteria
- **Ignored Low-Confidence:** Proceeding with uncertain outputs without enhanced review

**Configurable Defaults**

- Validation coverage: All phase-completing outputs (minimum)
- Validation agent context: Fresh spawn, criteria + output only (no generator context)
- Confidence indication: Required on all significant outputs
- Low-confidence threshold: Triggers enhanced validation (threshold configurable)

---
