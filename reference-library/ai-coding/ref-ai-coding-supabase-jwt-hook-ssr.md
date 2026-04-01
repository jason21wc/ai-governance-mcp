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
    return payload.app_metadata as Record&lt;string, unknown&gt; | undefined
  } catch { return null }
})

## Lessons Learned

- getSession().user.app_metadata returns DB fields only — NOT JWT hook claims. Fails SILENTLY.
- React.cache() deduplicates across multiple helpers in the same request
- This is the SSR equivalent of auth.jwt() in RLS policies

## Cross-References

- Principles: [relevant principle IDs]
- Methods: [relevant method section refs]
- See also: [related entry IDs]
