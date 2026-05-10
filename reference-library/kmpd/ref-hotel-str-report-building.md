---
id: ref-hotel-str-report-building
title: "Hotel STR Performance Report — Document Structure"
domain: kmpd
tags: ["hotel", "str", "report", "docx", "revenue-management", "performance-analysis", "document-building"]
status: current
entry_type: reference
summary: "Proven 12-section report structure for hotel STR performance analysis documents"
created: 2026-05-09
last_verified: 2026-05-09
maturity: budding
decay_class: framework
source: "Captured via capture_reference tool"
---

## Context

Use when building a Word document report from STR/SMART Packet data. Full guide in Hotel Analyzer _ai-context/marriott/REPORT-BUILDING.md

## Artifact

## STR Performance Report — Section Template

**Output:** Word (.docx) via npm docx package
**Philosophy:** Factual, neutral, data-speaks-for-itself. No sales narrative.

### 12-Section Structure
1. Title & Property Info
2. YTD Performance Summary (Property + Comp Set, YoY)
3. Competitive Index Performance (MPI, ARI, RGI)
4. Monthly Performance Trend (12-14 months, color-coded YoY)
5. Monthly Index Trend with Ranks
6. Market Context (property vs market vs submarket vs class)
7. Competitive Set Composition
8. Most Recent Weekly Performance
9. Demand Segmentation YTD (category + transient detail)
10. Full-Year Segmentation (prior year vs prior-prior)
11. Top 20 Accounts with pacing %
12. Key Accounts apples-to-apples YTD comparison
13. Key Data Observations (10-15 factual bullets)

### Color Scheme
Headers: #2E5A88 (dark blue), Positive: #E8F5E9 bg / #2E7D32 text, Negative: #FFEBEE bg / #C62828 text

### Quality Gate
All numbers verified against source before hardcoding. PDF preview before delivery.

## Lessons Learned

1. Two-phase build (Python extract → Node.js docx) prevents data errors from compounding with formatting errors. 2. US Letter with 1" margins = 9360 DXA content width. 3. Always generate PDF preview to check table overflow. 4. Local npm install required in Cowork sandbox (global fails).

## Cross-References

- Principles: [relevant principle IDs]
- Methods: [relevant method section refs]
- See also: [related entry IDs]
