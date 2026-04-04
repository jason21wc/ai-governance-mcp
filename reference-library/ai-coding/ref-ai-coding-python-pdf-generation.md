---
id: ref-ai-coding-python-pdf-generation
title: "Python PDF Generation: WeasyPrint vs ReportLab Decision"
domain: ai-coding
tags: [pdf, python, document-generation, docker, library-selection, weasyprint, reportlab]
status: current
entry_type: direct
summary: "Decision guide for Python PDF generation — WeasyPrint (HTML/CSS→PDF) vs ReportLab (programmatic). Includes Docker deployment gotcha for WeasyPrint system dependencies."
created: 2026-04-03
last_verified: 2026-04-03
maturity: budding
decay_class: framework
source: "Web research (dev.to, templated.io, nutrient.io comparisons, 2025-2026). Validated against Docker deployment experience."
related: [ref-ai-coding-web-app-file-downloads]
---

## Context

Python has two established PDF generation libraries with fundamentally different approaches. AI agents tend to recommend ReportLab by default (more training data), but WeasyPrint is often simpler and more appropriate for web app report generation.

## Artifact

### Decision Tree

```
Need PDF output in Python?
├── HTML/CSS-based content (invoices, reports, letters)?
│   └── WeasyPrint — write HTML templates, render to PDF
│       ├── Pros: natural for web devs, CSS styling, easy templates
│       └── Cons: system dependencies (Cairo, Pango) — Docker pain
├── Data-heavy, precise layout (charts, forms, labels)?
│   └── ReportLab — programmatic, pixel-level control
│       ├── Pros: lightweight, no system deps, fast, precise
│       └── Cons: verbose API, non-intuitive layout model
└── Both simple and complex in same app?
    └── Use both — WeasyPrint for reports, ReportLab for specialized outputs
```

### Docker Deployment (WeasyPrint)

WeasyPrint requires system-level libraries that are NOT included in `python:*-slim` images:

```dockerfile
FROM python:3.12-slim

# Required for WeasyPrint — without these, import fails silently or with cryptic errors
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf2.0-0 \
    libffi-dev \
    libcairo2 \
    && rm -rf /var/lib/apt/lists/*
```

ReportLab has no system dependencies — `pip install reportlab` works in any Python environment.

### Validation Pattern

```python
import fitz  # PyMuPDF

def validate_pdf(pdf_bytes: bytes, expected_pages: int) -> bool:
    """Validate generated PDF has expected structure."""
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    assert doc.page_count == expected_pages, f"Expected {expected_pages} pages, got {doc.page_count}"
    assert len(pdf_bytes) > 1024, "PDF suspiciously small — likely empty or corrupt"
    # Check first page has text content
    first_page = doc[0]
    assert first_page.get_text().strip(), "First page has no text content"
    doc.close()
    return True
```

## Lessons Learned

- AI agents recommend ReportLab by default because it has more training data presence. For most web app report generation, WeasyPrint is simpler — you write HTML/CSS templates and render to PDF.
- The WeasyPrint Docker dependency issue is the #1 gotcha. The error messages when system libraries are missing are not helpful — `OSError: cannot load library 'libgobject-2.0.so'` doesn't obviously point to "install Pango."
- For serverless/Lambda deployments, ReportLab is strongly preferred — WeasyPrint's system dependencies make Lambda layers complex.
- Both libraries work with `io.BytesIO()` for in-memory generation — no temp files needed.

## Do / Don't

**Do:** Choose WeasyPrint for HTML-based reports where CSS controls layout. Choose ReportLab for programmatic, data-dense outputs requiring precise positioning.

**Don't:** Use WeasyPrint without verifying system dependencies in your deployment environment. Don't use ReportLab for simple reports that would be easier to template in HTML/CSS.

## Cross-References

- Principles: meta-quality-structured-output-enforcement, coding-quality-supply-chain-solution-integrity
- Methods: §9.4 (Document Generation Patterns), §9.4.3 (Download Serving Patterns)
- See also: ref-ai-coding-web-app-file-downloads
