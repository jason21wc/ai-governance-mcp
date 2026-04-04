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
related: [ref-ai-coding-supabase-ssr-async-setall, ref-ai-coding-playwright-auth-setup-pattern]
---

## Context

Three non-obvious exemption categories: (1) API routes must return 401, not redirect — 307 breaks fetch clients; (2) /auth/* callbacks must pass through; (3) post-PKCE pages like /reset-password where user IS authenticated. Proven in ai-expert (L046, L056).

## Artifact

const isAuthPath = pathname.startsWith('/sign-in') || pathname.startsWith('/sign-up') ||
  pathname.startsWith('/forgot-password') || pathname.startsWith('/reset-password') ||
  pathname.startsWith('/auth/')
const isApiPath = pathname.startsWith('/api/')

if (!user && !isAuthPath && !isApiPath) {
  return NextResponse.redirect(new URL('/sign-in', request.url))
}
if (user && isAuthPath && !pathname.startsWith('/auth/') && !pathname.startsWith('/reset-password')) {
  return NextResponse.redirect(new URL('/', request.url))
}

## Lessons Learned

- API routes MUST be excluded — 307 breaks POST/PUT/DELETE fetch clients
- /reset-password: after PKCE exchange user IS authenticated, naive redirect-away rule blocks them
- When adding new auth flows, ask: will the user be authenticated when they land here?

## Do / Don't

**Do:** Exempt API routes from auth redirects — return 401 status instead. Exempt `/auth/*` callback routes. Exempt post-PKCE pages like `/reset-password` where the user IS authenticated after the code exchange.

**Don't:** Apply a blanket "no user → redirect to sign-in" rule to all routes. 307 redirects break API `fetch` clients (POST/PUT/DELETE). Don't redirect authenticated users away from `/reset-password` — after PKCE exchange the user has a valid session and needs to reach that page. Don't add new auth-adjacent routes without asking: "will the user be authenticated when they land here?"

## Cross-References

- Principles: coding-context-specification-completeness, coding-quality-production-ready-standards
- Methods: §3.1.5 (Library-Specific Knowledge Sources), §5.13.2 (Diagnostic Block Requirement)
- See also: ref-ai-coding-supabase-ssr-async-setall, ref-ai-coding-playwright-auth-setup-pattern
