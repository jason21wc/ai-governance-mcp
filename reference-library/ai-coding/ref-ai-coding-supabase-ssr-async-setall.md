---
id: ref-ai-coding-supabase-ssr-async-setall
title: "Supabase SSR Async setAll Fix for Auth Callback"
domain: ai-coding
tags: ["nextjs", "supabase", "cookies", "pkce", "auth-callback", "async"]
status: current
entry_type: direct
summary: "@supabase/ssr fires setAll async via onAuthStateChange after exchangeCodeForSession resolves — must await setAll via Promise before returning redirect response"
created: 2026-04-01
last_verified: 2026-04-01
maturity: budding
decay_class: framework
source: "Captured via capture_reference tool"
---

## Context

Both cookies() and response.cookies.set() fail because setAll fires async. Fix: wrap setAll in a Promise and await before returning redirect. Proven in ai-expert (L058). Official Supabase pattern also fails on Next.js 16.1.3 + @supabase/ssr 0.8.0.

## Artifact

let resolveSetAll: () => void
const setAllPromise = new Promise&lt;void&gt;((resolve) => { resolveSetAll = resolve })

const supabase = createServerClient(url, key, {
  cookies: {
    getAll() { /* parse from request headers */ },
    setAll(cookiesToSet) {
      cookiesToSet.forEach(({ name, value, options }) => {
        response.cookies.set(name, value, options)
      })
      resolveSetAll!()
    },
  },
})

const { error } = await supabase.auth.exchangeCodeForSession(code)
if (!error) {
  await Promise.race([setAllPromise, new Promise&lt;void&gt;(r => setTimeout(r, 5000))])
  return response
}

## Lessons Learned

- CORRECTS prior wrong diagnosis (L056): issue is NOT cookies() vs response.cookies.set(). BOTH fail because setAll fires async via onAuthStateChange.
- Promise.race with 5s timeout prevents hanging
- Prior session's wrong diagnosis led to 3 wasted attempts — re-verify cached conclusions when stack versions change

## Cross-References

- Principles: [relevant principle IDs]
- Methods: [relevant method section refs]
- See also: [related entry IDs]
