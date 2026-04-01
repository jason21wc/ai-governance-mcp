---
id: ref-ai-coding-nextjs-middleware-auth-exemptions
title: "Next.js Middleware Auth Redirect Exemption Pattern"
domain: ai-coding
tags: ["nextjs", "middleware", "auth", "routing", "api-routes", "supabase"]
status: current
entry_type: direct
summary: "Next.js auth middleware must exempt API routes (401 not redirect), auth callback routes, and post-auth pages like /reset-password from redirect rules"
created: 2026-04-01
last_verified: 2026-04-01
maturity: budding
decay_class: framework
source: "Captured via capture_reference tool"
---

## Context

Three non-obvious exemption categories: (1) API routes must return 401, not redirect — 307 breaks fetch clients; (2) /auth/* callbacks must pass through; (3) post-PKCE pages like /reset-password where user IS authenticated. Proven in ai-expert (L046, L056).

## Artifact

const isAuthPath = pathname.startsWith('/sign-in') || pathname.startsWith('/sign-up') ||
  pathname.startsWith('/forgot-password') || pathname.startsWith('/reset-password') ||
  pathname.startsWith('/auth/')
const isApiPath = pathname.startsWith('/api/')

if (!user &amp;&amp; !isAuthPath &amp;&amp; !isApiPath) {
  return NextResponse.redirect(new URL('/sign-in', request.url))
}
if (user &amp;&amp; isAuthPath &amp;&amp; !pathname.startsWith('/auth/') &amp;&amp; !pathname.startsWith('/reset-password')) {
  return NextResponse.redirect(new URL('/', request.url))
}

## Lessons Learned

- API routes MUST be excluded — 307 breaks POST/PUT/DELETE fetch clients
- /reset-password: after PKCE exchange user IS authenticated, naive redirect-away rule blocks them
- When adding new auth flows, ask: will the user be authenticated when they land here?

## Cross-References

- Principles: [relevant principle IDs]
- Methods: [relevant method section refs]
- See also: [related entry IDs]
