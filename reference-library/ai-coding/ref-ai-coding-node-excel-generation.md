---
id: ref-ai-coding-node-excel-generation
title: "Node.js Excel Generation: ExcelJS over SheetJS CE"
domain: ai-coding
tags: [excel, node, document-generation, library-selection, exceljs, sheetjs]
status: current
entry_type: direct
summary: "ExcelJS is the correct choice for Node.js Excel generation with formatting. SheetJS Community Edition has limited styling support on write — Pro edition required for full styling."
created: 2026-04-03
last_verified: 2026-04-03
maturity: budding
decay_class: framework
source: "Web research (pkgpulse.com, mfyz.com, npmtrends.com comparisons, 2025-2026). SheetJS CE limitation confirmed across multiple independent sources."
related: [ref-ai-coding-web-app-file-downloads, ref-ai-coding-node-pdf-generation]
---

## Context

AI agents frequently recommend SheetJS (npm package `xlsx`) for Node.js Excel generation because it has higher download counts and more training data presence (~36k GitHub stars). However, the free Community Edition has limited styling support on write — headers won't have background colors, text won't be bold, column widths won't auto-fit. The Pro edition supports full styling but is paid. ExcelJS (MIT license, ~15k stars) has full styling and streaming support for free.

This is the #1 library selection trap for Node.js Excel generation.

## Artifact

### Decision Tree

```
Need to generate .xlsx in Node.js?
├── Need formatting (colors, bold, column widths, number formats)?
│   └── ExcelJS — full styling, streaming, MIT license
├── Need to READ/PARSE existing Excel files?
│   └── SheetJS CE — excellent for parsing, free
├── Simple data export, no formatting needed?
│   └── Either works — SheetJS CE is fine for unstyled data dumps
└── Need both read and styled write?
    └── SheetJS for reading, ExcelJS for writing
```

### ExcelJS Styled Generation Example

```javascript
import ExcelJS from 'exceljs'

const workbook = new ExcelJS.Workbook()
const sheet = workbook.addWorksheet('Report')

// Header row with styling
const headerRow = sheet.addRow(['Name', 'Amount', 'Date'])
headerRow.eachCell((cell) => {
  cell.fill = {
    type: 'pattern',
    pattern: 'solid',
    fgColor: { argb: 'FF1F4E79' },  // Dark blue
  }
  cell.font = { color: { argb: 'FFFFFFFF' }, bold: true }
})

// Auto-fit column widths
sheet.columns.forEach((column) => {
  column.width = Math.max(12, column.header?.length + 2 || 12)
})

// Number formatting
sheet.getColumn(2).numFmt = '$#,##0.00'

// Write to buffer (for HTTP response)
const buffer = await workbook.xlsx.writeBuffer()
```

### Streaming for Large Files

```javascript
// ExcelJS streaming API for memory-efficient generation
const workbook = new ExcelJS.stream.xlsx.WorkbookWriter({
  stream: res,  // Pipe directly to HTTP response
})
const sheet = workbook.addWorksheet('Data')
// ... add rows — each row is flushed to stream
await workbook.commit()
```

## Lessons Learned

- SheetJS CE is excellent for **reading** Excel files — parsing is fully supported in the free edition. The limitation is specifically on **write styling**.
- AI agents recommend SheetJS by default because it dominates npm download counts. Always verify the styling limitation when the task involves formatted output.
- ExcelJS supports both in-memory (`writeBuffer()`) and streaming (`stream.xlsx.WorkbookWriter`) APIs. Use streaming for files with >10K rows.
- ExcelJS handles formulas, conditional formatting, data validation, images, and merged cells — all in the free MIT-licensed package.

## Do / Don't

**Do:** Use ExcelJS for any Excel generation that needs formatting (styled headers, number formats, column widths, conditional formatting). Use SheetJS CE for reading/parsing Excel files.

**Don't:** Use SheetJS CE for styled Excel generation unless you have the Pro license. Don't assume that higher npm download counts mean the library is better for your specific use case — SheetJS's downloads are inflated by its excellent read/parse capabilities.

## Cross-References

- Principles: meta-quality-structured-output-enforcement, coding-quality-supply-chain-solution-integrity
- Methods: §9.4 (Document Generation Patterns), §9.4.4 (Library Selection Quick Reference)
- See also: ref-ai-coding-web-app-file-downloads, ref-ai-coding-node-pdf-generation
