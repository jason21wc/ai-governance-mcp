"""Tests for the Layer-0 insecure-persistence floor (BACKLOG #73, plan async-giggling-wren).

The floor is the deterministic ESCALATE net UNDER the keyword-adjudication judge:
a sentence-scoped strong-signal persistence verb co-located with a CRITICAL
safety keyword fires deterministically (judge never consulted). It restores the
session-237 required guard (b) with a deliberately NARROW membership — a floor
false-positive merely reproduces today's behavior (ESCALATE), while noun-collision
verbs this project's own vocabulary uses constantly (commit/log/write/embed/cache)
are EXCLUDED and left to the judge.

Routing consumption of the floor is tested in tests/test_server_governance.py;
this file pins the pure detector semantics.
"""

import pytest

from ai_governance_mcp.safety_scan import detect_insecure_persistence


class TestDetectInsecurePersistence:
    """Sentence-scoped persistence-verb + CRITICAL keyword co-location."""

    # ------------------------------------------------------------------ #
    # Genuine insecure-persistence phrasings MUST fire (the FN corpus     #
    # class the session-237 security review required a deterministic net  #
    # for).                                                               #
    # ------------------------------------------------------------------ #

    @pytest.mark.parametrize(
        "action",
        [
            "store the user password in plaintext in config.py",
            "hardcode the api key in the source",
            "hardcoding the api key for the demo",
            "stored the credential in a debug file",
            "saving the secret to disk for later",
            "persist the access token in localStorage",
            "Store the PASSWORD in the settings module",  # case-insensitive
        ],
    )
    def test_genuine_persistence_phrasings_fire(self, action):
        hits = detect_insecure_persistence(action)
        assert hits, f"floor must fire on: {action!r}"

    def test_plaintext_co_occurrence_fires_without_a_verb(self):
        # 'plaintext' co-located with a CRITICAL keyword is itself the signal —
        # no persistence verb needed ("the password ends up in plaintext").
        hits = detect_insecure_persistence(
            "after this change the password ends up in plaintext on disk"
        )
        assert hits

    def test_hit_message_names_signal_and_keyword(self):
        # Audit visibility: the message must carry both the matched signal and
        # the CRITICAL keyword so the escalation rationale is self-explanatory.
        hits = detect_insecure_persistence("store the password in the config")
        assert any("store" in h and "password" in h for h in hits)

    # ------------------------------------------------------------------ #
    # Benign phrasings from THIS project's live vocabulary must NOT fire  #
    # (contrarian S1: noun collisions are concentrated in the project's   #
    # own normal work — a floor FP here would silently re-create the FP   #
    # class the judge exists to remove).                                  #
    # ------------------------------------------------------------------ #

    @pytest.mark.parametrize(
        "action",
        [
            # excluded noun-collision verbs: commit / log / write / embed / cache
            "push 3 commits mentioning the secret-scanner",
            "commit the secret-scanner fix and run the suite",
            "log the credential-redaction test results",
            "write tests for the api key detection module",
            "the embedding cache layer needs a secret-handling docstring",
            # safe-context leader in the co-located sentence suppresses the floor
            "the embedding cache stores no secrets",
            "we never store the password anywhere",
            "documents how credentials are stored by the upstream vendor",
            # verb present but NO critical keyword in its sentence
            "update the docs describing how we store configuration",
            # word-boundary: 'restore' must not match 'store'
            "restore the password backup from yesterday's snapshot",
            # no keyword at all
            "store the parsed results in the database",
        ],
    )
    def test_benign_phrasings_do_not_fire(self, action):
        assert detect_insecure_persistence(action) == []

    # ------------------------------------------------------------------ #
    # Sentence scoping                                                    #
    # ------------------------------------------------------------------ #

    def test_verb_and_keyword_in_different_sentences_do_not_fire(self):
        action = (
            "Store the results in the database. The credential handling is unchanged."
        )
        assert detect_insecure_persistence(action) == []

    def test_leader_in_other_sentence_does_not_suppress(self):
        # The leader must sit in the SAME sentence as the co-location to
        # suppress — a leader elsewhere cannot talk the floor out of a real hit.
        action = (
            "No changes to the retrieval engine. "
            "Store the password in plaintext for the demo."
        )
        assert detect_insecure_persistence(action)

    def test_empty_and_keyword_free_inputs(self):
        assert detect_insecure_persistence("") == []
        assert detect_insecure_persistence("refactor the parser") == []
