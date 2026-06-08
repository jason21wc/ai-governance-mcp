---
description: Transform raw content (transcripts, articles, lectures, informal posts) into enhanced reference documents — removes noise, restructures for clarity, fills knowledge gaps with researched best practices, preserves the author's voice. Invoke when the user provides source content to enhance, clean up, or transform into a useful reference document.
disable-model-invocation: true
allowed-tools: Bash Read Edit Write WebSearch WebFetch
---

## Context Snapshot

**Today:** !`date "+%Y-%m-%d"`

## Instructions

You are running the content enhancer skill. Read `procedure.md` in this skill folder for the full 5-step protocol.

### Execution Protocol

1. **Call `evaluate_governance(planned_action="content enhancement")`** before any writes.

2. **Get the source content.** If the user has not already provided it, ask: "What content would you like me to enhance? You can paste text, provide a file path, or share a URL."

3. **Extract visual content (if source is a file with embedded images).** Skip this step for pasted text, transcripts, or text-only sources.

   **Format detection → strategy.** Identify the source format and map it to an extraction *strategy* — the format determines the mechanism, not just the parser:

   | Source type | Strategy |
   |---|---|
   | Embedded raster (PDF, DOCX, HTML, Markdown) | **Extract** embedded images (below) |
   | Native-rendered deck (PPTX with shapes/charts) | **Render** slides if LibreOffice present, **else escalate** to user PDF export |
   | Legacy binary (`.doc`, `.ppt`) | **Convert first** to a modern format, then re-run detection |
   | Tabular (XLSX / spreadsheet) | **Tabularize** → Markdown tables (not image extraction) |
   | Multi-file folder | **Orchestrate** across files (below) |
   | Unknown / encrypted / corrupt | **Escalate** (terminal branches, below) |

   **Web-sourced visuals are gap-filling, not extraction.** If a *visual gap* needs a figure the provided source lacks, handle it via the Gap-Filling Protocol's visual lane (re-express data as a table, or link+describe) — **never** embed or synthesize a third-party image. This Step-3 path applies only to images already present in a provided source.

   **Output directory setup:**
   ```bash
   mkdir -p enhanced/{slug}
   ```
   `{slug}` = slugified document title or filename (lowercase, hyphens for spaces, no special characters). If the user provides a name, use it. The enhanced document will be written to `enhanced/{slug}/index.md`.

   **Prerequisite check (once per session):**
   ```bash
   python3 -c "import fitz; print(f'PyMuPDF {fitz.version}')" 2>/dev/null || echo "PyMuPDF not available"
   python3 -c "from docx import Document; print('python-docx available')" 2>/dev/null || echo "python-docx not available"
   python3 -c "import openpyxl; print('openpyxl available')" 2>/dev/null || echo "openpyxl not available"   # XLSX -> tables
   command -v soffice >/dev/null && echo "LibreOffice available" || echo "LibreOffice not available"        # PPTX render / .doc convert
   command -v textutil >/dev/null && echo "textutil available" || echo "textutil not available"             # macOS .doc convert
   ```
   Record availability. **Do not install packages during enhancement.** If the strategy a source needs has no available tool, take that strategy's escalation branch (below) — never block or crash; degrade to text-only for that source and tell the user what to provide.

   **Optional one-time setup (enables the render + convert strategies).** Installing LibreOffice (`brew install --cask libreoffice` on macOS) puts `soffice` on PATH, which turns the **PPTX render** and **legacy `.doc`/`.ppt` convert** strategies from "escalate to the user" into automatic. Verified: `soffice --headless --convert-to pdf deck.pptx` renders native-shape decks that have *no* extractable `ppt/media/` (then process the PDF with the PDF strategy). On macOS this installs the full app (used only via the CLI). Without it, the per-strategy escalation branches below apply — nothing breaks, the user just exports/saves manually.

   **Extract by format:**

   *PDF (PyMuPDF):*
   ```python
   import fitz
   doc = fitz.open("source.pdf")
   n = 1
   for page in doc:
       for img in page.get_images():
           xref = img[0]
           data = doc.extract_image(xref)
           ext = data["ext"]  # original format preserved
           with open(f"enhanced/{slug}/fig-{n:02d}-{descriptor}.{ext}", "wb") as f:
               f.write(data["image"])
           n += 1
   ```
   `extract_image` returns the original encoded bytes — no re-encoding, original resolution preserved.

   *DOCX (ZIP extraction):*
   ```bash
   unzip -j source.docx 'word/media/*' -d /tmp/docx-extract-$$
   # Rename and copy each image to enhanced/{slug}/fig-{NN}-{descriptor}.{ext}
   ```
   DOCX files are ZIP archives. Images in `word/media/` are already separate files in their original format.

   *HTML (download referenced images):*
   ```bash
   curl -sL -o "enhanced/{slug}/fig-{NN}-{descriptor}.{ext}" "https://example.com/image.png"
   ```

   *Markdown (copy referenced images):*
   ```bash
   cp source-dir/images/diagram.png "enhanced/{slug}/fig-01-diagram.png"
   ```
   Resolve paths in `![](...)` syntax relative to the source file's location.

   *PPTX (PowerPoint) — render or escalate:* PPTX is a ZIP; if `ppt/media/` holds rasters, extract them like DOCX (`unzip -j source.pptx 'ppt/media/*' -d ...`). **But native-shape decks (text boxes, SmartArt, charts) have an empty `ppt/media/`** — those slides are vector-rendered and cannot be image-extracted. If `soffice` is present: `soffice --headless --convert-to pdf source.pptx`, then process the PDF. **If not (common), escalate:** "This deck's visuals are native PowerPoint shapes, not embedded images — export it to PDF (File → Export → PDF) and I'll process that." *(Residual limitation: native-shape PPTX is not auto-processable without LibreOffice.)*

   *Legacy binary (`.doc`, `.ppt`) — convert first:* pre-2007 binary formats can't be read by python-docx/PyMuPDF — convert, then re-run detection on the result. macOS: `textutil -convert docx "source.doc"` (or `-convert html` to preserve tables); cross-platform: `soffice --headless --convert-to docx source.doc`. Check for non-UTF8 text after conversion. If neither tool exists, escalate: ask the user to re-save as `.docx`/PDF.

   *Tabular (XLSX / spreadsheet) — tabularize, don't image-extract:* a spreadsheet is **data, not an image source** — render its sheets/ranges as Markdown tables. Read values with openpyxl (`load_workbook(path, read_only=True, data_only=True)` — `data_only` yields computed values, not formula strings; pattern per `reference-library/ai-coding/ref-example.md`) or pandas, and emit a Markdown table per relevant sheet. Only extract `xl/media/*` (it's a ZIP) if the workbook embeds genuine charts/diagrams worth showing as figures.

   *Multi-file folder (multiple sources) — orchestrate:* (1) **dedup** byte-identical sources first (`md5`) — a duplicated manual contributes nothing. (2) Number figures **globally** in final-document order across all sources (`fig-01..NN`), not per file. (3) For large sources (hundreds of pages / thousands of images that are mostly repeated chrome), **do not bulk-extract** — select figures *content-driven*: for each section/procedure of the target document, pull the one image that supports it; filter chrome by minimum dimensions and dedup. Parallel per-section-group selection scales this (one reviewer per group, each *viewing* candidates before choosing).

   *Unknown / encrypted / corrupt (terminal branches):* unknown extension or a format with no strategy above → escalate: "I don't have an extraction method for [format] — export to PDF/DOCX/HTML, or provide the images separately." A password-protected or corrupt ZIP-container file (PPTX/XLSX/DOCX are all ZIPs) will fail to open → do **not** crash: report "[file] is encrypted or corrupt — provide an unlocked copy," skip it, and proceed text-only for the rest.

   **Image naming:** `fig-{NN}-{descriptor}.{ext}` — sequential by document order. Descriptor is 2-4 words from caption or content description (e.g., `fig-01-revenue-comparison.png`). Preserve original extension (JPEG stays JPEG, PNG stays PNG).

   **Failure handling:**

   | Failure | Action |
   |---------|--------|
   | Tool not installed | Escalate to user with install command |
   | Image corrupt or zero-byte | Insert `[Image extraction failed: {filename}]` placeholder, continue |
   | Source has no extractable images | Note and proceed as text-only (§1.4 skip gate applies) |
   | Native-shape PPTX (empty `ppt/media/`) | Render via LibreOffice if present, else escalate to user PDF export |
   | Encrypted / corrupt container (PPTX/XLSX/DOCX) | Report "[file] encrypted or corrupt", skip it, continue with the rest |
   | Multiple source files | md5-dedup; global sequential numbering; content-driven selection (see *Multi-file folder* above) |

4. **Read `procedure.md`** — it contains the complete processing protocol.

5. **Execute all 5 steps in order:**
   - Step 1: **Triage** — assess competence, identify audience, determine use context. STOP and escalate if any triage gate fails.
   - Step 2: **Analyze** — classify content type, separate core facts from presentation, fingerprint the voice. Inventory extracted images per §2.5.
   - Step 3: **Enhance** — restructure, clean, fill gaps per the gap-filling protocol. Enhance image metadata per §3.5. Apply voice preservation constraint throughout.
   - Step 4: **Assemble** — build the output document in the right format for the audience and use context. Place images per §4.4.
   - Step 5: **Verify** — factual fidelity, voice check, adoption fitness, visual content verification per §5.4, research disclosure per §5.5. Fix any failures before delivering.

6. **Deliver the enhanced document** to the user. When images were extracted, the output is a page bundle directory (`enhanced/{slug}/`) — tell the user the path so they can browse images and provide feedback. If they want to store the content as a reference, they can use `capture_reference` separately.

7. **Generate distributable formats (optional).** The page bundle (`index.md` + `fig-*` files) is the single source of truth; convert to any format with pandoc. Markdown *references* images (`![](fig-01.png)`) rather than embedding them, so run pandoc **from inside the bundle directory** to keep relative paths resolving, and keep `index.md` and its figures together:
   ```bash
   cd enhanced/{slug}
   pandoc index.md -o {slug}.docx                          # Word — images embedded
   pandoc index.md -o {slug}.pdf                           # PDF — needs a LaTeX/HTML engine
   pandoc index.md --reference-doc=house-style.docx -o {slug}.docx   # apply house styles
   ```
   This is why the bundle is Markdown: one source, regenerate Word/PDF/HTML on demand. Verify the output embeds every figure (`unzip -l {slug}.docx | grep media` for docx).

### Key Principles

- **Voice preservation is the #1 risk.** If the output sounds like generic AI prose, you have failed. Re-read Step 3.4 in the procedure.
- **Flag what you add, and disclose its grounding.** Use `[Editor's note: ...]` for AI-added facts and context. When a fill was externally researched, cite the source URL inside the note (`[Source: name, URL]`); when it came from model knowledge, mark it `from general domain knowledge, not externally verified`. Structural improvements are the expected value — don't annotate them. (Procedure §5.5 checks this before delivery.)
- **Coherence over completeness.** Removing extraneous material improves comprehension more than adding material. When in doubt, cut.
- **When uncertain, ask.** Six explicit escalation conditions are defined in the procedure. Use them.

### Governance Citations

- `kmpd-quality-assurance-qa2-artifact-adoption-fitness` — output must be easier to use than the original
- `kmpd-training-tl1-audience-appropriate-design` — identify target audience before generating
- Storytelling `E1` Human Voice Preservation — augment, do not replace the author's voice
- Multimodal RAG `P1` Inline Image Integration — images placed at the step they support, not appended
- Multimodal RAG `P3` Image Selection Criteria — Coherence, Unique Value, and Proximity tests
- Multimodal RAG `P5` Accessibility Compliance — alt text for every image, WCAG 2.1 AA
- Multimodal RAG `R1` Image-Text Collocation — images adjacent to supporting text
- Multimodal RAG `R2` Descriptive Context — alt text + context descriptions for retrieval
- Multimodal RAG `V1` Cross-Modal Consistency — text descriptions must match what images show
- Multimodal RAG `CT1` Fragment-Level Source Attribution — researched gap-fills cite their source (name + URL)
- Multimodal RAG `CT2` Spatial Attribution for Visual Content — reference specific regions, not "the image" generically
