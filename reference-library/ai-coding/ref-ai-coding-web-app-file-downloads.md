---
id: ref-ai-coding-web-app-file-downloads
title: "Web App File Download Serving Patterns"
domain: ai-coding
tags: [file-download, web-app, streaming, s3, document-generation, fastapi, nextjs, express]
status: current
entry_type: direct
summary: "Patterns for serving generated files from web apps — direct serve, streaming, pre-signed URLs, background jobs. Framework-specific examples for FastAPI, Next.js, Express."
created: 2026-04-03
last_verified: 2026-04-03
maturity: budding
decay_class: framework
source: "Web research (davidmuraya.com, codeconcisely.com, fourtheorem.com, copyprogramming.com, 2025-2026). Common patterns across multiple production projects."
related: [ref-ai-coding-python-pdf-generation]
---

## Context

After generating a document (Excel, PDF, Word), the web app needs to serve it for download. This is where production bugs live — wrong headers cause browsers to display instead of download, concurrent requests collide on temp files, and large files exhaust memory. The right pattern depends on file size, concurrency, and deployment environment.

## Artifact

### Pattern 1: Direct Serve (In-Memory)

Best for: files <50MB, low-to-moderate concurrency.

**FastAPI:**
```python
from fastapi.responses import Response
import io

@app.get("/api/export")
async def export_report():
    buffer = io.BytesIO()
    # ... generate document into buffer ...
    buffer.seek(0)
    return Response(
        content=buffer.getvalue(),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": 'attachment; filename="report.xlsx"'}
    )
```

**Next.js App Router:**
```typescript
// app/api/export/route.ts
export async function GET() {
  const buffer = await generateReport()  // Returns Buffer
  return new Response(buffer, {
    headers: {
      'Content-Type': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      'Content-Disposition': 'attachment; filename="report.xlsx"',
    },
  })
}
```

**Express:**
```javascript
app.get('/api/export', async (req, res) => {
  const buffer = await generateReport()
  res.set({
    'Content-Type': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'Content-Disposition': 'attachment; filename="report.xlsx"',
  })
  res.send(buffer)
})
```

### Pattern 2: Pre-Signed URL (S3/R2)

Best for: high concurrency, serverless, files that need re-download.

```python
import boto3
from uuid import uuid4

s3 = boto3.client("s3")

def export_with_presigned_url(report_data: dict) -> str:
    """Synchronous — boto3 is not async-native.
    In async frameworks (FastAPI), call via run_in_executor."""
    buffer = generate_report(report_data)
    key = f"exports/{uuid4()}.xlsx"  # Unique key — no collision

    s3.put_object(Bucket="my-bucket", Key=key, Body=buffer.getvalue())

    url = s3.generate_presigned_url(
        "get_object",
        Params={"Bucket": "my-bucket", "Key": key},
        ExpiresIn=3600,  # 1 hour
    )
    return url
```

**Required:** S3/R2 lifecycle rule to auto-delete after N days. CORS configuration if client downloads directly.

### Common MIME Types

| Format | MIME Type |
|--------|----------|
| Excel (.xlsx) | `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` |
| PDF | `application/pdf` |
| Word (.docx) | `application/vnd.openxmlformats-officedocument.wordprocessingml.document` |
| PowerPoint (.pptx) | `application/vnd.openxmlformats-officedocument.presentationml.presentation` |
| CSV | `text/csv` |

## Lessons Learned

- **`Content-Disposition: attachment`** is the most commonly missed header. Without it, browsers try to display the file inline instead of downloading.
- **Fixed filenames are a concurrency bug.** Never write to `report.xlsx` on disk — use `uuid4()` or include a timestamp. In-memory buffers (`io.BytesIO()`) avoid this entirely.
- **Temp files need cleanup.** If you must write to disk, use Python's `tempfile.NamedTemporaryFile(delete=True)` or wrap in `try/finally`. AI agents frequently generate code that writes temp files without cleanup.
- **Pre-signed URL CORS:** If the client downloads directly from S3/R2, you need `AllowedOrigins` matching your domain (not `*` in production), `AllowedMethods: [GET]`, and `AllowedHeaders: [Content-Disposition]`.
- **Streaming vs buffering:** For files >50MB or high-concurrency scenarios, use streaming APIs (ExcelJS `workbook.xlsx.write(stream)`, PDFKit `doc.pipe(res)`). FastAPI's `StreamingResponse` accepts any iterable.

## Do / Don't

**Do:** Use in-memory buffers (`io.BytesIO()`, `Buffer`) for files <50MB. Use unique filenames (UUID) when writing to disk or S3. Always set `Content-Disposition: attachment`.

**Don't:** Write temp files with fixed names (concurrent request collision). Serve large files by buffering the entire file in memory. Use `Content-Disposition: inline` for downloadable documents. Skip lifecycle rules on S3/R2 export buckets.

## Cross-References

- Principles: meta-quality-structured-output-enforcement, coding-quality-production-ready-standards
- Methods: §9.4 (Document Generation Patterns), §9.4.3 (Download Serving Patterns)
- See also: ref-ai-coding-python-pdf-generation
