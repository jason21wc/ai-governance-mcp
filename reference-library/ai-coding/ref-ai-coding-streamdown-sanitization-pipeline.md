---
id: ref-ai-coding-streamdown-sanitization-pipeline
title: "Streamdown Markdown Sanitization Pipeline for AI Chat"
domain: ai-coding
tags: ["security", "xss", "markdown", "streaming", "sanitization", "rehype", "react"]
status: current
entry_type: direct
summary: "Streamdown's full sanitization pipeline for rendering AI-generated markdown safely — pipeline ordering, default schema, rehype-harden wildcard fix, user vs AI message separation"
created: 2026-05-14
last_verified: 2026-05-14
maturity: seedling
decay_class: framework
source: "Captured via capture_reference tool"
---

## Context

Use when rendering LLM-generated content as markdown in any web application. The key insight is that switching from plain text (whitespace-pre-wrap) to markdown rendering is a deliberate trade from "XSS-impossible" to "XSS-mitigated via sanitization." The sanitization must never be bypassed. Streamdown handles this correctly by default, but the rehype-harden plugin ships with wildcard config that nullifies its URL-origin restrictions. RAG-injected content (document chunks containing HTML/script payloads) flows through the same pipeline — the sanitization handles it, but the safety depends on the plugin chain remaining intact.

## Artifact

## Streamdown Sanitization Pipeline (in order)

```
1. remark-parse          → Parses markdown to MDAST
2. remark-gfm            → GFM support (tables, strikethrough)
3. remark-rehype          → Converts to HAST (allowDangerousHtml: true)
4. rehype-raw             → Re-parses raw HTML nodes into proper HAST
5. rehype-sanitize        → Allowlist filter (GitHub's defaultSchema)
6. rehype-harden          → URL validation + link safety
7. hast-util-to-jsx-runtime → React elements (NO dangerouslySetInnerHTML)
```

**Pipeline ordering is critical:** Raw HTML is parsed BEFORE sanitization (steps 4→5), not after.

## What rehype-sanitize Blocks

Based on GitHub's `defaultSchema` from `hast-util-sanitize`:
- All `<script>`, `<style>`, `<iframe>`, `<object>`, `<embed>`, `<form>` tags
- All event handlers (`onclick`, `onerror`, etc.)
- `javascript:` protocol in URLs (only `http`, `https`, `mailto`, `tel` allowed)

## rehype-harden Default Config Problem

```typescript
// DEFAULT (ships with streamdown) — TOO PERMISSIVE
{
  allowedImagePrefixes: ["*"],    // allows any image URL
  allowedLinkPrefixes: ["*"],     // allows any link URL
  allowedProtocols: ["*"],        // allows any protocol
  defaultOrigin: undefined,
  allowDataImages: true,          // allows data-URI images (tracking pixels)
}
```

**Still safe against XSS** because `blockedProtocols` set blocks `javascript:`, `vbscript:`, `file:`, bare `data:` links. But defense-in-depth is nullified.

## Recommended Override

```typescript
const hardenConfig = {
  allowedLinkPrefixes: ["https://"],
  allowedImagePrefixes: ["https://your-trusted-domain.com/"],
  allowedProtocols: ["https:", "mailto:"],
  allowDataImages: false,
  defaultOrigin: "https://your-app.com",
};
```

## User vs AI Message Rendering (CRITICAL)

```typescript
// CORRECT — user messages as plain text, AI through streamdown
{message.role === 'user' ? (
  <MessageContent>{message.content}</MessageContent>  // plain text
) : (
  <MessageResponse>{message.content}</MessageResponse> // streamdown markdown
)}
```

**Why:** Even with sanitization, rendering user-controlled markdown increases social engineering surface (phishing links, misleading formatting). Plain text for user messages = XSS-impossible for that path.

## SafeMarkdown Wrapper Pattern

```typescript
// Wrap streamdown to prevent accidentally bypassing sanitization
function SafeMarkdown({ content }: { content: string }) {
  return (
    <Streamdown
      rehypePlugins={[
        rehypeRaw,
        [rehypeSanitize, defaultSanitizeSchema],
        [rehypeHarden, hardenConfig],
      ]}
    >
      {content}
    </Streamdown>
  );
}
// SECURITY: Never pass custom rehypePlugins without rehypeSanitize.
```

## RAG Content Safety

Document chunks with embedded HTML/script payloads flow through LLM responses into streamdown. The sanitization pipeline handles this correctly by default. The threat model:
1. Malicious document uploaded → chunks stored → RAG retrieves → LLM quotes verbatim
2. `<script>` tags stripped by rehype-sanitize (step 5)
3. Event handlers stripped
4. Only whitelisted tags/attributes pass through

Safety depends on the plugin chain remaining intact — if a developer later passes custom `rehypePlugins` omitting `rehypeSanitize`, XSS becomes possible.

## Lessons Learned

1. Moving from plain text to markdown rendering is a security model change — document it as a deliberate decision, not an incremental feature. 2. The default rehype-harden wildcard config provides a false sense of security — always override with explicit prefixes. 3. rehype-sanitize uses GitHub's schema which is one of the most battle-tested HTML sanitization allowlists. 4. streamdown is marked "use client" — ProcessorCache is browser-only, no cross-tenant leakage in SSR. 5. Link safety feature (enabled by default) shows confirmation modal before navigating to external URLs — good defense against phishing in AI responses. 6. Links default to target="_blank" rel="noreferrer" preventing reverse tabnabbing.

## Cross-References

- Principles: [relevant principle IDs]
- Methods: [relevant method section refs]
- See also: [related entry IDs]
