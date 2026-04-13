---
version: "1.0.0"
status: "active"
effective_date: "2026-03-08"
domain: "ui-ux"
governance_level: "federal-regulations"
---

# UI/UX Methods v1.0.0
## Operational Procedures for Building Interactive Software Interfaces

> **SYSTEM INSTRUCTION FOR AI AGENTS:**
> This methods document provides HOW-TO procedures for implementing UI/UX domain principles. It is subordinate to the domain principles document (title-15-ui-ux.md), which establishes WHAT governance applies.

**Version:** 1.0.0
**Status:** Active
**Effective Date:** 2026-03-08
**Governance Level:** Methods (SOPs) — subordinate to UI/UX Domain Principles

---

### Governance Hierarchy

```
Constitution (Meta-Principles)
  └─ UI/UX Domain Principles (Federal Statutes)
       └─ UI/UX Methods (This Document — Operational Procedures)
```

**Process vs. Substance:**
- For WHEN to do UX work → AI-Coding Methods §2.4 (UX Elaboration), §2.5 (Visual Design Specs)
- For WHAT good UX is → UI/UX Domain Principles + This Document

### Legal System Analogy

| Legal Concept | Framework Equivalent | Purpose |
|---------------|---------------------|---------|
| Bill of Rights | S-Series (constitution.md) | Immutable safety guardrails with veto authority |
| Constitution | Meta-Principles (constitution.md) | Universal reasoning laws |
| Federal Statutes | title-15-ui-ux.md | Domain-specific binding law |
| Rules of Procedure | rules-of-procedure.md | How the framework evolves and maintains itself |
| **Federal Regulations (CFR)** | **This document** | **Operational rules implementing statutes** |
| Agency SOPs | Tool-specific guides | Platform-specific execution |
| Case Law | Reference Library | Precedent from real application |

---

### Importance Tags Legend

| Tag | Meaning |
|-----|---------|
| **CRITICAL** | Must follow in all UI/UX work. Skipping creates accessibility or usability failures. |
| **IMPORTANT** | Should follow in most cases. Exceptions require documented rationale. |
| **OPTIONAL** | Recommended for quality. Apply when scope and timeline permit. |

---

## 1 Design-to-Code Workflow

**Importance: IMPORTANT — Bridges design intent and implementation**

**Implements:** DS3 (Design System Discovery), VH1 (Layout Composition), DS1 (Design Token Architecture)

### 1.1 Pre-Implementation Discovery Procedure

**Purpose:** Ensure the AI agent understands the existing design context before generating any UI code.

**Applies To:** Any task that involves creating or modifying interface components, pages, or layouts.

Before writing any UI code, perform **design system discovery**:

```
1. QUERY for existing design context:
   - query_project("design tokens CSS variables theme configuration")
   - query_project("component library shared components")
   - query_project("layout patterns page templates")

2. IDENTIFY the token system:
   - CSS custom properties (var(--spacing-md))
   - Tailwind config (tailwind.config.js/ts)
   - SCSS/Less variables
   - JS/TS theme objects (styled-components, MUI theme)
   - Design token JSON files

3. CATALOG existing components:
   - Button variants (primary, secondary, destructive, ghost)
   - Form elements (input, select, checkbox, radio)
   - Layout components (card, container, grid, stack)
   - Navigation components (nav, sidebar, tabs, breadcrumbs)

4. DOCUMENT the design system status:
   - "Complete": Tokens + components found → USE THEM
   - "Partial": Some tokens/components → USE what exists, NOTE gaps
   - "None": No design system → RECOMMEND establishing tokens before building multiple views
```

**Key signals for token discovery:**
- `--` prefix in CSS files → CSS custom properties
- `theme` or `tokens` in filenames → centralized token definitions
- **Tailwind config** `extend` section → project-specific customizations
- `ThemeProvider` or `createTheme` → JS/TS theme system

### 1.2 Design Handoff Processing

**Purpose:** Translate design artifacts (Figma, screenshots, wireframes) into implementation specifications.

**Applies To:** Tasks where the user provides visual design references alongside implementation requests.

When a design artifact is provided:

```
1. ANALYZE the design for:
   - Layout structure (grid, flexbox, positioning)
   - Spacing rhythm (identify the spacing scale being used)
   - Typography (fonts, sizes, weights, line heights)
   - Color palette (primaries, secondaries, neutrals, semantic colors)
   - Component patterns (buttons, cards, forms, navigation)
   - Responsive behavior (if multiple breakpoints shown)

2. MAP to existing tokens:
   - Match design values to existing token definitions
   - Flag any design values that don't match existing tokens
   - Propose new token values if gaps are found

3. IDENTIFY components:
   - Map design elements to existing components
   - Flag elements requiring new components
   - Note component variants needed

4. PLAN implementation order:
   - Tokens/variables first (if new ones needed)
   - Base components second
   - Composed views third
   - Responsive adjustments fourth
```

### 1.3 Visual QA Procedure

**Purpose:** Verify implementation matches design intent and meets quality standards.

**Applies To:** After implementing any **visual interface changes** — component creation, layout modifications, style updates.

Post-implementation **visual quality checklist**:

```
□ Layout matches design reference (if provided)
□ Spacing uses token values (no hard-coded magic numbers)
□ Typography matches type scale
□ Colors reference semantic tokens
□ Component matches existing variants
□ Responsive behavior verified at 320px, 768px, 1024px
□ Dark mode appearance verified (if applicable)
□ Animation/transition feels natural (not janky)
```

---

## 2 Component Library Governance

**Importance: CRITICAL — Prevents design system drift across AI-generated code**

**Implements:** DS1 (Design Token Architecture), DS2 (Component Consistency), DS3 (Design System Discovery)

### 2.1 Token Management Procedures

**Purpose:** Establish and maintain **design token architecture** to prevent hard-coded value proliferation.

**Applies To:** Any project with more than one view or page. Single-page prototypes may use simplified tokens.

**Minimum viable token set** (establish before building multiple views):

```css
/* Spacing Scale (4px base recommended) */
--spacing-xs: 4px;
--spacing-sm: 8px;
--spacing-md: 16px;
--spacing-lg: 24px;
--spacing-xl: 32px;
--spacing-2xl: 48px;
--spacing-3xl: 64px;

/* Color Tokens — Semantic (reference primitives) */
--color-primary: var(--blue-600);
--color-primary-hover: var(--blue-700);
--color-error: var(--red-600);
--color-success: var(--green-600);
--color-warning: var(--amber-600);
--color-surface: var(--white);
--color-surface-secondary: var(--gray-50);
--color-text-primary: var(--gray-900);
--color-text-secondary: var(--gray-600);
--color-border: var(--gray-200);

/* Type Scale (Major Third 1.25 or Perfect Fourth 1.333) */
--font-size-xs: 0.75rem;   /* 12px */
--font-size-sm: 0.875rem;  /* 14px */
--font-size-base: 1rem;    /* 16px */
--font-size-lg: 1.25rem;   /* 20px */
--font-size-xl: 1.5rem;    /* 24px */
--font-size-2xl: 2rem;     /* 32px */
--font-size-3xl: 2.5rem;   /* 40px */

/* Border Radius */
--radius-sm: 4px;
--radius-md: 8px;
--radius-lg: 12px;
--radius-full: 9999px;

/* Shadows */
--shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.05);
--shadow-md: 0 4px 6px rgba(0, 0, 0, 0.1);
--shadow-lg: 0 10px 15px rgba(0, 0, 0, 0.1);
```

**Token naming convention:**
- Use semantic names for **application tokens** (what it means): `--color-primary`, `--spacing-md`
- Use descriptive names for **primitive tokens** (what it is): `--blue-600`, `--gray-200`
- Application tokens reference primitives: `--color-primary: var(--blue-600)`
- Components reference application tokens, never primitives directly

**Hard-coded value audit:**

When reviewing AI-generated code, check for:
```
VIOLATION: margin: 24px           → FIX: margin: var(--spacing-lg)
VIOLATION: color: #3b82f6         → FIX: color: var(--color-primary)
VIOLATION: font-size: 14px        → FIX: font-size: var(--font-size-sm)
VIOLATION: border-radius: 8px     → FIX: border-radius: var(--radius-md)
VIOLATION: padding: 20px          → FIX: Not on scale — use var(--spacing-md) or var(--spacing-lg)
```

### 2.2 Atomic Design Implementation

**Purpose:** Structure component hierarchy using **atomic design methodology** for consistent composition.

**Applies To:** Projects with component libraries or design systems. Less relevant for single-page applications.

**Component hierarchy:**

| Level | Name | Description | Examples |
|-------|------|-------------|----------|
| 1 | **Atoms** | Smallest functional units | Button, Input, Label, Icon, Badge |
| 2 | **Molecules** | Atoms composed into functional groups | Form Field (Label + Input + Error), Search Bar (Input + Button) |
| 3 | **Organisms** | Molecules composed into distinct sections | Navigation Bar, Card with Actions, Form Section |
| 4 | **Templates** | Page-level layouts with placeholder content | Dashboard Layout, Settings Page Layout |
| 5 | **Pages** | Templates with real data | User Dashboard, Account Settings |

**Rules for composition:**
- Atoms should be **fully self-contained** — no external dependencies, predictable API
- Molecules combine atoms — they should not import other molecules
- Organisms combine molecules and atoms — they define section-level structure
- Templates define layout slots — they should not contain business logic
- Pages fill templates with data — they handle data fetching and state

### 2.3 Component Naming Conventions

**Purpose:** Maintain **consistent component naming** to prevent discovery failures and duplication.

**Applies To:** Any project using component-based frameworks (React, Vue, Svelte, Angular, web components).

**Naming rules:**

| Convention | Format | Example |
|------------|--------|---------|
| Component files | PascalCase | `PrimaryButton.tsx`, `UserCard.vue` |
| Component exports | PascalCase | `export const PrimaryButton` |
| CSS classes (BEM) | kebab-case with BEM | `card__header`, `button--primary` |
| CSS custom properties | kebab-case | `--color-primary`, `--spacing-md` |
| Props/attributes | camelCase (JS) / kebab-case (HTML) | `onClick`, `is-disabled` |

**Variant naming:**
- Size variants: `sm`, `md`, `lg`, `xl` (not `small`, `medium`, `large`)
- Visual variants: `primary`, `secondary`, `ghost`, `destructive` (not `blue`, `gray`, `outlined`)
- State variants: `disabled`, `loading`, `error`, `active` (not `isDisabled`, `hasError`)

### 2.4 Design System Gap Reporting

**Purpose:** When the design system is incomplete, document gaps rather than silently introducing ad-hoc solutions.

**Applies To:** Situations where the **existing design system lacks** a needed token, component, or pattern.

When a gap is found:

```
1. DOCUMENT the gap:
   "No existing [token/component/pattern] found for [use case]"

2. PROPOSE a solution that fits the existing system:
   "Proposed: Add --spacing-2xs: 2px to the spacing scale"
   "Proposed: Create a StatusBadge component using existing color tokens"

3. USE the proposal consistently within the current task

4. FLAG for human review:
   "Design system gap: [description]. Using proposed solution [X] consistently.
    Please review and approve or adjust for the design system."
```

**Anti-pattern:** Silently generating a one-off solution without documenting the gap.

---

## 3 Design Review and Validation Gates

**Importance: CRITICAL — Catches AI-generated UX failures before they reach users**

**Implements:** All principles (validation criteria), ACC1-ACC3, RD1-RD2, PL1-PL2, IX7

### 3.1 Pre-Commit UI Review Checklist

**Purpose:** **Structured validation gate** for all UI-affecting changes before they are committed.

**Applies To:** Any commit that modifies user-facing interface code (components, pages, styles, layouts).

**Tier 1 — Always check (every UI commit):**

| Check | Validates | Quick Method |
|-------|-----------|-------------|
| **Semantic HTML** | ACC1 | No `<div onclick>` without role + keyboard handler |
| **Labels present** | ACC1 | Every `<input>` has associated `<label>` |
| **Alt text** | ACC1 | Every `<img>` has meaningful `alt` (or `alt=""` for decorative) |
| **Token usage** | DS1 | No hard-coded color hex, spacing px, or font size values |
| **Component reuse** | DS2 | No re-implementation of existing components |
| **Error states** | IX4 | Forms have validation and error display |

**Tier 2 — Check for new pages/components:**

| Check | Validates | Quick Method |
|-------|-----------|-------------|
| **Keyboard navigation** | ACC2 | Tab through all interactive elements |
| **Focus indicators** | ACC2 | No `outline: none` without replacement |
| **Color contrast** | ACC3 | Run contrast checker on text elements |
| **Responsive** | RD1 | Check at 320px and 1024px minimum |
| **Touch targets** | RD2 | Interactive elements ≥44x44px |
| **Loading states** | IX2 | Data-dependent views show skeleton/spinner |

**Tier 3 — Check for platform-specific work:**

| Check | Validates | Quick Method |
|-------|-----------|-------------|
| **Platform conventions** | PL1 | Navigation, icons, gestures match target platform |
| **Cross-platform consistency** | PL2 | Shared design language with adapted chrome |

### 3.2 Accessibility Spot-Check Procedure

**Purpose:** Quick **accessibility verification** that can be performed during development without specialized tools.

**Applies To:** All interface work. Supplements but does not replace full accessibility auditing (§4).

**30-second keyboard test:**

```
1. Click the first element in the page
2. Press Tab repeatedly through the page:
   □ Can you reach every interactive element?
   □ Is the focus indicator always visible?
   □ Does tab order match visual reading order?
3. Press Enter/Space on focused buttons:
   □ Do they activate?
4. Press Escape on modals/dropdowns:
   □ Do they close?
   □ Does focus return to the trigger?
```

**30-second screen reader test (VoiceOver/NVDA):**

```
1. Enable screen reader
2. Navigate the page:
   □ Are headings announced in order?
   □ Are images described meaningfully?
   □ Are form fields labeled?
   □ Are button/link purposes clear?
3. Complete a primary task:
   □ Can you accomplish the main task using screen reader alone?
```

### 3.3 Responsive Validation Matrix

**Purpose:** **Systematic responsive testing** across the standard breakpoint spectrum.

**Applies To:** Any page or component that must work across viewport sizes.

| Viewport | Width | Check |
|----------|-------|-------|
| **Small mobile** | 320px | Layout doesn't overflow, text readable, touch targets ≥44px |
| **Standard mobile** | 375px | Primary workflow completable, navigation accessible |
| **Tablet portrait** | 768px | Layout adapts (stacking or side-by-side), no awkward wrapping |
| **Tablet landscape** | 1024px | Full layout features available, navigation appropriate |
| **Desktop** | 1280px | Content contained (not stretching to full width), readable line lengths |
| **Wide desktop** | 1440px+ | Content area has max-width, sidebars proportional |

**Testing method:**
- Browser DevTools device emulation for quick checks
- Actual device testing for touch interactions and performance
- Both landscape and portrait orientations for tablet

### 3.4 Component Consistency Audit

**Purpose:** Detect and remediate **visual inconsistencies** across AI-generated components.

**Applies To:** After generating or modifying multiple related components within a single task.

**Audit procedure:**

```
1. INVENTORY all components modified in this task

2. COMPARE each component against its peers:
   □ Same-function buttons use identical styling?
   □ Cards use consistent padding, radius, shadow?
   □ Form inputs have consistent height, border, focus state?
   □ Spacing between elements follows the token scale?

3. COMPARE against existing components in the project:
   □ New components match the visual language of existing ones?
   □ No new token values introduced unnecessarily?
   □ Component API (props/events) follows existing patterns?

4. FIX inconsistencies before committing:
   □ Extract shared styles into tokens or shared components
   □ Align variant naming with existing conventions
   □ Document any intentional deviations
```

### 3.5 Dark Pattern Screening

**Purpose:** Detect **deceptive design patterns** in AI-generated interfaces before deployment.

**Applies To:** All interactive elements, forms, checkout flows, subscription management, cookie/consent banners, and any flow involving user commitment (purchase, sign-up, data sharing).

**FTC dark pattern category checklist:**

```
□ NAGGING: No repeated prompts that pressure users into actions
  - Dismiss/decline is as easy as accept
  - Dismissed prompts do not reappear in the same session
  - No countdown timers creating false urgency

□ OBSTRUCTION: No unnecessary friction for user-protective actions
  - Cancellation ≤2 clicks from account settings
  - Unsubscribe link in every marketing email
  - No phone-only or chat-only cancellation requirements
  - Account deletion accessible without contacting support

□ SNEAKING: No hidden costs, forced additions, or stealth changes
  - All costs visible before payment information entry
  - No pre-checked add-ons in cart
  - No auto-enrollment in recurring billing without explicit consent
  - Terms changes communicated proactively

□ INTERFACE INTERFERENCE: No visual manipulation that steers decisions
  - Accept and decline options have equal visual weight
  - Confirmshaming detection: decline text is neutral, not guilt-inducing
  - Primary/secondary button styling not used to misdirect
  - No "trick questions" with double negatives

□ FORCED ACTION: No coerced behavior beyond what is necessary
  - Account creation not required for guest checkout (if applicable)
  - No forced social sharing to access content
  - No required app downloads for basic functionality
  - Marketing consent decoupled from service terms
```

**AI-specific screening signals:**
- AI defaults to conversion-optimized patterns from training data — always verify opt-in defaults
- AI generates asymmetric CTA styling (bright "Accept" vs. muted "Decline") — normalize visual weight
- AI pre-selects checkboxes because training examples often have them checked — verify default states
- AI generates **confirmshaming detection** copy because growth-hacked patterns dominate training data

**Automated detection patterns:**
```
# Pre-checked optional checkboxes
grep -rn 'checked\|defaultChecked\|:checked' src/ | grep -vi 'required\|terms-of-service'

# Asymmetric button styling in consent/opt-in contexts
# Manual review: compare accept vs. decline button styling

# Forced continuity without cancellation
# Review: subscription flows have visible cancellation path
```

**Misdirection screening** procedure:
1. For every accept/decline pair, compare visual weight (size, color, contrast, positioning)
2. For every pre-checked checkbox, verify it's genuinely required (not optional marketing consent)
3. For every multi-step flow, verify exit path at every step
4. For every **forced continuity audit** target (subscriptions, trials), verify cancellation is ≤2 clicks

---

### 3.6 Core Web Vitals Validation

**Purpose:** Measurable **performance perception thresholds** for web applications.

**Applies To:** Web applications, progressive web apps, and any browser-based interface. Not applicable to native mobile apps (use platform-specific performance metrics instead).

**Core Web Vitals thresholds (Google, 2024):**

| Metric | Good | Needs Improvement | Poor | What It Measures |
|--------|------|-------------------|------|-----------------|
| **Largest Contentful Paint** (LCP) | <2.5s | 2.5-4.0s | >4.0s | Loading speed — when main content is visible |
| **Interaction to Next Paint** (INP) | <200ms | 200-500ms | >500ms | Responsiveness — delay between user action and visual response |
| **Cumulative Layout Shift** (CLS) | <0.1 | 0.1-0.25 | >0.25 | Visual stability — how much the layout shifts during loading |

**AI-specific causes of poor Core Web Vitals:**

| Violation | CWV Impact | AI Cause | Fix |
|-----------|-----------|----------|-----|
| Images without `width`/`height` | CLS | AI generates `<img src="...">` without dimensions | Add explicit `width` and `height` attributes |
| Dynamically injected content | CLS | AI generates JavaScript that inserts DOM elements after load | Reserve space with `min-height` or skeleton placeholders |
| Web font flash (FOIT/FOUT) | CLS, LCP | AI imports custom fonts without `font-display` | Add `font-display: swap` or `optional` |
| Unoptimized hero images | LCP | AI uses full-size images without responsive sizing | Use `<picture>`, `srcset`, and appropriate compression |
| Third-party script blocking | LCP, INP | AI adds analytics/tracking scripts synchronously | Use `async` or `defer` attributes |
| Expensive event handlers | INP | AI generates unthrottled scroll/resize/input handlers | Throttle/debounce handlers, use `passive` event listeners |
| **Layout shift prevention** requires explicit dimensions | CLS | AI omits `aspect-ratio` or dimensions on dynamic content | Add `aspect-ratio` CSS or explicit dimensions |

**Validation procedure:**

```
1. MEASURE with Lighthouse or PageSpeed Insights:
   □ LCP < 2.5s (Largest Contentful Paint threshold)
   □ INP < 200ms (Interaction to Next Paint)
   □ CLS < 0.1 (layout shift prevention)

2. CHECK AI-generated code for:
   □ All <img> tags have width and height attributes
   □ Web fonts use font-display: swap or optional
   □ Dynamic content containers have min-height or aspect-ratio
   □ Third-party scripts use async/defer
   □ Event handlers are throttled/debounced where appropriate

3. TEST at realistic conditions:
   □ Throttled CPU (4x slowdown in DevTools)
   □ Throttled network (Fast 3G in DevTools)
   □ Both mobile and desktop viewports
```

---

## 4 Accessibility Testing and Auditing

**Importance: CRITICAL — Accessibility failures have legal and ethical consequences**

**Implements:** ACC1 (Semantic Markup), ACC2 (Keyboard Navigation), ACC3 (Color and Contrast)

### 4.1 WCAG 2.2 Level AA Compliance Checklist

**Purpose:** Systematic **WCAG compliance verification** for AI-generated interfaces.

**Applies To:** All user-facing interfaces. Priority: public-facing first, then internal tools.

**Perceivable (WCAG 1.x):**

- [ ] **1.1.1 Non-text Content:** All images have **descriptive alt text** (or `alt=""` for decorative)
- [ ] **1.3.1 Info and Relationships:** Heading hierarchy is correct (`h1` → `h2` → `h3`, no skips). Form inputs have associated labels. Tables have headers.
- [ ] **1.3.2 Meaningful Sequence:** DOM order matches visual order. Screen reader reads content in logical sequence.
- [ ] **1.4.1 Use of Color:** Information not conveyed by **color alone** — icons, text, or patterns accompany color coding
- [ ] **1.4.3 Contrast (Minimum):** Normal text ≥4.5:1 contrast ratio. Large text (≥18pt/14pt bold) ≥3:1.
- [ ] **1.4.4 Resize Text:** Text resizable to 200% without loss of content or functionality
- [ ] **1.4.11 Non-text Contrast:** UI components and graphical objects ≥3:1 contrast against adjacent colors

**Operable (WCAG 2.x):**

- [ ] **2.1.1 Keyboard:** All functionality **operable via keyboard** alone
- [ ] **2.1.2 No Keyboard Trap:** Focus can be moved away from any element using standard keys
- [ ] **2.4.1 Bypass Blocks:** **Skip navigation** link present for repeated content
- [ ] **2.4.3 Focus Order:** Tab order is **logical and predictable**, matches visual layout
- [ ] **2.4.6 Headings and Labels:** Headings and labels are **descriptive** (not "Section 1", "Input")
- [ ] **2.4.7 Focus Visible:** **Focus indicator** is visible on all interactive elements
- [ ] **2.4.11 Focus Not Obscured:** Focused element is not hidden behind sticky headers/footers

**Understandable (WCAG 3.x):**

- [ ] **3.1.1 Language of Page:** `lang` attribute present on `<html>` element
- [ ] **3.2.1 On Focus:** No unexpected **context change** when element receives focus
- [ ] **3.3.1 Error Identification:** Errors are identified and described in text (not color alone)
- [ ] **3.3.2 Labels or Instructions:** Form fields have visible labels and instructions where needed

**Robust (WCAG 4.x):**

- [ ] **4.1.2 Name, Role, Value:** Custom controls have accessible **name, role, and value** via ARIA
- [ ] **4.1.3 Status Messages:** Status messages are communicated to assistive technology via `role="status"` or `aria-live`

### 4.2 Screen Reader Testing Procedure

**Purpose:** Verify interface **usability with assistive technology** beyond automated checking.

**Applies To:** New pages, major component changes, and any **accessibility remediation** work.

**Test with at least one screen reader:**

| Platform | Screen Reader | Browser |
|----------|---------------|---------|
| macOS | VoiceOver (built-in) | Safari |
| Windows | NVDA (free) | Chrome or Firefox |
| iOS | VoiceOver (built-in) | Safari |
| Android | TalkBack (built-in) | Chrome |

**Testing script:**

```
1. NAVIGATE to the page

2. LANDMARKS test:
   □ Screen reader announces page landmarks (main, nav, header, footer)
   □ Landmark-based navigation works (VoiceOver: rotor → landmarks)

3. HEADINGS test:
   □ Heading navigation lists all headings in correct order
   □ Headings are descriptive and hierarchical

4. FORMS test:
   □ Each form field announces its label when focused
   □ Required fields are announced as required
   □ Error messages are announced when they appear
   □ Form can be completed and submitted via screen reader alone

5. INTERACTIVE ELEMENTS test:
   □ Buttons announce their purpose
   □ Links announce their destination
   □ Custom controls announce role, state, and value
   □ State changes are announced (expanded/collapsed, checked/unchecked)

6. DYNAMIC CONTENT test:
   □ Content updates are announced (live regions)
   □ Modal focus management works
   □ Page navigation announces new content
```

### 4.3 Automated Accessibility Scanning

**Purpose:** Supplement manual testing with **automated accessibility tools** for broad coverage.

**Applies To:** All interface projects. Run during development and as part of CI/CD.

**Recommended tools:**

| Tool | Type | What It Catches |
|------|------|-----------------|
| **axe-core** | Library/CLI | WCAG violations, ARIA errors, contrast issues |
| **Lighthouse Accessibility** | Browser DevTools | Accessibility score with specific issues |
| **eslint-plugin-jsx-a11y** | Linter plugin | JSX accessibility anti-patterns during development |
| **Pa11y** | CLI/CI tool | WCAG compliance errors for CI integration |

**Integration approach:**
- **Development time:** `eslint-plugin-jsx-a11y` catches issues as code is written
- **Pre-commit:** axe-core in component tests catches issues before merge
- **CI pipeline:** Pa11y or Lighthouse CI catches issues in deployed previews
- **Manual review:** Screen reader testing catches issues automated tools miss

**Critical limitation:** Automated tools catch ~30-40% of accessibility issues. They find contrast failures, missing alt text, and ARIA errors — but cannot evaluate whether alt text is *meaningful*, whether focus order is *logical*, or whether the interface is *usable* with assistive technology. Manual testing (§4.2) is required for full coverage.

### 4.4 Color Contrast Verification

**Purpose:** Systematic **contrast ratio verification** for all text and UI elements.

**Applies To:** All text elements, UI component boundaries, focus indicators, and **icons conveying information**.

**Verification procedure:**

```
1. IDENTIFY all text elements:
   - Body text, headings, labels, placeholders, error messages
   - Text on buttons, badges, tags, tooltips
   - Text in input fields (both value and placeholder)

2. CHECK contrast ratios:
   - Normal text (<18pt or <14pt bold): ≥4.5:1
   - Large text (≥18pt or ≥14pt bold): ≥3:1
   - UI components (borders, icons): ≥3:1
   - Focus indicators: ≥3:1 against both element and page background

3. CHECK both color modes:
   □ Light mode contrast passes
   □ Dark mode contrast passes (if applicable)
   □ High contrast mode works (if applicable)

4. VERIFY non-color indicators:
   □ Error states have icon + text (not just red)
   □ Success states have icon + text (not just green)
   □ Links are distinguishable without color (underline, weight, or position)
```

**Tools for contrast checking:**
- Chrome DevTools: Inspect element → computed styles shows contrast ratio
- **Colour Contrast Analyser** (desktop app) — point-and-click checking
- **WebAIM Contrast Checker** — web-based ratio calculator

---

## 5 Responsive Breakpoint Strategy

**Importance: IMPORTANT — Prevents desktop-only generation**

**Implements:** RD1 (Responsive Layout Strategy), RD2 (Touch Target Adaptation)

### 5.1 Breakpoint Definition and Rationale

**Purpose:** Establish **consistent breakpoint strategy** across the project.

**Applies To:** All responsive interface work. Non-responsive applications (fixed kiosk, desktop-only) should document the exception.

**Recommended breakpoints** (content-driven, not device-driven):

| Token | Width | Common Devices | Layout Adaptation |
|-------|-------|----------------|-------------------|
| `--bp-sm` | 480px | Large phones (landscape) | Stack → limited side-by-side |
| `--bp-md` | 768px | Tablets (portrait) | Side-by-side layouts, sidebar appears |
| `--bp-lg` | 1024px | Tablets (landscape), small laptops | Full desktop layout |
| `--bp-xl` | 1280px | Standard desktops | Max-width content containers |
| `--bp-2xl` | 1536px | Wide desktops | Optional: wider content area |

**Critical principle:** Breakpoints are based on **content** behavior, not device specifications. Add custom breakpoints where the layout naturally breaks, not at arbitrary device widths.

**Mobile-first CSS ordering:**

```css
/* Base styles = mobile (smallest viewport) */
.component { /* mobile layout */ }

/* Progressively enhance for larger viewports */
@media (min-width: 480px) { .component { /* phone landscape */ } }
@media (min-width: 768px) { .component { /* tablet */ } }
@media (min-width: 1024px) { .component { /* desktop */ } }
```

### 5.2 Content Adaptation Patterns

**Purpose:** Define **how content adapts** across breakpoints for common UI patterns.

**Applies To:** Any component or layout that appears across multiple viewport sizes.

| Pattern | Mobile (<768px) | Tablet (768-1023px) | Desktop (≥1024px) |
|---------|-----------------|---------------------|-------------------|
| **Navigation** | Bottom tab (≤5) or hamburger | Sidebar or top nav | Sidebar or horizontal nav |
| **Card grid** | 1 column, full width | 2 columns | 3-4 columns |
| **Data table** | Card view or horizontal scroll | Condensed table | Full table |
| **Sidebar + content** | Sidebar hidden, toggle to show | Sidebar collapsible | Sidebar always visible |
| **Form** | Single column, full width fields | Single column, constrained width | Single column or 2-col for short fields |
| **Hero section** | Stacked (text above image) | Side-by-side | Side-by-side with larger image |
| **Dashboard** | Single column, stacked widgets | 2-column grid | Multi-column with sidebar |

**Content priority on mobile:**
- Primary action/CTA must be visible without scrolling
- Secondary navigation can be hidden behind a menu
- Supplementary content (sidebars, related items) moves below main content
- Images should be responsive but not dominate mobile viewport

### 5.3 Touch Target Compliance Matrix

**Purpose:** Ensure **interactive elements meet minimum size requirements** across platforms.

**Applies To:** All interactive elements on **touch-capable devices** (mobile, tablet, touchscreen desktop).

| Element Type | Minimum Size | Minimum Gap | Notes |
|--------------|-------------|-------------|-------|
| Buttons | 44x44px (Apple) / 48x48dp (Material) | 8px | Visual size can be smaller if tap area extends |
| Links in text | 44px height tap area | N/A | Use padding to extend tap area |
| Form inputs | 44px height | 8px | Standard mobile input height |
| Checkboxes/radios | 44x44px tap area | 8px | Label should extend tap area |
| Icon buttons | 44x44px tap area | 8px | Padding around icon |
| List items (tappable) | 44px minimum height | 0 (borders serve as separators) | Full-width tap area |
| Toggle switches | 44px minimum height | 8px | Include label in tap area |

**Implementation technique — extending tap areas:**

```css
/* Make a small icon button meet touch target minimums */
.icon-button {
  /* Visual size */
  width: 24px;
  height: 24px;
  /* Extend tap area with padding */
  padding: 10px;  /* 24 + 10 + 10 = 44px total */
  /* Or use min-width/min-height */
  min-width: 44px;
  min-height: 44px;
}
```

---

## 6 Cross-Platform Adaptation

**Importance: IMPORTANT — Prevents platform convention violations**

**Implements:** PL1 (Platform Convention Compliance), PL2 (Cross-Platform Adaptation)

### 6.1 Platform Convention Reference

**Purpose:** Quick-reference guide for **platform-specific conventions** to prevent UX-F3 violations.

**Applies To:** Any interface targeting a specific platform (iOS, Android, web) or multiple platforms.

| Element | iOS (Apple HIG) | Android (Material 3) | Web |
|---------|-----------------|----------------------|-----|
| **Primary nav** | Bottom tab bar (≤5 items) | Bottom navigation bar / Nav rail | Top nav bar or sidebar |
| **Back navigation** | System back swipe, nav bar back button | System back button/gesture | Browser back button, breadcrumbs |
| **Primary action** | Top-right nav bar button | Floating Action Button (FAB) | Inline button or CTA |
| **Icons** | SF Symbols | Material Symbols | SVG / icon library |
| **Typography** | SF Pro (system font) | Roboto / system font | System font stack |
| **Touch targets** | 44x44pt minimum | 48x48dp minimum | 44x44px recommended |
| **Modals** | Sheet (slides up) | Bottom sheet or dialog | Centered dialog |
| **Selection** | Checkmarks in lists | Checkboxes | Checkboxes |
| **Destructive actions** | Red text, swipe-to-delete | Snackbar with undo | Confirmation dialog |
| **Dark mode** | System preference respected | System preference respected | `prefers-color-scheme` media query |
| **Search** | Search bar in nav | Search in top app bar | Search input or search page |

### 6.2 Cross-Platform Decision Matrix

**Purpose:** Guide **what to share vs. adapt** in cross-platform applications.

**Applies To:** Applications targeting multiple platforms (React Native, Flutter, responsive web, Electron).

| Element | Share Across Platforms | Adapt Per Platform |
|---------|------------------------|--------------------|
| **Color palette** | Yes — brand colors consistent | Adjust for dark mode per platform |
| **Typography scale** | Yes — relative sizes consistent | Font family may differ (SF Pro vs Roboto) |
| **Spacing scale** | Yes — spacing tokens consistent | Absolute values may adjust (pt vs dp vs px) |
| **Iconography meaning** | Yes — same metaphors | Icon set differs (SF Symbols vs Material) |
| **Component behavior** | Yes — same interaction model | Gesture/animation differs |
| **Navigation structure** | No — destinations same, chrome differs | Tab bar (iOS) vs nav rail (Android) vs sidebar (web) |
| **System integration** | No — platform-specific APIs | Pickers, share sheets, permissions |
| **Gestures** | No — follow platform conventions | Swipe behaviors differ by platform |

### 6.3 Platform Testing Checklist

**Purpose:** Verify **platform-appropriate behavior** on each target platform.

**Applies To:** Cross-platform applications before release on each platform.

**Per-platform checks:**

```
iOS:
□ Tab bar used for primary navigation (not hamburger menu)
□ SF Symbols used for icons
□ Swipe-to-go-back works from left edge
□ VoiceOver can navigate the entire interface
□ Dynamic Type (text size accessibility) supported
□ Safe area insets respected (notch, home indicator)

Android:
□ Material Design navigation patterns used
□ System back button/gesture works correctly
□ TalkBack can navigate the entire interface
□ Edge-to-edge display supported (gesture navigation)
□ Material motion used for transitions

Web:
□ Browser back button works correctly (history not broken)
□ Standard keyboard shortcuts work (Ctrl+S, Escape, etc.)
□ Tab navigation reaches all interactive elements
□ No horizontal scroll at 320px viewport
□ Links are distinguishable from text
□ Right-click context menu not hijacked
```

### 6.4 Platform Convention Currency Verification

**Purpose:** Verify AI-generated platform patterns match **current** (not outdated) platform conventions.

**Applies To:** iOS, Android, and web platform code where AI applies platform-specific design patterns.

AI models have a **training data temporal lag** — patterns learned during training may reflect platform conventions that have since been updated. For example, iOS 26 introduced the Liquid Glass design language (2025), fundamentally changing visual treatment of navigation bars, tab bars, and sidebars. AI trained on pre-Liquid-Glass data will generate deprecated flat/translucent bar styles.

**Convention currency verification** checklist:

```
iOS:
□ Navigation bars match current HIG (Liquid Glass for iOS 26+, or appropriate version)
□ Tab bar styling matches current platform visual language
□ System controls use current API (UIKit/SwiftUI current release)
□ Safe area handling matches current device lineup
□ No deprecated interaction patterns (e.g., 3D Touch replaced by Haptic Touch)

Android:
□ Material Design version matches target (Material 3 / Material You)
□ Navigation components use current patterns (nav rail vs. bottom bar)
□ Dynamic color (Material You) supported if targeting Android 12+
□ Predictive back gesture support for Android 14+

Web:
□ HTML elements use current semantics (e.g., <dialog> instead of custom modals)
□ CSS features match browser support targets (container queries, :has(), etc.)
□ No polyfills for widely-supported features
□ Deprecated APIs flagged (e.g., document.write, synchronous XHR)
```

**Platform guideline version check** procedure:
1. Identify the target platform version(s) for the application
2. Check the current platform design guideline version (HIG, Material Design, web specs)
3. Compare AI-generated patterns against current guidelines, not cached training knowledge
4. Flag any patterns that appear to come from outdated guideline versions
5. When uncertain, consult the canonical source: Apple HIG (developer.apple.com/design), Material Design (m3.material.io), MDN Web Docs (developer.mozilla.org)

**Training data temporal lag** indicators:
- AI generates flat navigation bars when the current iOS uses Liquid Glass
- AI uses Material Design 2 components when Material 3 is current
- AI generates jQuery patterns when modern vanilla JS or framework equivalents exist
- AI uses `-webkit-` prefixes for properties that no longer require them

---

## 7 Design System Documentation

**Importance: OPTIONAL — Enhances design system discoverability and maintenance**

**Implements:** DS1 (Design Token Architecture), DS3 (Design System Discovery)

### 7.1 Token Documentation Format

**Purpose:** Document design tokens for **human and AI discoverability**.

**Applies To:** Projects with established design token systems that need documentation.

**Recommended documentation structure:**

```markdown
# Design System Tokens

## Spacing
| Token | Value | Usage |
|-------|-------|-------|
| --spacing-xs | 4px | Inline element gaps, icon-to-text spacing |
| --spacing-sm | 8px | Compact element padding, list item gaps |
| --spacing-md | 16px | Standard component padding, form field gaps |
| --spacing-lg | 24px | Section spacing, card padding |
| --spacing-xl | 32px | Major section separation |

## Colors
| Token | Light Value | Dark Value | Usage |
|-------|-------------|------------|-------|
| --color-primary | #2563eb | #60a5fa | Primary actions, active states |
| --color-error | #dc2626 | #f87171 | Error states, destructive actions |
...

## Typography
| Token | Value | Usage |
|-------|-------|-------|
| --font-size-base | 1rem (16px) | Body text |
| --font-size-lg | 1.25rem (20px) | Subheadings, emphasis |
...
```

**Key rule:** Documentation should be in a format the AI agent can **query and discover** via `query_project()`. Markdown in the codebase is preferable to external tools.

### 7.2 Component Catalog Format

**Purpose:** Document **component variants and usage** for consistent application.

**Applies To:** Shared component libraries with multiple variants.

**Per-component documentation:**

```markdown
## Button

### Variants
| Variant | Usage | Visual |
|---------|-------|--------|
| primary | Main actions, form submission | Filled, brand color |
| secondary | Supporting actions | Outlined, neutral |
| ghost | Tertiary actions, inline actions | Text-only, no border |
| destructive | Delete, remove, destructive actions | Filled, red |

### Sizes
| Size | Height | Font Size | Padding |
|------|--------|-----------|---------|
| sm | 32px | 14px | 8px 12px |
| md | 40px | 16px | 10px 16px |
| lg | 48px | 18px | 12px 24px |

### States
- Default, Hover, Active, Focus, Disabled, Loading

### Usage Rules
- One primary button per view
- Destructive buttons require confirmation
- Loading state replaces text with spinner
```

### 7.3 Pattern Library Maintenance

**Purpose:** Keep design system documentation **current** as the system evolves.

**Applies To:** Active design systems that change over time.

**Maintenance triggers:**
- New token added → update token documentation
- New component created → add to component catalog
- Component variant added → update variant table
- **Breaking change** → version bump, migration guide

**Staleness indicators:**
- Token in code but not in documentation
- Component in code but not in catalog
- Documentation references deprecated token names
- **AI-generated code** uses undocumented tokens or components (indicates discovery gap)

---

## 8 AI Tooling Integration

**Importance: OPTIONAL — Enhances design-to-code quality with specialized AI tools**

**Implements:** DS3 (Design System Discovery), VH1 (Layout Composition)

### 8.1 Figma MCP Integration

**Purpose:** Use **Figma MCP connectors** to provide design context directly to the AI agent.

**Applies To:** Projects using Figma for design, where a Figma MCP server is available.

**Integration workflow:**

```
1. CONNECT Figma MCP server to the AI development environment
2. REFERENCE specific Figma frames/components when requesting UI implementation
3. AI agent READS Figma data:
   - Layout structure and constraints
   - Design token values (from Figma variables)
   - Component properties and variants
   - Auto-layout settings (maps to CSS flexbox/grid)
4. AI agent GENERATES code that matches the Figma design:
   - Token values from Figma variables, not hard-coded
   - Layout using auto-layout equivalents (flexbox/grid)
   - Responsive behavior from Figma constraints
```

**Current limitation:** Figma MCP fidelity varies by server implementation. Always verify generated code against the design visually. The Figma data provides structure and values, but the AI agent must still apply VH, DS, and ACC principles.

**Token cost warning:** Figma MCP `get_design_context` on large designs can produce 600K+ tokens — far exceeding typical context windows. Limit selection scope to specific frames/components rather than entire pages. Prefer `get_variable_defs` (tokens only) when full layout context isn't needed.

**Ecosystem note (2026-03):** Production-grade MCP servers now exist for the full design-to-code-to-test pipeline: Figma Official MCP (read+write), Storybook MCP (component manifests), Deque Axe MCP (accessibility auditing), Microsoft Playwright MCP (browser automation/screenshots), Percy via BrowserStack MCP (visual regression). Tool-specific integration guides will be added to this section as tools are adopted — per the tool-specific content pattern, capture what we actively use rather than cataloging every option.

### 8.2 Design Token Extraction

**Purpose:** Extract design tokens from **existing design tools** into code-usable formats.

**Applies To:** Projects migrating from design-tool-only token definitions to code-based tokens.

**Extraction sources:**

| Source | Format | Extraction Method |
|--------|--------|-------------------|
| Figma Variables | Figma API | Figma MCP or plugin export |
| Figma Styles | Figma API | Style export plugin |
| Sketch Libraries | Sketch JSON | Parser script |
| Adobe XD | XD API | Plugin export |
| Manual definition | Spreadsheet/doc | Manual translation |

**Output formats:**

| Format | Framework | Example |
|--------|-----------|---------|
| CSS Custom Properties | Any web | `--color-primary: #2563eb;` |
| Tailwind Config | Tailwind CSS | `colors: { primary: '#2563eb' }` |
| JSON Tokens | W3C Design Tokens | `{ "color": { "primary": { "$value": "#2563eb" } } }` |
| JS/TS Object | styled-components, MUI | `export const colors = { primary: '#2563eb' }` |
| SCSS Variables | SCSS/Sass | `$color-primary: #2563eb;` |

### 8.3 Screenshot-Based Visual QA

**Purpose:** Use **screenshot comparison** to verify AI-generated UI matches design intent.

**Applies To:** Projects with visual design references where automated visual comparison is desired.

**Workflow:**

```
1. CAPTURE screenshots of implemented interface at key breakpoints
2. COMPARE against design references:
   - Layout structure matches?
   - Spacing proportions correct?
   - Typography matches?
   - Color matches?
3. IDENTIFY deviations:
   - Intentional (responsive adaptation, platform adjustment)
   - Unintentional (token mismatch, component error)
4. FIX unintentional deviations
```

**Tools for visual comparison:**
- **Percy** (CI-integrated visual testing)
- **Chromatic** (Storybook visual regression)
- **BackstopJS** (open-source visual regression)
- Manual comparison (screenshot side-by-side with design)

### 8.4 AI Code Generation Guardrails

**Purpose:** Prevent common AI-generated **UI code anti-patterns** through review guidance.

**Applies To:** All AI-generated interface code. Use as a **post-generation checklist**.

**Common AI UI code anti-patterns to check:**

| Anti-Pattern | Detection | Fix |
|--------------|-----------|-----|
| `<div onclick>` | Search for `div.*onclick\|div.*onClick` | Replace with `<button>` |
| Hard-coded colors | Search for `#[0-9a-f]{3,6}\|rgb\(` in component files | Replace with token references |
| Hard-coded spacing | Search for `margin:.*px\|padding:.*px` not referencing tokens | Replace with token references |
| `outline: none` without replacement | Search for `outline:\s*none\|outline:\s*0` | Add `:focus-visible` styles |
| Placeholder-only labels | Search for `placeholder=` without adjacent `<label>` | Add visible `<label>` element |
| Missing `alt` on images | Search for `<img` without `alt=` | Add descriptive `alt` attribute |
| Fixed widths on responsive elements | Search for `width:\s*\d+px` on containers | Use `max-width`, `%`, or `fr` |
| Missing loading states | Check async data components for loading handling | Add skeleton/spinner states |
| Missing error states | Check form/data components for error handling | Add error display and recovery |
| **Icon-only buttons without labels** | Search for icon components inside buttons without text/aria-label | Add `aria-label` or visible text |

**Regex patterns for automated detection:**

```bash
# Hard-coded colors in component files
grep -rn '#[0-9a-fA-F]\{3,6\}' src/components/

# Div with click handlers
grep -rn 'div.*onClick\|div.*onclick' src/

# Outline removal without replacement
grep -rn 'outline:\s*none\|outline:\s*0' src/

# Images without alt
grep -rn '<img[^>]*>' src/ | grep -v 'alt='
```

---

## 9 UX Content and Microcopy Governance

**Importance: IMPORTANT — AI-generated microcopy is often generic, inconsistent, or tonally inappropriate**

**Implements:** IX4 (Error Handling), IX7 (Ethical Interaction Design), VH2 (Typography and Readability)

### 9.1 Voice and Tone Consistency

**Purpose:** Maintain consistent **voice consistency rules** across all interface text generated by AI.

**Applies To:** All user-facing text in interfaces — button labels, navigation items, headings, descriptions, tooltips, empty states, onboarding text.

AI generates microcopy that varies in tone across a single interface — formal error messages alongside casual empty states, technical jargon in user-facing labels, and inconsistent capitalization patterns. Each AI generation draws from different training examples, producing **tone calibration** drift within a single application.

**Voice definition framework:**

```
1. DEFINE the product voice (collaborate with stakeholders):
   - Personality traits: [e.g., Friendly but professional, Confident but not arrogant]
   - Vocabulary level: [e.g., Plain language, no jargon, 8th-grade reading level]
   - Sentence style: [e.g., Short, active voice, direct]
   - Humor tolerance: [e.g., Light humor in empty states, none in errors]

2. ESTABLISH tone variations by context:
   | Context | Tone | Example |
   |---------|------|---------|
   | Success | Encouraging | "Your changes are saved." |
   | Error | Helpful, not alarming | "We couldn't save your changes. Try again?" |
   | Empty state | Guiding | "No projects yet. Create your first one." |
   | Destructive action | Clear, serious | "This will permanently delete your account." |
   | Onboarding | Welcoming | "Welcome! Let's get you set up." |

3. APPLY consistently:
   - AI-generated text must match the defined voice
   - Flag tone mismatches during review
```

**Brand voice alignment** check:
- If a brand voice guide exists, `query_project("brand voice guide tone style")` before writing any microcopy
- If no guide exists, establish basic voice parameters before generating multiple views with text
- Cross-reference: Storytelling domain voice/tone principles may overlap for applications with narrative elements

### 9.2 Error Message Patterns

**Purpose:** Standardize **error message framework** across the application for consistent, helpful error communication.

**Applies To:** All error messages — form validation, API errors, permission errors, 404/500 pages, empty states that result from errors.

AI generates error messages that range from developer-oriented ("Error 422: Unprocessable Entity") to vague ("Something went wrong") to passive-aggressive ("Invalid input"). The **actionable error copy** pattern ensures every error message answers three questions: What happened? Why? What can the user do?

**Error message framework:**

| Component | Required | Example |
|-----------|----------|---------|
| **What happened** | Yes | "Your password is too short." |
| **Why** | If non-obvious | "Passwords must be at least 8 characters." |
| **What to do** | Yes | "Add more characters and try again." |

**Error tone matching** rules:
- Use the same tone as the rest of the application (don't suddenly become formal in errors)
- Never blame the user ("You entered an invalid email" → "Please enter a valid email address")
- Never use error codes as the primary message (show codes in details/console, not UI)
- Never use ALL CAPS for emphasis in error messages
- Be specific: "Email address must include @" not "Invalid email"

**Standard error templates:**

```
Form validation: "[Field name] [what's wrong]. [How to fix it]."
  → "Email address must include an @ symbol. Example: name@company.com"

Permission: "You don't have access to [resource]. [How to get access]."
  → "You don't have access to this project. Ask the project owner to invite you."

Network: "[What failed]. [Recovery action]."
  → "Couldn't load your messages. Check your connection and try again."

Not found: "[What's missing]. [Alternative action]."
  → "This page doesn't exist. Go back to the dashboard or search for what you need."
```

### 9.3 Microcopy Quality Standards

**Purpose:** Ensure all interface microcopy meets **microcopy quality gate** standards for clarity, consistency, and actionability.

**Applies To:** All short-form UI text — button labels, form labels, placeholder text, tooltips, menu items, badges, tags, breadcrumbs, **progressive disclosure text**.

AI generates generic microcopy defaults ("Submit", "Click here", "Read more", "Untitled") that fail to communicate specific meaning. The **action-oriented labels** pattern ensures every interactive element's label describes its specific action or destination.

**Microcopy quality checklist:**

```
BUTTONS:
□ Labels describe the specific action: "Save draft" not "Submit"
□ Destructive actions named explicitly: "Delete project" not "Remove"
□ Loading states update text: "Saving..." not generic spinner
□ Cancel buttons say "Cancel" not "Dismiss" or "Close" (unless closing a non-modal)

FORM LABELS:
□ Labels are nouns/noun phrases: "Email address" not "Enter your email"
□ Placeholder text shows format example: "name@example.com" not "Enter email"
□ Help text explains constraints: "Must be at least 8 characters"
□ Required fields marked consistently

NAVIGATION:
□ Menu items describe destination: "Account settings" not "Settings"
□ Breadcrumbs show location hierarchy, not generic "Back"
□ Links describe destination: "View all projects" not "Click here"
□ Action-oriented labels on CTAs: "Start free trial" not "Get started"

EMPTY STATES:
□ Explain what will appear: "No notifications yet"
□ Include guidance: "You'll see notifications when someone mentions you"
□ Provide action if applicable: "Create your first project"

TOOLTIPS:
□ Add information, don't repeat the label
□ Keep under 150 characters
□ Explain why, not just what: "Required for account recovery" not "Enter phone number"
```

**Progressive disclosure text** patterns:
- "Show more" / "Show less" (not "Expand" / "Collapse" for user-facing content)
- "Show N more items" with count (not just "Show more")
- Accordion headers that describe content, not generic "Details" or "More info"

---

## Situation Index

For quick routing of common scenarios to relevant methods:

| Situation | Relevant Sections |
|-----------|-------------------|
| "Building a new page/view" | §1.1 (Discovery), §1.2 (Handoff), §3.1 (Review) |
| "Creating a new component" | §2.1 (Tokens), §2.2 (Atomic Design), §2.3 (Naming), §3.4 (Consistency) |
| "Fixing accessibility issues" | §4.1 (WCAG Checklist), §4.2 (Screen Reader), §4.4 (Contrast) |
| "Making a page responsive" | §5.1 (Breakpoints), §5.2 (Content Adaptation), §5.3 (Touch Targets) |
| "Building for iOS/Android" | §6.1 (Platform Reference), §6.2 (Decision Matrix), §6.3 (Testing) |
| "Setting up a design system" | §2.1 (Tokens), §7.1 (Token Docs), §7.2 (Component Catalog) |
| "Integrating with Figma" | §8.1 (Figma MCP), §8.2 (Token Extraction) |
| "Reviewing AI-generated UI" | §3.1 (Review Checklist), §8.4 (Guardrails), §4.3 (Automated Scan) |
| "Design tokens and consistency" | §2.1 (Token Management), §2.4 (Gap Reporting), §7.1 (Documentation) |
| "Form design and validation" | §3.1 (Review), §4.1 (WCAG 3.3.x), §5.3 (Touch Targets) |
| "Loading and skeleton states" | §3.1 Tier 2 (Loading States), §1.3 (Visual QA) |
| "AI generating generic template layout" | §1.1 (Discovery), §3.4 (Consistency Audit) |
| "Dark patterns in checkout/consent" | §3.5 (Dark Pattern Screening), IX7 (Ethical Interaction Design) |
| "Web performance and Core Web Vitals" | §3.6 (Core Web Vitals Validation) |
| "Outdated platform conventions" | §6.4 (Platform Convention Currency) |
| "Error message writing" | §9.2 (Error Message Patterns), IX4 (Error Handling) |
| "Button labels and microcopy" | §9.3 (Microcopy Quality Standards) |
| "Voice and tone consistency" | §9.1 (Voice and Tone Consistency) |
| "Animation accessibility reduced motion" | §4.1 (WCAG 2.3.3), ACC3 (Color and Contrast — includes motion accessibility), UX-F19 |

---

## Changelog

### v1.0.0 (Current)
- Initial release + Phase 6 external review enhancements
- 9 sections covering design-to-code workflow, component governance, review gates, accessibility testing, responsive strategy, cross-platform adaptation, design system documentation, AI tooling integration, and UX content/microcopy governance
- §3.5 Dark Pattern Screening (FTC 5-category checklist, confirmshaming detection, forced continuity audit)
- §3.6 Core Web Vitals Validation (LCP, INP, CLS thresholds with AI-specific causes)
- §6.4 Platform Convention Currency Verification (training data temporal lag, guideline version check)
- §9 UX Content and Microcopy Governance (voice/tone consistency, error message framework, microcopy quality gate)
- Situation index expanded with 7 new routing entries

---

*Version 1.0.0*
*Companion to: UI/UX Domain Principles v1.0.0*
*Process gates: AI-Coding Methods §2.4, §2.5*
