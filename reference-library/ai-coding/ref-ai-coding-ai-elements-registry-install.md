---
id: ref-ai-coding-ai-elements-registry-install
title: "Vercel AI Elements: shadcn/ui Registry Install Pattern for Chat UI"
domain: ai-coding
tags: ["vercel-ai-sdk", "shadcn", "nextjs", "chat-ui", "registry", "streaming", "react"]
status: current
entry_type: direct
summary: "Install pattern for Vercel AI Elements chat components via shadcn/ui registry — source-copied (not npm), post-install cleanup required (remove unused plugins), integrates with existing useChat hook"
created: 2026-05-14
last_verified: 2026-05-14
maturity: seedling
decay_class: framework
source: "Captured via capture_reference tool"
---

## Context

Use when building chat UIs with Vercel AI SDK v6+. AI Elements provides pre-built message rendering, prompt input, and code block components that work with the same useChat hook. Key advantage: zero integration friction if already using AI SDK. Components are Apache 2.0, source-copied into your project (you own the code). Selected over assistant-ui (adds unnecessary runtime abstraction) and react-markdown (doesn't handle streaming incomplete markdown well).

## Artifact

## Install Commands

```bash
# 1. Install npm dependencies
npm install streamdown @streamdown/code shiki use-stick-to-bottom

# 2. Install AI Elements components via registry (copies source files)
npx shadcn@latest add https://elements.ai-sdk.dev/api/registry/message.json
npx shadcn@latest add https://elements.ai-sdk.dev/api/registry/prompt-input.json
npx shadcn@latest add https://elements.ai-sdk.dev/api/registry/code-block.json
```

## Post-Install Cleanup (REQUIRED)

The registry installs unused plugins by default. In the generated `message.tsx`:

1. Remove `@streamdown/mermaid` import and `mermaid` key from `streamdownPlugins` (eliminates dangerouslySetInnerHTML, removes ~2MB mermaid dep from bundle)
2. Remove `@streamdown/math` import and `math` key (eliminates KaTeX dep)
3. Remove `@streamdown/cjk` import if not needed
4. Only keep `@streamdown/code` (shiki syntax highlighting)

## Tighten rehype-harden Config

Override wildcard defaults in your local `message.tsx`:

```typescript
// In the Streamdown component props or wrapper
const hardenConfig = {
  allowedLinkPrefixes: ["https://"],
  allowedImagePrefixes: ["https://your-supabase-url.supabase.co/"],
  allowedProtocols: ["https:", "mailto:"],
  allowDataImages: false,
  defaultOrigin: "https://your-app.vercel.app",
};
```

## Integration with Existing useChat

AI Elements uses the same `useChat` from `@ai-sdk/react`. No transport changes needed:

```typescript
const { messages, input, handleSubmit, ... } = useChat({
  transport: new DefaultChatTransport({
    api: '/api/chat',
    body: { conversationId }, // custom body still works
  }),
});
```

## Security Rules

- Render user messages with `<MessageContent>` (plain text)
- Render AI responses with `<MessageResponse>` (streamdown markdown)
- NEVER pass user messages through `<MessageResponse>`/`<Streamdown>`
- Configure shiki to load only needed languages (~8, not all 200+)
- Pin `use-stick-to-bottom` to exact version (single maintainer package)

## What You Get

- `message.tsx` → Message component with streamdown markdown, code highlighting
- `prompt-input.tsx` → Auto-resizing textarea with shift+enter support
- `code-block.tsx` → Syntax-highlighted code blocks with copy button
- Components go to `src/components/` (or your shadcn components path)
- Source files committed to git — you own them, no auto-updates

## Lessons Learned

1. The registry declares more npm deps than you need (mermaid, math, cjk) — always review and trim post-install. 2. Components are source-copied, meaning security patches require manual re-install — track upstream versions. 3. No integrity verification on registry content (standard for shadcn pattern) — review generated source before committing. 4. Mermaid uses dangerouslySetInnerHTML for SVG rendering — removing the plugin eliminates this attack vector entirely. 5. use-stick-to-bottom has a single maintainer (samdd@StackBlitz) and zero deps — consider vendoring the ~200-line hook for supply chain safety.

## Cross-References

- Principles: [relevant principle IDs]
- Methods: [relevant method section refs]
- See also: [related entry IDs]
