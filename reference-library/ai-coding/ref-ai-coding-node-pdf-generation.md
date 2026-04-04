---
id: ref-ai-coding-node-pdf-generation
title: "Node.js PDF Generation: Library Decision Tree"
domain: ai-coding
tags: [pdf, node, document-generation, library-selection, pdfkit, puppeteer, jspdf, pdf-lib]
status: current
entry_type: direct
summary: "Decision tree for Node.js PDF generation — PDFKit (programmatic server-side), Puppeteer (HTML-to-PDF), jsPDF (browser-oriented), pdf-lib (modification/manipulation). AI agents frequently confuse these four libraries."
created: 2026-04-03
last_verified: 2026-04-03
maturity: budding
decay_class: framework
source: "Web research (nutrient.io, dev.to, pdfnoodle.com, pdfbolt.com comparisons, 2025-2026). Library confusion pattern confirmed across multiple AI agent interactions."
related: [ref-ai-coding-web-app-file-downloads, ref-ai-coding-python-pdf-generation, ref-ai-coding-node-excel-generation]
---

## Context

Node.js PDF generation is the most fragmented document generation category. Four libraries serve fundamentally different purposes, but AI agents routinely confuse them — recommending jsPDF for server-side use (it's browser-oriented) or pdf-lib for generation from scratch (it excels at modification). This is the highest-value library selection guidance in the document generation space.

## Artifact

### Decision Tree

```
Need PDF output in Node.js?
├── Building PDF programmatically from data (invoices, reports)?
│   └── PDFKit — server-side, streaming, well-established
│       ├── Pros: streaming API, pipes to HTTP response, no native deps
│       └── Cons: manual layout (no CSS), verbose for complex layouts
│
├── Converting HTML/CSS to PDF (existing web templates)?
│   └── Puppeteer or Playwright — headless Chrome rendering
│       ├── Pros: pixel-perfect, uses your existing CSS, handles complex layouts
│       └── Cons: needs Chrome binary (~300MB), high memory, slow cold start
│       └── Note: Playwright is newer alternative with same approach
│
├── Modifying existing PDFs (fill forms, merge, stamp, add pages)?
│   └── pdf-lib — works in browser AND Node, zero native deps
│       ├── Pros: pure JS, small bundle, great for form filling
│       └── Cons: limited for complex generation from scratch
│
├── Client-side PDF in the browser?
│   └── jsPDF — browser-native, uses html2canvas
│       ├── Pros: runs in browser, no server needed
│       └── Cons: image-based output (no real text), blurry on zoom,
│       │   poor text selection, NOT designed for server-side
│       └── WARNING: AI agents frequently recommend this for server use
│
└── Need it serverless (Lambda, Vercel Functions)?
    └── PDFKit (no native deps) or pdf-lib (for modifications)
    └── NOT Puppeteer (Chrome binary doesn't fit in Lambda easily)
```

### PDFKit Server-Side Example

```javascript
import PDFDocument from 'pdfkit'

function generateInvoice(data) {
  const doc = new PDFDocument()
  const buffers = []

  doc.on('data', (chunk) => buffers.push(chunk))

  doc.fontSize(20).text('Invoice', { align: 'center' })
  doc.moveDown()

  // Table-like layout
  data.lineItems.forEach((item) => {
    doc.fontSize(10)
       .text(item.description, 50, doc.y, { width: 300 })
       .text(`$${item.amount.toFixed(2)}`, 400, doc.y - 12, { align: 'right' })
  })

  doc.end()

  return new Promise((resolve) => {
    doc.on('end', () => resolve(Buffer.concat(buffers)))
  })
}
```

### Puppeteer HTML-to-PDF Example

```javascript
import puppeteer from 'puppeteer'

async function htmlToPdf(html) {
  const browser = await puppeteer.launch({ headless: true })
  const page = await browser.newPage()
  await page.setContent(html, { waitUntil: 'networkidle0' })

  const pdf = await page.pdf({
    format: 'A4',
    printBackground: true,  // Include CSS background colors
    margin: { top: '1cm', bottom: '1cm', left: '1cm', right: '1cm' },
  })

  await browser.close()
  return pdf  // Buffer
}
```

### Quick Comparison

| Library | Use Case | Server-Side | Browser | Native Deps | npm weekly |
|---------|----------|-------------|---------|-------------|------------|
| **PDFKit** | Generate from data | Yes (primary) | No | None | ~1M |
| **Puppeteer** | HTML → PDF | Yes (primary) | No | Chrome | ~4M |
| **pdf-lib** | Modify existing PDFs | Yes | Yes | None | ~1.5M |
| **jsPDF** | Client-side generation | Awkward | Yes (primary) | None | ~1.5M |

## Lessons Learned

- **jsPDF is the #1 wrong recommendation.** AI agents see its high download count and recommend it for server-side Express/Next.js routes. It produces image-based PDFs via html2canvas — text is rasterized, not selectable, and blurry at non-native zoom levels.
- **pdf-lib is for modification, not generation.** It can create pages and add text, but it has no layout engine. For anything beyond simple text placement, use PDFKit.
- **Puppeteer needs Chrome in production.** This means ~300MB added to your Docker image or Lambda layer. For serverless, consider `@sparticuz/chromium` (optimized Chromium for Lambda) or switch to PDFKit.
- **PDFKit streams naturally.** `doc.pipe(res)` sends PDF directly to the HTTP response — no buffering the entire file in memory. This is ideal for server-side generation.
- **Playwright is a Puppeteer alternative** with the same HTML-to-PDF capability via `page.pdf()`. Choose based on which you already use for testing.

## Do / Don't

**Do:** Use PDFKit for programmatic server-side PDF generation (invoices, reports, data-driven documents). Use Puppeteer/Playwright when you have HTML/CSS templates you want to render as PDF. Use pdf-lib for filling forms, merging PDFs, or stamping watermarks.

**Don't:** Use jsPDF for server-side PDF generation — it's browser-oriented and produces image-based output. Don't use Puppeteer in serverless without accounting for the Chrome binary size and cold start cost. Don't use pdf-lib as your primary generation library for complex layouts.

## Cross-References

- Principles: meta-quality-structured-output-enforcement, coding-quality-supply-chain-solution-integrity
- Methods: §9.4 (Document Generation Patterns), §9.4.4 (Library Selection Quick Reference)
- See also: ref-ai-coding-web-app-file-downloads, ref-ai-coding-python-pdf-generation, ref-ai-coding-node-excel-generation
