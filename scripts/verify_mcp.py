#!/usr/bin/env python3
"""
MCP Verification Script
Run after rebuilding index to verify all domains are accessible.
"""

import json
from pathlib import Path


def verify_index():
    """Verify the index file has expected content."""
    index_path = Path(__file__).parent.parent / "index" / "global_index.json"

    with open(index_path) as f:
        index = json.load(f)

    print("=" * 60)
    print("INDEX VERIFICATION")
    print("=" * 60)

    expected = {
        "constitution": {"principles": 42, "methods": 62},
        "ai-coding": {"principles": 12, "methods": 104},
        "multi-agent": {"principles": 11, "methods": 15},
    }

    all_pass = True
    for domain, counts in expected.items():
        if domain not in index["domains"]:
            print(f"❌ {domain}: MISSING")
            all_pass = False
            continue

        actual_p = len(index["domains"][domain].get("principles", []))
        actual_m = len(index["domains"][domain].get("methods", []))

        p_ok = actual_p == counts["principles"]
        m_ok = actual_m == counts["methods"]

        p_status = "✅" if p_ok else "❌"
        m_status = "✅" if m_ok else "❌"

        print(f"{domain}:")
        print(f"  {p_status} Principles: {actual_p} (expected {counts['principles']})")
        print(f"  {m_status} Methods: {actual_m} (expected {counts['methods']})")

        if not p_ok or not m_ok:
            all_pass = False

    print()
    total_items = sum(
        len(d.get("principles", [])) + len(d.get("methods", []))
        for d in index["domains"].values()
    )
    print(f"Total items: {total_items}")
    print()

    if all_pass:
        print("✅ ALL CHECKS PASSED")
    else:
        print("❌ SOME CHECKS FAILED")

    return all_pass


if __name__ == "__main__":
    verify_index()
