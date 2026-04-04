---
id: ref-ai-coding-supabase-jwt-hook-ssr
title: "Supabase JWT Hook Claims in Next.js SSR"
domain: ai-coding
tags: ["supabase", "jwt", "nextjs", "ssr", "auth", "custom-claims"]
status: current
entry_type: direct
summary: "When using Supabase custom access token hooks, read claims from decoded JWT access_token — not session.user.app_metadata (which returns DB metadata only)"
created: 2026-04-01
last_verified: 2026-04-01
maturity: budding
decay_class: framework
source: "Captured via capture_reference tool"
related: [ref-ai-coding-supabase-ssr-async-setall]
---

## Context

supabase.auth.getSession().user.app_metadata returns DATABASE app_metadata, not JWT hook-injected claims. Must decode session.access_token directly. Undocumented by Supabase. Proven in ai-expert project (L052).

## Artifact

const getJwtClaims = cache(async () => {
  const supabase = await createClient()
  const { data: { session } } = await supabase.auth.getSession()
  if (!session?.access_token) return null
  try {
    const payload = JSON.parse(
      Buffer.from(session.access_token.split('.')[1], 'base64url').toString()
    )
    return payload.app_metadata as Record<string, unknown> | undefined
  } catch { return null }
})

## Lessons Learned

- getSession().user.app_metadata returns DB fields only — NOT JWT hook claims. Fails SILENTLY.
- React.cache() deduplicates across multiple helpers in the same request
- This is the SSR equivalent of auth.jwt() in RLS policies

## Do / Don't

**Do:** Decode `session.access_token` directly to read JWT hook-injected custom claims. Use `Buffer.from(token.split('.')[1], 'base64url')`.

**Don't:** Read `session.user.app_metadata` expecting JWT hook claims — returns database `app_metadata` only, not hook-injected claims. Fails silently (returns stale/empty data, no error).

## Cross-References

- Principles: coding-context-specification-completeness, coding-quality-production-ready-standards
- Methods: §3.1.5 (Library-Specific Knowledge Sources), §5.13.2 (Diagnostic Block Requirement)
- See also: ref-ai-coding-supabase-ssr-async-setall
