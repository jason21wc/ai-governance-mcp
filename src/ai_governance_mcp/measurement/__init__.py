"""Objective-measurement primitives for AI-governance effectiveness (BACKLOG #48).

Deliberately dependency-light (stdlib only) so measurement tooling — the throwaway
`examples/effort-not-time-probe/` AND the real-transcript `scripts/measure_directive_compliance.py`
— can share one SSOT grader without pulling the torch-heavy server package.

See `graders.py` for the deterministic directive-compliance detectors.
"""
