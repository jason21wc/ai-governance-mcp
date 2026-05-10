---
id: ref-hotel-smart-packet-extraction
title: "Marriott SMART Packet Data Extraction Process"
domain: kmpd
tags: ["hotel", "marriott", "smart-packet", "str", "revenue-management", "data-extraction", "openpyxl"]
status: current
entry_type: reference
summary: "Step-by-step process for extracting hotel performance data from Marriott SMART Packet xlsx files using openpyxl"
created: 2026-05-09
last_verified: 2026-05-09
maturity: budding
decay_class: framework
source: "Captured via capture_reference tool"
---

## Context

Use when analyzing any Marriott hotel property's SMART Packet for performance analysis. The full methodology is in the Hotel Analyzer _ai-context/marriott/ folder.

## Artifact

## SMART Packet Extraction — Quick Reference

**Source:** Marriott Themed SMART Packet (.xlsx, ~10 MB, 50+ sheets)
**Tool:** openpyxl with read_only=True, data_only=True

### Key Sheets
- Monthly STR → core metrics (Occ, ADR, RevPAR) by month with YoY
- Monthly STR Comp → competitive indexes (MPI, ARI, RGI) with rank
- Weekly STR → most recent weekly performance
- Monthly STR Seg → market/submarket/class context
- ws_DAT3 → account-level data (6,000+ rows, filter by date)

### Column Mapping (Monthly STR)
Columns 3-6 = Sep-Dec prior-prior year; 7-18 = Jan-Dec prior year; 19+ = current year.
Read by cell coordinate (row, col integers), not headers.

### Extraction Order
1. Open read_only → 2. Map columns to months → 3. Monthly STR metrics → 4. Comp indexes → 5. Weekly → 6. Market context → 7. ws_DAT3 accounts → 8. Verify totals

### Two-Phase Build
Phase 1 (Python): Extract, verify, print. Phase 2 (Node.js docx): Hardcode verified values into document builder.

## Lessons Learned

1. Always use read_only=True — files are 10MB+ and will timeout otherwise. 2. Column mapping is positional, not header-based. 3. Separate extraction from document building to isolate data errors from formatting errors. 4. ws_DAT3 spans multiple years — filter by date before aggregating. 5. Back-compute prior YTD values from current value and YoY change when not directly available.

## Cross-References

- Principles: [relevant principle IDs]
- Methods: [relevant method section refs]
- See also: [related entry IDs]
