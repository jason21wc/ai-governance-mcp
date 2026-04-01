---
id: ref-ai-coding-playwright-auth-setup-pattern
title: "Playwright Auth Setup Project with Supabase + .env.local"
domain: ai-coding
tags: ["playwright", "e2e-testing", "auth", "supabase", "nextjs", "storage-state"]
status: current
entry_type: direct
summary: "Playwright auth setup project: sign in once, save storage state, reuse across test projects with .env.local credentials and exact:true for strict mode"
created: 2026-04-01
last_verified: 2026-04-01
maturity: budding
decay_class: framework
source: "Captured via capture_reference tool"
---

## Context

E2E tests need single sign-in with session reuse. Requires dotenv for .env.local, storage state file, setup dependency, and exact:true on getByRole. Proven in ai-expert (L053, 24 E2E tests).

## Artifact

// playwright.config.ts
import dotenv from 'dotenv'
dotenv.config({ path: path.resolve(__dirname, '.env.local') })
const STORAGE_STATE = path.join(__dirname, 'playwright/.auth/user.json')

export default defineConfig({
  projects: [
    { name: 'setup', testMatch: /.*\.setup\.ts/ },
    { name: 'authenticated', use: { storageState: STORAGE_STATE }, dependencies: ['setup'], testIgnore: /.*unauthenticated.*/ },
    { name: 'unauthenticated', testMatch: /.*unauthenticated.*/ },
  ],
})

// auth.setup.ts
setup('authenticate', async ({ page }) => {
  await page.goto('/sign-in')
  await page.getByLabel('Email').fill(process.env.E2E_TEST_EMAIL!)
  await page.getByLabel('Password').fill(process.env.E2E_TEST_PASSWORD!)
  await page.getByRole('button', { name: 'Sign In', exact: true }).click()
  await page.waitForURL('/')
  await page.context().storageState({ path: STORAGE_STATE })
})

## Lessons Learned

- Use dotenv for .env.local — Playwright doesn't load Next.js env files
- Add playwright/.auth/ to .gitignore
- Use { exact: true } on getByRole to avoid strict mode violations
- Split authenticated/unauthenticated projects

## Cross-References

- Principles: [relevant principle IDs]
- Methods: [relevant method section refs]
- See also: [related entry IDs]
