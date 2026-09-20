# Sample Methods for Testing

This is a minimal methods document for unit and integration testing.

## 1 Cold Start Kit

The Cold Start Kit initializes new project sessions.

### Purpose
Establish baseline context for effective AI assistance.

### Procedure
1. Check for existing session state
2. Load project memory if available
3. Scan for key files (README, config, etc.)
4. Create SESSION-STATE.md if new project

## 2 Phase Gate Validation

Gate validation ensures quality before phase transitions.

### Checklist
- [ ] All requirements addressed
- [ ] Tests passing
- [ ] Coverage meets threshold
- [ ] No blocking issues

### Recovery
If gate fails, return to previous phase and address deficiencies.

## 3 Specification Workflow

Process for handling incomplete specifications.

### Detection
- Missing acceptance criteria
- Ambiguous requirements
- Conflicting constraints

### Resolution
1. Document gaps
2. Propose clarifications
3. Request Product Owner input
