---
version: "1.2.0"
status: "active"
effective_date: "2026-03-30"
domain: "ui-ux"
governance_level: "federal-statute"
---

# UI/UX Domain Principles Framework v1.2.0
## Federal Statutes for AI Agents Building Interactive Software Interfaces

> **SYSTEM INSTRUCTION FOR AI AGENTS:**
> **This document represents the FEDERAL STATUTES (Domain Principles) for the UI/UX jurisdiction.**
> * **Status:** Domain-specific laws derived from the Constitution (Meta-Principles). These principles govern AI agents building interactive software interfaces — web sites, web apps, desktop apps, and mobile apps.
> * **Hierarchy:** These statutes must comply with the Constitution (constitution.md). In case of conflict: **Bill of Rights (S-Series)** > **Constitution (Meta-Principles)** > **Domain Principles (This Document)** > **Methods/Tools (SOPs)**.
> * **Scope:** Interactive software interface design and implementation. Covers visual hierarchy, design systems, accessibility, responsive design, interaction patterns, and platform conventions.
> * **Application:** Required for all AI-assisted interface development activities, whether AI is generating UI code, reviewing interfaces, or advising on design decisions.
>
> **Action Directive:** When building or reviewing interactive interfaces, apply Constitutional principles (Meta-Principles) through the lens of these Domain Statutes, then derive appropriate Methods that satisfy both.
>
> ---
>
> **RELATIONSHIP TO CONSTITUTIONAL LAW (Meta-Principles):**
> This framework assumes the AI agent has already loaded and internalized the **constitution.md** (Constitution). The principles in this document are **derived applications** of those meta-principles to the specific domain of interactive interface design and development.
>
> **Derivation Formula:**
> `[UI/UX Failure Mode] + [Evidence-Based Prevention] + [Constitutional Basis] = [Domain Principle]`
>
> **Supremacy Reminder:**
> If conflict arises: **S-Series (Safety) > Meta-Principles > Domain Principles > Implementation Methods**
>
> **Truth Source Hierarchy:**
> Constitution > UI/UX Domain Principles > UI/UX Methods > External References (WCAG 2.2, Nielsen Norman, Apple HIG, Material Design 3)

---

## Scope and Non-Goals

### In Scope

This document governs AI-assisted interactive interface design and development:
- **Web sites** — Marketing, content, e-commerce, landing pages
- **Web apps** — SaaS, dashboards, admin panels, data-rich applications
- **Desktop apps** — Native (macOS, Windows), Electron, Tauri
- **Mobile apps** — iOS, Android, cross-platform (React Native, Flutter)
- **Visual hierarchy** — Layout composition, spacing, typography, color usage
- **Design systems** — Token architecture, component consistency, naming conventions
- **Accessibility** — WCAG 2.2 compliance, keyboard navigation, screen readers, color contrast
- **Responsive design** — Breakpoints, adaptive layouts, touch targets, content adaptation
- **Interaction design** — Feedback, affordances, state management, error handling, loading states
- **Platform conventions** — Apple HIG, Material Design 3, web platform standards

### Out of Scope (Handled Elsewhere)

The following are NOT governed by this document:
- **Presentations, slide decks, infographics** — Future Visual Communication domain
- **Print design, brochures, posters** — Future Visual Communication domain
- **Documents and reports** — Future Visual Communication domain
- **UX process and workflow gates** — AI-Coding Methods §2.4 (UX Elaboration) and §2.5 (Visual Design Specs)
- **Image retrieval and presentation** — Multimodal RAG domain
- **General AI safety and alignment** — Constitution S-Series (Bill of Rights)
- **Code quality and testing** — AI-Coding domain principles and methods

### Future Considerations

- **Internationalization/localization (i18n/l10n)** — RTL layout, text expansion, string externalization, locale-aware formatting — flagged for future version. AI-generated UIs rarely account for text expansion (German text is ~30% longer than English), RTL layout requirements, or locale-specific date/number formats.

### Scope Boundary: UI/UX vs ai-coding §2.4/§2.5

AI-Coding Methods §2.4 (UX Elaboration) and §2.5 (Visual Design Specs) define **process gates** — when to map user flows, when to create mockups, what approval gates to pass. They remain as-is and are not superseded.

This UI/UX domain defines **substance** — what good visual hierarchy is, what accessibility requires, what interaction patterns to use. Process tells you *when* to do UX work; substance tells you *what good UX is*.

Cross-references exist in both directions: ai-coding §2.4/§2.5 reference this domain for substance; this domain references ai-coding for process gates.

If a concern is about *when to do UX work* → AI-Coding Methods §2.4/§2.5.
If a concern is about *what the UX should look like* → This document.

---

## Domain Context: Why UI/UX Requires Specific Governance

### The Unique Constraints of AI-Generated Interfaces

A huge amount of AI-assisted development involves building interfaces. When AI generates UI code, specific failure modes emerge that do not exist — or occur at much lower rates — in human-developed interfaces:

**1. Pattern-Matching Visual Output, Not Document Structure**
AI generates markup that *looks right* visually but lacks semantic structure. It produces `<div>` soup with inline styles because training data rewards visual output, not document semantics. Screen readers, keyboard navigation, and assistive technologies depend on semantic HTML that AI systematically omits.

**2. Context-Independent Generation**
Each AI generation is context-independent — it lacks awareness of existing design tokens, component libraries, and visual patterns established elsewhere in the project. This produces inconsistent spacing, typography, and component treatments across views that a human developer working in the codebase would naturally maintain.

**3. Training Data Distribution Bias**
AI training data is dominated by common UI libraries (Bootstrap, Tailwind, Material UI), producing interfaces that default to card grids, hamburger menus, and generic template layouts regardless of the application's actual needs. This "synthetic genericism" creates functionally adequate but undifferentiated interfaces.

**4. Happy Path Optimization**
AI focuses on the primary user flow and omits error states, loading states, empty states, and edge cases. It generates complete page renders rather than incremental states, missing skeleton screens, progress indicators, and graceful degradation that real applications require.

**5. Visual Complexity Over Usability**
AI optimizes for "impressive looking" rather than usable. It adds decorative gradients, shadows, animations, and visual effects because visually complex output is more likely to be accepted, even when simpler interfaces would serve users better.

**6. Platform Agnosticism**
AI applies web conventions to native apps and vice versa. It generates bottom navigation on iPad (Material Design pattern, wrong for iPadOS), hamburger menus on desktop (mobile pattern, wrong for wide screens), and iOS-style switches on Android. Training data skews heavily toward web, so non-web platforms receive web patterns by default.

### Why Meta-Principles Alone Are Insufficient

The Constitution (Meta-Principles) establishes universal reasoning principles. However, UI/UX has domain-specific failure modes requiring domain-specific governance:

| Constitution Says | But UI/UX Specifically Needs | Concrete Failure the Constitution Can't Prevent |
|-------------------|------------------------------|--------------------------------------------------|
| "Bias Awareness & Fairness" (general) | WCAG 2.2 Level AA compliance, ARIA authoring patterns, focus management, touch target minimums, color contrast ratios | AI generates `<div role="button">` without `tabindex="0"` or keyboard handler. Constitution says "be accessible" but doesn't specify ARIA contract requirements. WebAIM data: pages with ARIA present average 41% more detected errors than those without. |
| "Resource Efficiency & Waste Reduction" (general) | Platform-specific conventions (HIG vs Material vs Web), knowing WHEN to deviate | AI applies Material Design bottom navigation to an iPad app. Constitution says "use established solutions" but doesn't distinguish which platform's solutions apply. Apple HIG and Material Design give contradictory guidance for the same interaction pattern. |
| "Structural Foundations" (general) | Design token architecture, atomic design hierarchy, component naming conventions | AI generates `color: #3b82f6` in 5 different components instead of `var(--color-primary)`. Constitution says "organize clearly" but doesn't address design token indirection or cross-file visual consistency. GitClear 2025: 4x code clone growth with AI. |
| "Verification & Validation" (general) | Accessibility auditing procedures, responsive breakpoint testing, cross-platform validation | AI generates a form that passes all code tests but has 3:1 contrast ratio (fails WCAG AA 4.5:1 minimum). Constitution says "verify" but doesn't specify visual/perceptual verification criteria. |
| "Context Engineering" (general) | Understanding user viewport, device capabilities, platform conventions, existing design system | AI generates a desktop-first layout with 14px touch targets (Apple HIG minimum: 44pt). Constitution says "load context" but doesn't specify what UI context means. |
| "Structural Foundations" (general) | Design token system before component implementation, spacing scale before layout | AI generates 15 different spacing values across components. Constitution says "build foundations first" but doesn't specify that the spacing scale IS a foundation. |

### Evidence Base

This framework derives from analysis of interface design research including:
- **Nielsen's 10 Usability Heuristics** (1994, updated 2020) — foundational heuristic evaluation framework
- **WCAG 2.2** (W3C, 2023) — Web Content Accessibility Guidelines, Level A/AA compliance standard
- **Apple Human Interface Guidelines** (2025/2026) — Liquid Glass design language, platform-specific conventions
- **Material Design 3** (Google) — Cross-platform design system with Android-first patterns
- **Laws of UX** — Fitts's Law, Hick's Law, Jakob's Law, Miller's Law, Doherty Threshold, Gestalt principles
- **WebAIM Million** (2025) — Annual accessibility analysis of top 1,000,000 home pages
- **GitClear 2025** — Developer productivity analysis showing 4x growth in code clones with AI assistance
- **Stack Overflow Developer Survey** (2025) — AI tool adoption and quality impact data
- **Baymard Institute** — Evidence-based e-commerce and web UX research
- **Brad Frost, Atomic Design** (2016) — Component architecture methodology
- **W3C Design Tokens** — Specification for cross-platform design token format
- **Don Norman** — Affordances, signifiers, mapping, feedback (The Design of Everyday Things)
- **Eye-tracking research** — F-pattern and Z-pattern scanning behavior (Nielsen Norman Group)
- **Typography readability studies** — Optimal line length (45-75 characters), contrast ratios, font size minimums
- **ISO/IEC 40500:2025** — WCAG 2.2 adopted as international standard (October 2025), strengthening legal basis for accessibility compliance
- **W3C Design Tokens Community Group v2025.10** — Stable specification for cross-platform design token interchange format
- **WCAG 2.5.8 Target Size (Minimum)** — 24×24px minimum (Level AA), 44×44px recommended (Level AAA / Apple HIG / Material Design)
- **MobileSoft 2025: "Breaking Barriers in Mobile Accessibility"** — 540 accessibility issues analyzed; accessibility-specific prompts sometimes produced MORE errors in AI-generated code
- **Serezlic & Quijada 2025** — AI dark pattern generation thesis: AI e-commerce UIs contain deceptive design patterns unless explicitly prompted to avoid them
- **FTC "Bringing Dark Patterns to Light"** (2022) — Federal Trade Commission report defining 5 dark pattern categories (nagging, obstruction, sneaking, interface interference, forced action)

---

## Failure Mode Taxonomy

AI-generated interfaces have specific failure modes that require dedicated prevention. Each failure mode is framed with the AI-specific angle: *why AI produces this failure at a higher rate or in a qualitatively different way than a human developer*.

| Code | Failure Mode | AI-Specific Framing | Series |
|------|--------------|---------------------|--------|
| **UX-F1** | Inaccessible Markup | AI generates `<div>` soup instead of semantic HTML because it pattern-matches visual output, not document structure. Missing alt text, ARIA roles, landmark regions. ARIA misuse is worse than no ARIA: WebAIM finds 41% more errors on pages with ARIA. | ACC |
| **UX-F2** | Spacing/Typography Inconsistency | AI generates hard-coded `margin: 24px` instead of referencing `--spacing-md` tokens because it lacks design-system context across files. GitClear: 4x code clone growth with AI. | DS |
| **UX-F3** | Platform Convention Violation | AI applies web/iOS patterns to Android (and vice versa) because training data skews heavily toward web conventions. Bottom sheets on iOS, hamburger menus on iPad. | PL |
| **UX-F5** | Design System Drift | AI generates one-off component styles instead of using existing tokens/components because each generation is context-independent — it doesn't see the project's design system. | DS |
| **UX-F6** | Missing Visual Hierarchy | AI generates flat, equally-weighted layouts because it applies generic component patterns without compositional hierarchy awareness. Every element gets the same visual weight. | VH |
| **UX-F7** | Missing Interaction Feedback | AI omits loading states, error feedback, and confirmation dialogs because it focuses on the "happy path" and doesn't model user uncertainty or system latency. | IX |
| **UX-F8** | Breakpoint Failure | AI generates desktop-first layouts that overflow or produce tiny touch targets on mobile because it lacks viewport-aware testing context. | RD |
| **UX-F9** | Readability Failure | AI generates text blocks with excessive line length (>90 characters), insufficient contrast, or small font sizes because it optimizes for information density over readability. | VH |
| **UX-F10** | Color Accessibility Violation | AI uses color as the only differentiator (red/green for status) and generates insufficient contrast ratios because it doesn't model color vision deficiencies. 8% of males have some form of color vision deficiency. | ACC |
| **UX-F12** | Perceived Performance Neglect | AI omits skeleton screens and progressive loading because it generates complete page renders, not incremental states. Causes layout shifts (poor CLS scores) and perceived slowness. | IX |
| **UX-F13** | Missing Affordance | AI generates clickable elements that lack visual affordance (flat text links, icon-only buttons without labels) because it doesn't model user discoverability. Users can't click what they can't identify as interactive. | IX |
| **UX-F14** | Keyboard Navigation Failure | AI creates focus traps, missing focus indicators, and illogical tab order because keyboard interaction isn't part of visual output generation. | ACC |
| **UX-F15** | Component Inconsistency | AI generates different visual treatments for the same function across views because each generation is context-independent. A "Save" button looks different on every page. | DS |
| **UX-F16** | Generic/Template UI | AI defaults to Bootstrap-style card grids and cookie-cutter layouts because training data is dominated by common UI libraries. 75% of firms adopted GenAI tools, producing identical-looking interfaces. Lacks design intentionality. | VH |
| **UX-F17** | Component Misapplication | AI selects components by name matching rather than UX appropriateness (modal when toast suffices, data table when list is clearer, dropdown when radio buttons would be better). | IX |
| **UX-F18** | Form Validation Inconsistency | AI produces inconsistent validation patterns within a single app (sometimes inline, sometimes on-submit; mixed error styling) due to lack of cross-file awareness. | IX |
| **UX-F19** | Motion/Animation Accessibility Neglect | AI generates CSS animations, transitions, parallax, and scroll-triggered effects without `prefers-reduced-motion` because training data favors visually impressive demos. Approximately 35% of adults over 40 experience vestibular sensitivity — uncontrolled motion causes dizziness, nausea, or seizure risk. | ACC |
| **UX-F21** | Dark Pattern / Deceptive Design | AI generates confirmshaming copy, misdirecting color emphasis, pre-checked opt-ins, and roach motel flows because training data is saturated with conversion-optimized patterns. Serezlic & Quijada 2025: AI e-commerce UIs contain dark patterns unless explicitly prompted to avoid them. FTC, EU DSA, CPRA, and EAA create legal liability. | IX |

**Note on UX-F4 and UX-F11:** These failure modes from the initial taxonomy were evaluated against the AI-specificity gate during research. UX-F4 (Over-Designed Interface) and UX-F11 (Information Architecture Failure) are common in both AI and human development without strong evidence of qualitatively different AI failure patterns. They are captured as secondary concerns within VH-Series and IX-Series principles respectively, but do not warrant dedicated failure mode codes.

---

## Framework Overview: The Six Principle Series

This framework organizes domain principles into six series that address different functional aspects of interactive interface design. This mirrors the Constitution's functional organization and groups principles by what they govern.

### The Six Series

1. **Visual Hierarchy Principles (VH-Series)**
   * **Role:** Layout Composition and Readability
   * **Function:** Governing HOW AI structures visual layouts — spacing, typography, focal points, visual weight, and information scanning patterns. These principles ensure interfaces guide users' attention effectively.

2. **Design System Principles (DS-Series)**
   * **Role:** Consistency and Token Architecture
   * **Function:** Governing HOW AI maintains visual consistency — design tokens, component reuse, naming conventions, and cross-file coherence. These principles prevent the "every generation is independent" failure pattern.

3. **Accessibility Principles (ACC-Series)**
   * **Role:** Inclusive Design Compliance
   * **Function:** Governing HOW AI ensures interfaces are usable by everyone — WCAG 2.2 compliance, keyboard navigation, screen reader support, color contrast, and focus management. These principles address AI's systematic tendency toward inaccessible markup.

4. **Responsive Design Principles (RD-Series)**
   * **Role:** Multi-Device Adaptation
   * **Function:** Governing HOW AI handles different viewport sizes — breakpoint strategy, touch targets, content adaptation, and mobile-first considerations. These principles prevent desktop-only generation.

5. **Interaction Principles (IX-Series)**
   * **Role:** User Feedback and State Management
   * **Function:** Governing HOW AI implements user interactions — loading states, error handling, affordances, microinteractions, navigation patterns, form design, component selection, and ethical interaction design. These principles address the "happy path only" failure pattern and AI's tendency toward deceptive design.

6. **Platform Principles (PL-Series)**
   * **Role:** Convention Compliance
   * **Function:** Governing HOW AI respects platform-specific conventions — Apple HIG, Material Design 3, web standards, and cross-platform adaptation. These principles prevent platform-agnostic generation.

### The Twenty Principles

**VH-Series: Visual Hierarchy Principles** — *How AI structures visual layouts*

| Principle | Primary Failure Mode Addressed |
|-----------|-------------------------------|
| VH1: Layout Composition and Visual Weight | UX-F6 (Missing Visual Hierarchy) |
| VH2: Typography and Readability | UX-F9 (Readability Failure) |
| VH3: Design Intentionality | UX-F16 (Generic/Template UI) |

**DS-Series: Design System Principles** — *How AI maintains visual consistency*

| Principle | Primary Failure Mode Addressed |
|-----------|-------------------------------|
| DS1: Design Token Architecture | UX-F2 (Spacing/Typography Inconsistency) |
| DS2: Component Consistency | UX-F15 (Component Inconsistency) |
| DS3: Design System Discovery | UX-F5 (Design System Drift) |

**ACC-Series: Accessibility Principles** — *How AI ensures inclusive interfaces*

| Principle | Primary Failure Mode Addressed |
|-----------|-------------------------------|
| ACC1: Semantic Markup and ARIA Contracts | UX-F1 (Inaccessible Markup) |
| ACC2: Keyboard Navigation and Focus Management | UX-F14 (Keyboard Navigation Failure) |
| ACC3: Color and Contrast Compliance | UX-F10 (Color Accessibility Violation) |

**RD-Series: Responsive Design Principles** — *How AI handles multiple viewports*

| Principle | Primary Failure Mode Addressed |
|-----------|-------------------------------|
| RD1: Responsive Layout Strategy | UX-F8 (Breakpoint Failure) |
| RD2: Touch Target and Input Adaptation | UX-F8 (Breakpoint Failure) |

**IX-Series: Interaction Principles** — *How AI implements user interactions*

| Principle | Primary Failure Mode Addressed |
|-----------|-------------------------------|
| IX1: Interaction Feedback and State Communication | UX-F7 (Missing Interaction Feedback) |
| IX2: Loading and Perceived Performance | UX-F12 (Perceived Performance Neglect) |
| IX3: Affordance and Discoverability | UX-F13 (Missing Affordance) |
| IX4: Error Handling and Recovery | UX-F7 (Missing Interaction Feedback), UX-F18 (Form Validation Inconsistency) |
| IX5: Component Selection Appropriateness | UX-F17 (Component Misapplication) |
| IX6: Form Design and Validation | UX-F18 (Form Validation Inconsistency) |
| IX7: Ethical Interaction Design | UX-F21 (Dark Pattern / Deceptive Design) |

**PL-Series: Platform Principles** — *How AI respects platform conventions*

| Principle | Primary Failure Mode Addressed |
|-----------|-------------------------------|
| PL1: Platform Convention Compliance | UX-F3 (Platform Convention Violation) |
| PL2: Cross-Platform Adaptation | UX-F3 (Platform Convention Violation) |

---

## VH-Series: Visual Hierarchy Principles

*Principles governing HOW AI structures visual layouts*

### VH1: Layout Composition and Visual Weight (The Focal Point Statute)

**Constitutional Basis:** Derived from `Structural Foundations` and `Context Engineering`.

**Why This Principle Matters**
Users scan interfaces in predictable patterns (F-pattern for text-heavy, Z-pattern for landing pages). Without deliberate visual hierarchy, every element competes equally for attention, forcing users to consciously parse the layout instead of being guided through it. AI generates flat layouts because it applies generic component patterns without compositional awareness — it doesn't reason about which element should be seen first, second, third.

**Failure Mode**
UX-F6 (Missing Visual Hierarchy): AI generates layouts where all elements have equal visual weight. Headers, body text, buttons, and secondary actions all occupy similar visual prominence. Users cannot quickly identify the primary action or most important information. Observable symptoms: no clear focal point, uniform spacing, same-size elements, no visual grouping via Gestalt proximity/similarity.

**Definition**
Every interface layout MUST establish a clear visual hierarchy through deliberate variation in size, color, contrast, spacing, and position. Primary actions and critical information MUST be visually dominant. Secondary elements MUST be visually subordinate. The hierarchy MUST be scannable without reading — users should understand the page structure within 3-5 seconds of first exposure.

**Domain Application**
- **Size contrast:** Primary headings at least 1.5x the size of body text. Primary CTAs visually larger than secondary actions.
- **Whitespace as structure:** Use spacing to create visual groups (Gestalt proximity). Related items closer together, unrelated items further apart. Minimum 1.5x spacing between groups vs. within groups.
- **F/Z-pattern alignment:** Place primary content along natural eye-tracking patterns. Logo/nav top-left, primary CTA in the terminal area of the dominant scanning pattern.
- **Visual weight budget:** Limit bold, high-contrast, or colored elements to ≤3 focal points per viewport. More than 3 competing focal points = no focal point.
- **Progressive disclosure:** Present essential information first; secondary details available on interaction (expand, tab, scroll).

**Validation Criteria**
- [ ] Page has a clear primary focal point identifiable within 3 seconds
- [ ] Heading hierarchy follows H1 > H2 > H3 with decreasing visual weight
- [ ] Primary and secondary actions are visually distinguishable
- [ ] Related elements are grouped with consistent spacing
- [ ] No more than 3 high-emphasis elements compete per viewport
- [ ] Squint test: blurring the page reveals the intended hierarchy

**Human Interaction Points**
- When the interface serves multiple equally-important user goals (competing focal points require business priority input).
- When brand guidelines constrain visual hierarchy options.
- When stakeholders disagree about what the primary action should be.

**Cross-References**
- VH2 (Typography and Readability) — typography is a primary tool for hierarchy
- DS1 (Design Token Architecture) — spacing and sizing should come from tokens
- See also: ai-coding §2.5 (Visual Design Specs) for process gates

---

### VH2: Typography and Readability (The Legibility Statute)

**Constitutional Basis:** Derived from `Bias Awareness & Fairness` and `Context Engineering`.

**Why This Principle Matters**
Typography is the primary medium of interface communication — the majority of UI content is text. AI generates text blocks that prioritize information density over readability: excessive line lengths that force eye-tracking errors, insufficient contrast that strains vision, and font sizes optimized for fitting more content rather than comfortable reading. Research consistently shows that readability directly impacts comprehension, task completion, and user satisfaction.

**Failure Mode**
UX-F9 (Readability Failure): AI generates text with line lengths exceeding 90 characters (optimal: 45-75), insufficient contrast ratios, body text below 16px on desktop, or line heights below 1.4x font size. Observable symptoms: users squinting, losing their place between lines, or avoiding reading entirely.

**Definition**
All interface text MUST meet evidence-based readability thresholds. Body text MUST use a line length of 45-75 characters, a minimum size of 16px on desktop (minimum 14px on mobile with appropriate line height), a line height of at least 1.4x the font size, and contrast ratios meeting WCAG AA standards (4.5:1 for normal text, 3:1 for large text ≥18pt or bold ≥14pt).

**Domain Application**
- **Line length:** Constrain content areas to 45-75 characters wide. Use `max-width` on text containers (typically 65ch or ~600-700px for body text).
- **Font size:** Desktop body text minimum 16px. Mobile body text minimum 14px. Never use a single font size across all elements — establish a type scale (e.g., major third 1.25 or perfect fourth 1.333).
- **Line height:** Body text at 1.5-1.6x font size. Headings at 1.1-1.3x (tighter is acceptable for large text). Never use `line-height: 1` on multi-line text.
- **Type scale:** Use a mathematical scale (e.g., 14/16/20/25/32/40) rather than arbitrary sizes. Minimum 3 distinct sizes in the scale.
- **Paragraph spacing:** Space between paragraphs should be 0.5-1.0x the line height. Never use zero paragraph spacing with no indentation.
- **Font selection:** Prefer system font stacks or established UI typefaces. AI should not introduce novel or decorative fonts for body text.

**Validation Criteria**
- [ ] Body text line length is 45-75 characters (measure with browser dev tools)
- [ ] Body text size ≥16px desktop, ≥14px mobile
- [ ] Line height ≥1.4x font size for body text
- [ ] Type scale uses consistent mathematical ratios
- [ ] Contrast ratio ≥4.5:1 for normal text, ≥3:1 for large text (WCAG AA)
- [ ] No font size below 12px used anywhere in the interface

**Human Interaction Points**
- When brand typography guidelines specify sizes below recommended minimums.
- When content length makes 45-75 character line length impractical (data-dense dashboards).
- When internationalization requires accommodating languages with different character widths.

**Cross-References**
- ACC3 (Color and Contrast Compliance) — contrast ratios overlap
- VH1 (Layout Composition) — type scale creates visual hierarchy
- DS1 (Design Token Architecture) — typography values should be tokenized

---

### VH3: Design Intentionality (The Anti-Template Statute)

**Constitutional Basis:** Derived from `Context Engineering` and `Discovery Before Commitment`.

**Why This Principle Matters**
AI defaults to generic, template-driven layouts because training data is dominated by common UI libraries. The result is "synthetic genericism" — 75% of firms adopting GenAI tools produce interfaces that look identical. Card grids, hero sections with gradient overlays, and Bootstrap-standard layouts appear regardless of whether they serve the application's actual user needs. Design intentionality means choosing layout patterns because they serve the content and user tasks, not because they're the most common patterns in training data.

**Failure Mode**
UX-F16 (Generic/Template UI): AI generates Bootstrap-style card grids, standard hero + 3-column feature sections, and cookie-cutter layouts for every application regardless of content type or user tasks. Observable symptoms: the interface could belong to any product; no design element reflects the specific application domain, user workflow, or content type.

**Definition**
Interface layouts MUST be driven by content type, user tasks, and application domain — not by template defaults. AI MUST articulate why a specific layout pattern was chosen for the content being presented. If the rationale is "this is a common pattern," the AI MUST evaluate whether a common pattern genuinely serves this specific use case or is merely a default.

**Domain Application**
- **Content-driven layout:** Data dashboards use dense grid layouts with data visualization. E-commerce uses product grids with filtering. Document apps use wide reading panes. Chat apps use conversation threads. The layout should be recognizable as serving its content type.
- **Task-flow alignment:** Primary user tasks should drive layout structure. If the primary task is comparison, use side-by-side layouts. If it's sequential input, use a stepper or wizard. If it's monitoring, use a dashboard with status indicators.
- **Template escape velocity:** When generating a standard pattern (card grid, hero section), explicitly evaluate: "Does this layout serve the specific content, or am I defaulting to the most common training data pattern?" Document the rationale.
- **Brand differentiation:** Interfaces should reflect the application's identity through deliberate design choices — color palette, typography, spacing rhythm, illustration style — not through generic component library defaults.

**Validation Criteria**
- [ ] Layout pattern matches the content type and primary user task
- [ ] Design rationale can articulate why this layout was chosen over alternatives
- [ ] Interface is visually distinguishable from a default Bootstrap/Tailwind template
- [ ] Component choices reflect application domain (not just the most common library default)

**Human Interaction Points**
- When time constraints require using a template as a starting point (acceptable, but the AI should note what should be customized later).
- When the application genuinely benefits from a conventional layout (not every interface needs to be unique — many benefit from familiarity per Jakob's Law).
- When brand guidelines or design system constraints limit layout options.

**Cross-References**
- DS3 (Design System Discovery) — use existing design system tokens for differentiation
- PL1 (Platform Convention Compliance) — platform conventions are not templates; follow conventions while expressing design intentionality within them

---

## DS-Series: Design System Principles

*Principles governing HOW AI maintains visual consistency*

### DS1: Design Token Architecture (The Indirection Statute)

**Constitutional Basis:** Derived from `Structural Foundations` and `Single Source of Truth`.

**Why This Principle Matters**
AI generates hard-coded values (`margin: 24px`, `color: #3b82f6`, `font-size: 14px`) instead of referencing design tokens (`var(--spacing-md)`, `var(--color-primary)`, `var(--font-size-sm)`) because each generation is context-independent — the AI doesn't see the project's token system across files. This produces the 4x code clone growth documented by GitClear (2025). Hard-coded values are impossible to maintain at scale: changing a brand color requires finding and updating every instance rather than changing one token.

**Failure Mode**
UX-F2 (Spacing/Typography Inconsistency): AI generates `margin-top: 24px` in one component and `margin-top: 20px` in another for the same conceptual spacing. Colors appear as hex codes throughout the codebase with slight variations (`#3b82f6` vs `#3B82F6` vs `rgb(59, 130, 246)`). Observable symptoms: inconsistent spacing rhythms across pages, color drift between components, typography that doesn't match the established scale.

**Definition**
All visual properties — spacing, color, typography, shadows, border radii, breakpoints — MUST reference design tokens rather than hard-coded values. If the project has an existing token system, the AI MUST discover and use it. If no token system exists, the AI MUST establish foundational tokens before generating components. The minimum viable token set includes: spacing scale, color palette (with semantic aliases), type scale, and border radius scale.

**Domain Application**
- **Token discovery:** Before generating UI code, check for existing token definitions: CSS custom properties (`--`), SCSS/Less variables, JS/TS theme objects, Tailwind config, or design token JSON files. Use `query_project("design tokens CSS variables theme")` to discover existing patterns.
- **Spacing scale:** Use a consistent scale (e.g., 4px base: 4/8/12/16/24/32/48/64). Never use arbitrary spacing values. All margins, paddings, and gaps should reference named tokens.
- **Color tokens:** Use semantic naming (`--color-primary`, `--color-error`, `--color-surface`) not descriptive naming (`--blue-500`). Maintain separation between primitive tokens (the actual colors) and semantic tokens (what they mean).
- **Type tokens:** Font sizes, weights, line heights, and letter spacing should all be tokenized. Reference the type scale, not arbitrary sizes.
- **Token format:** Match the project's existing format. If CSS custom properties, use `var(--token-name)`. If Tailwind, use utility classes. If styled-components, use theme references. Don't introduce a new token format into an existing project.

**Validation Criteria**
- [ ] No hard-coded color values in component code (hex, rgb, hsl) — all reference tokens
- [ ] No hard-coded spacing values — all reference spacing tokens or scale
- [ ] No hard-coded font sizes — all reference type scale tokens
- [ ] Token names are semantic (describe purpose, not appearance)
- [ ] Existing project token system is used (not a new system introduced alongside it)
- [ ] Minimum viable token set exists: spacing, colors, typography, border radius

**Human Interaction Points**
- When no design system exists and the AI needs to establish foundational tokens (present options for spacing scale, color palette).
- When existing tokens are incomplete and need extension.
- When migrating from hard-coded values to tokens (scope and priority decision).

**Cross-References**
- DS2 (Component Consistency) — components should use tokens
- DS3 (Design System Discovery) — discover existing tokens before generating
- See also: title-15-ui-ux-cfr §2 (Component Library Governance) for token management procedures

---

### DS2: Component Consistency (The Same-Function-Same-Appearance Statute)

**Constitutional Basis:** Derived from `Structural Foundations` and `Resource Efficiency & Waste Reduction`.

**Why This Principle Matters**
AI generates different visual treatments for the same function across views because each code generation is context-independent. A "Save" button that's blue with rounded corners on one page becomes green with square corners on another. A card component with 16px padding in one view uses 24px in another. This violates Jakob's Law — users expect consistent behavior from consistent-looking elements — and creates maintenance burden as each visual variant becomes a separate code path.

**Failure Mode**
UX-F15 (Component Inconsistency): AI generates a primary button as `bg-blue-500 rounded-lg px-4 py-2` in one component and `bg-blue-600 rounded-md px-6 py-3` in another. Same-function elements (cards, forms, navigation items) have different spacing, colors, borders, and typography across views. Observable symptoms: the interface looks like it was built by multiple designers who never communicated.

**Definition**
Elements that serve the same function MUST have the same visual treatment across the entire application. Visual consistency MUST be achieved through shared components or shared style references, not by independently styling each instance. When the AI generates a UI element, it MUST check whether an equivalent component already exists in the project and reuse it.

**Domain Application**
- **Component reuse:** Before creating a new component, search for existing components that serve the same function. Use `query_project("button component")` or equivalent.
- **Variant system:** Use explicit variants (primary/secondary/tertiary, small/medium/large) rather than one-off style overrides. If a variant doesn't exist, create it as a named variant rather than a local override.
- **Visual audit:** When generating a new view, verify that buttons, cards, form elements, navigation items, and other repeated components match their existing implementations.
- **Atomic design alignment:** Atoms (buttons, inputs) should be identical everywhere. Molecules (form groups, card headers) should be built from consistent atoms. Organisms (navigation bars, sidebars) should be built from consistent molecules.

**Validation Criteria**
- [ ] Same-function elements have identical styling across all views
- [ ] Components are imported/reused, not re-implemented per view
- [ ] Button variants (primary, secondary, destructive) are visually distinct and consistent
- [ ] Card components use the same padding, border radius, and shadow everywhere
- [ ] Form elements (inputs, selects, checkboxes) share a consistent visual treatment

**Human Interaction Points**
- When a new component variant is genuinely needed (not just a visual preference).
- When existing components have inconsistencies that need resolution.
- When the codebase has accumulated visual debt from prior inconsistent generation.

**Cross-References**
- DS1 (Design Token Architecture) — consistency comes from shared tokens
- DS3 (Design System Discovery) — discover existing components before creating new ones
- IX5 (Component Selection Appropriateness) — use the right component, then make it consistent

---

### DS3: Design System Discovery (The Context-First Statute)

**Constitutional Basis:** Derived from `Context Engineering` and `Discovery Before Commitment`.

**Why This Principle Matters**
Each AI generation is context-independent — the AI lacks awareness of existing design tokens, component libraries, and visual patterns established elsewhere in the project. This is the root cause of UX-F5 (Design System Drift): the AI generates new styles because it never looked for existing ones. The fix is not better generation — it's better context loading. The AI must discover the project's design system before writing any UI code.

**Failure Mode**
UX-F5 (Design System Drift): AI introduces a new spacing value, color, or component variant that conflicts with the established design system. Over time, the codebase accumulates competing style definitions. Observable symptoms: multiple similar-but-not-identical components, growing CSS file sizes, design inconsistencies that are hard to trace.

**Definition**
Before generating any UI code, the AI MUST discover the project's existing design system by querying for: (1) design tokens/CSS variables/theme configuration, (2) existing components that serve similar functions, and (3) established patterns for the type of UI being built. If no design system exists, the AI MUST note this gap and recommend establishing one before building multiple views.

**Domain Application**
- **Pre-generation discovery:** Before writing UI code, run discovery queries: design tokens, existing components, layout patterns, color usage, spacing conventions.
- **Token file identification:** Look for theme files, CSS variable definitions, Tailwind config, styled-components themes, or design token JSON files.
- **Component inventory:** Identify existing reusable components before creating new ones.
- **Pattern recognition:** Identify established patterns for common elements (how does this project handle cards? forms? navigation? modals?).
- **Gap reporting:** If no design system is found, explicitly report this: "No design tokens or shared components found. Recommend establishing a base token set before building additional views."

**Validation Criteria**
- [ ] Design system discovery was performed before generating UI code
- [ ] Existing tokens and components were identified and referenced
- [ ] No new token values introduced when existing ones serve the same purpose
- [ ] No new components created when equivalent existing components are available
- [ ] Design system gaps are documented when discovered

**Human Interaction Points**
- When no design system exists and one needs to be established.
- When existing design system has gaps that need filling.
- When multiple competing design patterns are discovered (need resolution direction).

**Cross-References**
- DS1 (Design Token Architecture) — what to look for during discovery
- DS2 (Component Consistency) — reuse what you discover
- See also: Context Engine MCP — `query_project()` for design system discovery

---

## ACC-Series: Accessibility Principles

*Principles governing HOW AI ensures inclusive interfaces*

### ACC1: Semantic Markup and ARIA Contracts (The Document Structure Statute)

**Constitutional Basis:** Derived from `Bias Awareness & Fairness` and `Structural Foundations`.

**Why This Principle Matters**
AI generates visually correct but semantically empty markup — `<div>` and `<span>` elements with click handlers instead of `<button>`, custom dropdowns instead of `<select>`, and unlabeled form fields. Worse, when AI does attempt accessibility, it often misuses ARIA: adding `role="button"` to a `<div>` without keyboard handling, or using `aria-label` in contradiction to visible text. WebAIM's annual analysis consistently finds that pages with ARIA present have *more* accessibility errors (41% more) than pages without — because incorrect ARIA is worse than no ARIA. AI exacerbates this pattern because it pattern-matches ARIA attribute names without understanding the contracts they create.

**Failure Mode**
UX-F1 (Inaccessible Markup): AI generates `<div onclick="...">` instead of `<button>`. Forms lack `<label>` associations. Navigation lacks `<nav>` landmarks. Images lack meaningful `alt` text (or have `alt="image"`). Custom components lack ARIA roles, states, and properties. When ARIA is added, it's incomplete: `<div role="button">` without `tabindex="0"`, `onkeydown`, and `aria-pressed`. Observable symptoms: screen readers cannot navigate the interface; keyboard-only users cannot interact with controls.

**Definition**
All interactive interfaces MUST use semantic HTML as the foundation. Native HTML elements (`<button>`, `<a>`, `<input>`, `<select>`, `<nav>`, `<main>`, `<header>`, `<footer>`, `<section>`) MUST be preferred over `<div>`/`<span>` with ARIA roles. When custom components require ARIA, the AI MUST implement the complete ARIA contract — role, states, properties, keyboard interaction pattern, and focus management — as specified in WAI-ARIA Authoring Practices. Incomplete ARIA is worse than no ARIA.

**Domain Application**
- **Semantic element preference:** Use `<button>` for actions, `<a>` for navigation, `<input>` for data entry, `<select>` for selection from options. The `<div>` element should never have `onclick` without a very specific reason and full ARIA implementation.
- **Landmark regions:** Every page must have `<main>`, `<nav>`, `<header>`, `<footer>` as appropriate. Screen readers use landmarks for page navigation.
- **Form associations:** Every `<input>` must have an associated `<label>` (via `for`/`id` or nesting). Placeholder text is NOT a label substitute.
- **Image alt text:** Every `<img>` must have an `alt` attribute. Informative images need descriptive alt text. Decorative images use `alt=""`. Never use `alt="image"` or `alt="photo"`.
- **ARIA completeness rule:** If you add a `role`, you MUST also implement: all required `aria-*` states/properties for that role, keyboard interaction per WAI-ARIA Authoring Practices, and focus management. If you cannot implement the complete contract, use the native HTML element instead.
- **Heading hierarchy:** Use `<h1>` through `<h6>` in order. Never skip heading levels. Never use headings for visual styling alone.

**Validation Criteria**
- [ ] No `<div>` or `<span>` with `onclick` without `role`, `tabindex`, and keyboard handler
- [ ] All form inputs have associated labels
- [ ] All images have meaningful `alt` attributes (or `alt=""` for decorative)
- [ ] Page has `<main>`, `<nav>`, and heading hierarchy
- [ ] Any ARIA roles have complete implementation (role + states + keyboard + focus)
- [ ] Heading levels do not skip (no h1 → h3)
- [ ] Links have descriptive text (not "click here" or "read more" alone)

**Human Interaction Points**
- When complex custom widgets require ARIA patterns not covered by WAI-ARIA Authoring Practices.
- When third-party component libraries have known accessibility issues.
- When accessibility remediation of legacy code requires prioritization decisions.

**Cross-References**
- ACC2 (Keyboard Navigation) — keyboard handling is part of the ARIA contract
- ACC3 (Color and Contrast) — visual accessibility complements structural accessibility
- See also: Multimodal RAG P5 (Accessibility Compliance) for image accessibility in retrieval contexts
- See also: Storytelling A3 (Accessibility by Design) for narrative-level accessibility (cognitive load, sensory diversity, cultural inclusion)

---

### ACC2: Keyboard Navigation and Focus Management (The Keyboard Equity Statute)

**Constitutional Basis:** Derived from `Bias Awareness & Fairness` and `Verification & Validation`.

**Why This Principle Matters**
AI generates interfaces that are only usable with a mouse because keyboard interaction isn't part of visual output generation. Focus states are omitted or removed for "cleaner" aesthetics. Tab order follows DOM order, which may not match visual order in complex layouts. Modal dialogs don't trap focus, letting keyboard users tab into invisible background content. These failures make the interface completely unusable for keyboard-only users, screen reader users, and many users with motor disabilities.

**Failure Mode**
UX-F14 (Keyboard Navigation Failure): AI removes default focus indicators (`outline: none` without replacement), creates focus traps (modal without focus return), or produces illogical tab order (visual left-to-right but DOM order reads differently). Custom interactive elements (accordions, tabs, carousels) lack keyboard support entirely. Observable symptoms: pressing Tab moves focus to invisible or unexpected elements; pressing Enter/Space on focused elements does nothing.

**Definition**
Every interactive element MUST be reachable and operable via keyboard alone. Focus indicators MUST be visible (never removed without a replacement). Tab order MUST match visual reading order. Focus MUST be managed for overlays, modals, and dynamic content — trapped within when open, returned to trigger when closed. Skip-to-content links MUST be provided for repeated navigation.

**Domain Application**
- **Focus visibility:** Never use `outline: none` or `outline: 0` without providing an alternative focus indicator (e.g., `box-shadow`, `border`, or custom outline). The `:focus-visible` pseudo-class can be used to show focus only for keyboard users.
- **Tab order:** Ensure DOM order matches visual order. If CSS reorders elements visually (flexbox `order`, grid placement), verify tab order still makes sense. Use `tabindex="0"` to add elements to natural tab order; avoid `tabindex` values > 0.
- **Modal focus management:** When a modal opens, move focus to the first focusable element inside it. Trap focus within the modal (Tab wraps from last to first focusable element). When the modal closes, return focus to the element that triggered it.
- **Skip navigation:** Provide a "Skip to main content" link as the first focusable element for pages with repeated navigation.
- **Keyboard interaction patterns:** Buttons activate on Enter and Space. Links activate on Enter only. Tab panels, menus, and tree views use arrow keys for internal navigation.
- **Dynamic content:** When content updates dynamically (AJAX, SPA navigation), manage focus appropriately — announce changes via ARIA live regions or move focus to the new content.

**Validation Criteria**
- [ ] Every interactive element is reachable via Tab key
- [ ] Every interactive element is operable via Enter/Space/arrows as appropriate
- [ ] Focus indicators are always visible (no `outline: none` without replacement)
- [ ] Tab order matches visual reading order
- [ ] Modals trap focus and return it on close
- [ ] Skip-to-content link present on pages with navigation
- [ ] Dynamic content changes are announced or receive focus

**Human Interaction Points**
- When complex widget keyboard patterns need user testing to validate.
- When visual design conflicts with visible focus indicators.
- When third-party components lack keyboard support and need wrappers.

**Cross-References**
- ACC1 (Semantic Markup) — native elements come with built-in keyboard support
- IX1 (Interaction Feedback) — focus state is a form of interaction feedback
- See also: WAI-ARIA Authoring Practices for keyboard interaction patterns

---

### ACC3: Color and Contrast Compliance (The Perceivability Statute)

**Constitutional Basis:** Derived from `Bias Awareness & Fairness` and `Verification & Validation`.

**Why This Principle Matters**
AI uses color as the sole differentiator for information (red = error, green = success, no other indicator) and generates insufficient contrast ratios because it doesn't model color vision deficiencies. Approximately 8% of males and 0.5% of females have some form of color vision deficiency, with red-green (deuteranopia/protanopia) being the most common. AI-generated interfaces frequently fail WCAG AA contrast requirements because the AI optimizes for visual appeal over perceivability.

**Failure Mode**
UX-F10 (Color Accessibility Violation): AI uses red/green as the only indicator for error/success states. Form validation relies solely on red borders with no icon or text indicator. Status badges use color alone (green dot = active, red dot = inactive). Text contrast ratios fall below 4.5:1 for body text or 3:1 for large text. Observable symptoms: users with color vision deficiency cannot distinguish states; users in high-glare environments cannot read low-contrast text.

**Definition**
Color MUST NOT be the sole means of conveying information. Every use of color to communicate status, error, or state MUST be accompanied by a non-color indicator (icon, text, pattern, shape). All text MUST meet WCAG 2.2 AA contrast ratio requirements: 4.5:1 for normal text (<18pt or <14pt bold), 3:1 for large text (≥18pt or ≥14pt bold), and 3:1 for UI components and graphical objects.

**Domain Application**
- **Status indicators:** Pair color with icon and text. Error: red + warning icon + "Error: [message]". Success: green + checkmark icon + "Success". Never rely on color alone.
- **Form validation:** Error states include: red border + error icon + descriptive error message. The error message must describe what's wrong and how to fix it, not just "Invalid input."
- **Charts and data visualization:** Use patterns, shapes, or direct labels in addition to color. Color-blind-safe palettes (e.g., ColorBrewer) should be preferred.
- **Contrast checking:** Verify contrast ratios during development using browser dev tools or dedicated tools (Colour Contrast Analyser). Check both light and dark mode.
- **Focus indicators:** Focus outlines must have sufficient contrast against both the element background and the page background.
- **Dark mode:** When generating dark mode styles, re-verify all contrast ratios — colors that pass in light mode often fail in dark mode and vice versa.
- **Motion accessibility:** All animations and transitions must respect `prefers-reduced-motion`. Wrap decorative animations in `@media (prefers-reduced-motion: no-preference)`. AI tends to add gratuitous CSS transitions, parallax scrolling, and hover effects without motion reduction support — approximately 35% of adults over 40 experience vestibular sensitivity.

**Validation Criteria**
- [ ] No information conveyed by color alone — every color coding has a non-color equivalent
- [ ] Body text contrast ratio ≥4.5:1 (WCAG AA)
- [ ] Large text contrast ratio ≥3:1 (WCAG AA)
- [ ] UI component contrast ratio ≥3:1 (borders, icons, form controls)
- [ ] Error/success/warning states use icon + text + color (not color alone)
- [ ] Dark mode contrast ratios verified separately
- [ ] Charts/visualizations use labels or patterns in addition to color
- [ ] Animations/transitions respect `prefers-reduced-motion` media query (WCAG 2.1 SC 2.3.3)

**Human Interaction Points**
- When brand colors produce insufficient contrast ratios (need brand team input).
- When dark mode color palette needs separate verification.
- When data visualization complexity requires specialized color-blind-safe palettes.
- When animation is core to conveying information (provide non-animated alternative).

**Cross-References**
- VH2 (Typography and Readability) — contrast is a component of readability
- ACC1 (Semantic Markup) — ARIA roles complement visual indicators
- See also: Multimodal RAG P6 (Accessibility Compliance) for accessibility in visual content

---

## RD-Series: Responsive Design Principles

*Principles governing HOW AI handles multiple viewports*

### RD1: Responsive Layout Strategy (The Viewport Adaptation Statute)

**Constitutional Basis:** Derived from `Context Engineering` and `Verification & Validation`.

**Why This Principle Matters**
AI generates desktop-first layouts without considering how they adapt to smaller viewports. Content that fits in a 1440px-wide viewport overflows or becomes unreadable on a 375px mobile screen. Navigation designed for desktop (horizontal menu bars) becomes unusable on mobile without explicit responsive handling. AI lacks viewport-aware testing context — it generates for one viewport and doesn't model the adaptation needed for others.

**Failure Mode**
UX-F8 (Breakpoint Failure): AI generates a 3-column layout that overflows on mobile with no responsive behavior. Tables extend beyond viewport. Horizontal navigation wraps awkwardly on tablet. Long content lines force horizontal scrolling. Observable symptoms: horizontal scroll bars on mobile, overlapping elements, text too small to read, interactive elements too close together.

**Definition**
All interface layouts MUST be responsive across the standard breakpoint spectrum: mobile (320-479px), tablet (480-767px), small desktop (768-1023px), and desktop (1024px+). Content MUST remain readable and interactive at every breakpoint. Layouts MUST use fluid sizing and appropriate breakpoints rather than fixed widths. Mobile-first CSS is RECOMMENDED to ensure small-viewport usability is the baseline.

**Domain Application**
- **Breakpoint strategy:** Define breakpoints based on content, not devices. Common breakpoints: 480px, 768px, 1024px, 1280px. The content should determine where the layout breaks, not arbitrary device widths.
- **Fluid grids:** Use percentage widths, `fr` units, or `flex` rather than fixed pixel widths. `max-width` constrains content areas on large viewports while allowing fluidity on smaller ones.
- **Content stacking:** Multi-column layouts should stack to single column on mobile. Sidebar content should move below main content or become collapsible.
- **Navigation adaptation:** Desktop horizontal navigation should become a collapsible menu on mobile. Use appropriate patterns: bottom tab bar for mobile apps (5 items max), hamburger for secondary navigation, persistent sidebar for desktop dashboard apps.
- **Image and media:** Use `max-width: 100%` on images. Consider `<picture>` element for art-directed responsive images. Lazy-load below-the-fold images.
- **Testing requirement:** Verify layout at minimum 320px (smallest common mobile), 768px (tablet), and 1024px (desktop). Check for horizontal overflow, text readability, and interactive element spacing at each.

**Validation Criteria**
- [ ] Layout renders without horizontal scroll at 320px viewport width
- [ ] Content is readable at all breakpoints (no text smaller than 14px on mobile)
- [ ] Multi-column layouts stack appropriately on narrow viewports
- [ ] Navigation is usable on all viewport sizes
- [ ] No fixed-width elements cause overflow on mobile
- [ ] Images scale appropriately and don't overflow containers

**Human Interaction Points**
- When the application is desktop-only by explicit design decision.
- When complex data tables need specialized mobile treatment (card view, horizontal scroll with sticky columns).
- When specific device targeting is required (kiosk, specific tablet model).

**Cross-References**
- RD2 (Touch Target Adaptation) — responsive layout affects touch target sizing
- VH1 (Layout Composition) — hierarchy may change across breakpoints
- VH2 (Typography and Readability) — font sizes may adjust across breakpoints

---

### RD2: Touch Target and Input Adaptation (The Mobile Interaction Statute)

**Constitutional Basis:** Derived from `Bias Awareness & Fairness` and `Context Engineering`.

**Why This Principle Matters**
AI generates interfaces with desktop-sized interactive elements (small checkboxes, compact button rows, inline links with minimal padding) that become impossible to accurately tap on touch devices. Apple HIG specifies 44x44pt minimum touch targets; Material Design specifies 48x48dp. AI doesn't model finger size or touch accuracy — it generates visually compact elements that are pixel-precise with a cursor but unusable with a finger.

**Failure Mode**
UX-F8 (Breakpoint Failure — touch variant): Interactive elements on mobile have tap targets smaller than 44x44px. Buttons are spaced too close together, causing wrong-target taps. Links within body text have no additional padding for touch contexts. Observable symptoms: users tap wrong elements, miss small targets, or need multiple attempts to hit the right control.

**Definition**
All interactive elements on touch devices MUST meet WCAG 2.5.8 Level AA minimum (24×24px) and SHOULD meet platform guidelines: 44x44pt (Apple HIG) or 48x48dp (Material Design), whichever is appropriate for the platform. Adjacent interactive elements MUST have sufficient spacing (minimum 8px gap) to prevent accidental activation of neighboring targets. Input methods MUST adapt to context: touch keyboards for mobile inputs, appropriate `inputmode` attributes for numeric/email/phone fields.

**Domain Application**
- **Touch target sizing:** Buttons, links, and interactive elements must be at least 44x44px on touch devices. If the visual element is smaller (e.g., an icon), extend the tap area using padding.
- **Spacing between targets:** Maintain minimum 8px gap between adjacent interactive elements. Toolbars and button groups should not pack buttons tighter than this.
- **Input types:** Use `inputmode="numeric"` for number fields, `type="email"` for email fields, `type="tel"` for phone fields. These trigger appropriate mobile keyboards.
- **Touch-friendly controls:** Replace hover-dependent interactions with tap-friendly alternatives on touch devices. Tooltips should be accessible via tap, not just hover.
- **Scroll regions:** Ensure scrollable areas have sufficient size and are not nested in ways that cause scroll hijacking. Pull-to-refresh should work as expected on mobile.

**Validation Criteria**
- [ ] All interactive elements meet 44x44px minimum touch target size
- [ ] Touch targets meet WCAG 2.5.8 minimum: 24×24px (AA), 44×44px recommended (AAA/HIG/Material)
- [ ] Adjacent interactive elements have ≥8px gap
- [ ] Input fields use appropriate `type` and `inputmode` attributes
- [ ] No hover-only interactions on touch devices
- [ ] Forms are usable with mobile keyboards (appropriate input types, no tiny fields)

**Human Interaction Points**
- When design requires compact UI that conflicts with touch target minimums (data-dense tables on mobile).
- When platform-specific touch target sizes differ (Apple 44pt vs Material 48dp).
- When gestures beyond tap are needed (swipe, long-press) and need documentation.

**Cross-References**
- RD1 (Responsive Layout Strategy) — layout determines touch target context
- PL1 (Platform Convention Compliance) — touch targets differ by platform
- ACC2 (Keyboard Navigation) — keyboard and touch are complementary input methods

---

## IX-Series: Interaction Principles

*Principles governing HOW AI implements user interactions*

### IX1: Interaction Feedback and State Communication (The Feedback Loop Statute)

**Constitutional Basis:** Derived from `Visible Reasoning & Traceability` and `Failure Recovery & Resilience`.

**Why This Principle Matters**
AI focuses on the "happy path" — generating the interface for when everything works correctly — and omits the states users encounter when things are in progress, have failed, or are empty. Real applications spend significant time in transitional states: loading, submitting, processing, failing, recovering. Users interpret silence as broken — if they click a button and nothing visually changes, they click again (and again), potentially triggering duplicate submissions or confusion.

**Failure Mode**
UX-F7 (Missing Interaction Feedback): AI generates a form with a submit button but no loading indicator, no success confirmation, and no error display. A data table loads with no skeleton or spinner, showing a flash of empty space. A delete action has no confirmation dialog and no undo capability. Observable symptoms: users don't know if their action registered; they resubmit; they don't understand what went wrong when it fails.

**Definition**
Every user action that triggers a system response MUST provide immediate visual feedback confirming the action was received. State transitions MUST be communicated clearly: idle → loading → success/error. Destructive actions MUST require confirmation. The interface MUST handle five states for data-dependent views: loading, empty, partial, complete, and error.

**Domain Application**
- **Button feedback:** Buttons should show a loading state when their action is in progress (spinner, disabled state with progress indicator). Prevent double-submission by disabling during processing.
- **Form submission:** Show clear loading → success or loading → error transitions. Success: confirmation message or redirect. Error: specific error messages near the fields that failed, with the form preserving user input.
- **Destructive actions:** Delete, remove, and irreversible actions require a confirmation step (dialog, inline confirm, or undo capability). Never silently delete without confirmation.
- **Five states:** Every data-dependent view should handle: (1) Loading — skeleton or spinner, (2) Empty — helpful empty state with guidance, (3) Partial — incomplete data with clear indicators, (4) Complete — the full data view, (5) Error — what went wrong and how to recover.
- **Optimistic UI:** For low-risk actions (like/bookmark), show the result immediately and roll back on failure. For high-risk actions (payment/delete), wait for server confirmation.

**Validation Criteria**
- [ ] Every button action shows feedback within 100ms of click (Doherty Threshold)
- [ ] Forms show loading state during submission
- [ ] Forms preserve user input on error
- [ ] Error messages are specific and actionable (not just "Something went wrong")
- [ ] Destructive actions require confirmation
- [ ] Data views handle all five states (loading, empty, partial, complete, error)
- [ ] No silent failures — every error is communicated to the user

**Human Interaction Points**
- When error messages require domain-specific language.
- When destructive actions have undo capability vs. confirmation dialog trade-off.
- When optimistic vs. pessimistic UI patterns affect business logic.

**Cross-References**
- IX2 (Loading and Perceived Performance) — loading states are a subset of feedback
- IX4 (Error Handling) — error states are a subset of feedback
- IX6 (Form Design) — form feedback patterns

---

### IX2: Loading and Perceived Performance (The Progress Communication Statute)

**Constitutional Basis:** Derived from `Visible Reasoning & Traceability` and `Context Engineering`.

**Why This Principle Matters**
AI generates complete page renders — the final state of a page with all data loaded — without considering the loading sequence. Real applications need to communicate progress during data fetching: skeleton screens show the page structure before data arrives, progress indicators show deterministic progress, and shimmer effects indicate indeterminate loading. Without these, users see blank pages, layout shifts when content finally loads (poor Cumulative Layout Shift scores), and perceived slowness even when actual load times are fast. Research shows that perceived performance matters more than actual performance — a 2-second load with a skeleton screen feels faster than a 1-second load with a blank flash (Doherty Threshold: systems should respond within 400ms to maintain user flow).

**Failure Mode**
UX-F12 (Perceived Performance Neglect): AI generates a data table component that shows nothing until all data loads, then suddenly renders the complete table — causing a jarring layout shift. A dashboard page loads as a blank white screen for 2 seconds before all widgets appear simultaneously. Observable symptoms: blank/white page flashes, layout shifts when content loads, no indication that loading is happening.

**Definition**
Interfaces MUST communicate loading progress rather than showing blank states. Skeleton screens MUST be used for content-heavy views to preserve layout stability during loading. Progress indicators MUST match the loading type: determinate (progress bar with percentage) for known-duration operations, indeterminate (spinner, shimmer) for unknown-duration operations. Layout MUST be stable during loading — the skeleton should match the final layout to prevent Cumulative Layout Shift (CLS target: <0.1).

**Domain Application**
- **Skeleton screens:** For content-heavy pages (feeds, dashboards, data tables), render skeleton shapes matching the expected layout before data loads. Skeletons should match the final element sizes and positions.
- **Inline loaders:** For button-triggered operations, show inline loading states (spinner replacing button text, progress bar below input field) rather than full-page overlays.
- **Progress matching:** Use determinate progress (progress bar) for file uploads, multi-step processes, and operations with known duration. Use indeterminate progress (spinner) for API calls and operations with unknown duration.
- **Layout stability:** Reserve space for dynamic content using `min-height` or `aspect-ratio` to prevent layout shifts. Images should have explicit `width`/`height` attributes.
- **Stale-while-revalidate:** For frequently-refreshing data (dashboards, feeds), show cached data immediately with a subtle "updating" indicator rather than a full loading state.

**Validation Criteria**
- [ ] Content-heavy pages show skeleton screens during loading
- [ ] No blank page flashes during data fetching
- [ ] Progress indicators match loading type (determinate vs. indeterminate)
- [ ] Layout remains stable during loading (CLS target: <0.1)
- [ ] Images have explicit dimensions to prevent layout shift
- [ ] Long-running operations show progress communication

**Human Interaction Points**
- When skeleton screen fidelity vs. simplicity needs balancing.
- When loading performance optimization requires architectural decisions.
- When offline/slow-connection states need specialized handling.

**Cross-References**
- IX1 (Interaction Feedback) — loading is a form of feedback
- RD1 (Responsive Layout) — skeleton screens must be responsive
- See also: ai-coding §3.1.4 (Technology Selection) for framework-specific loading patterns

---

### IX3: Affordance and Discoverability (The Clickability Statute)

**Constitutional Basis:** Derived from `Explicit Over Implicit` and `Context Engineering`.

**Why This Principle Matters**
AI generates clickable elements that lack visual affordance — flat text links indistinguishable from body text, icon-only buttons without labels or tooltips, and interactive cards without visual cues that they're clickable. The AI generates what looks clean and minimal, but minimalism without affordance creates mystery meat navigation — users can't click what they can't identify as interactive. Don Norman's principle of signifiers: the design must signal what actions are possible and how to perform them.

**Failure Mode**
UX-F13 (Missing Affordance): AI generates a card component that navigates on click but has no hover state, no cursor change, and no visual indicator of interactivity. Text links are styled identically to body text with no underline or color differentiation. Icon buttons have no tooltip, label, or ARIA label to indicate their function. Observable symptoms: users don't discover interactive elements; they hover randomly looking for cursor changes; they miss key functionality.

**Definition**
Every interactive element MUST provide clear visual signals that it is interactive. Links MUST be visually distinguished from body text (underline, color, or both). Buttons MUST look like buttons (clear boundaries, contrast with background). Icon-only elements MUST have tooltips AND accessible labels. Interactive containers (clickable cards, list items) MUST provide at least one visual cue (hover state, border, shadow, or chevron) indicating interactivity.

**Domain Application**
- **Link styling:** Links should be underlined, colored differently from body text, or both. Remove underlines only when the link's context makes it obviously interactive (navigation menus, clearly-styled CTAs). Body text links must always be distinguishable.
- **Button appearance:** Buttons should have clear visual boundaries — background color, border, or both. Ghost buttons (transparent background, border only) are acceptable for secondary actions. Text-only "buttons" without any visual container should be avoided for primary actions.
- **Icon buttons:** Always pair with: (1) a visible text label, OR (2) a tooltip AND `aria-label`. Icon-only buttons are acceptable only when the icon is universally understood (close ✕, hamburger ☰, search 🔍) and still require an `aria-label`.
- **Clickable containers:** When cards or list items are clickable, provide: (1) cursor: pointer on hover, (2) hover/focus state change (shadow, border, background), AND (3) a visual cue like a chevron (›) or "Learn more" link.
- **Cursor states:** Interactive elements should show `cursor: pointer`. Disabled elements should show `cursor: not-allowed`. Non-interactive elements should use default cursor.

**Validation Criteria**
- [ ] Links are visually distinguishable from body text
- [ ] Buttons have clear visual boundaries
- [ ] Icon-only elements have tooltips and accessible labels
- [ ] Interactive containers show hover/focus state changes
- [ ] Cursor changes appropriately for interactive vs. non-interactive elements
- [ ] No "mystery meat" — every interactive element's purpose is discoverable

**Human Interaction Points**
- When minimal design aesthetic conflicts with affordance requirements.
- When icon meaning is ambiguous and needs user testing.
- When clickable area boundaries are unclear in complex layouts.

**Cross-References**
- ACC1 (Semantic Markup) — semantic elements provide built-in affordance
- ACC2 (Keyboard Navigation) — focus indicators are affordance for keyboard users
- IX1 (Interaction Feedback) — feedback confirms the affordance was correct

---

### IX4: Error Handling and Recovery (The Graceful Failure Statute)

**Constitutional Basis:** Derived from `Failure Recovery & Resilience` and `Visible Reasoning & Traceability`.

**Why This Principle Matters**
AI generates error handling that is either absent (no error states), generic ("Something went wrong"), or inconsistent (different error patterns in different parts of the app). Real applications need error handling that tells users what happened, whether it's their fault or a system issue, and what they can do about it. AI generates the success state and leaves error handling as an afterthought or omits it entirely.

**Failure Mode**
UX-F7 (Missing Interaction Feedback — error variant) and UX-F18 (Form Validation Inconsistency): AI generates a form where some fields validate inline while others only validate on submit. Error messages say "Invalid" without explaining what's wrong. Network errors show a console error but no user-facing feedback. 404 pages show the browser default. Observable symptoms: inconsistent error patterns across the app; generic, unhelpful error messages; users don't know how to recover from errors.

**Definition**
Error states MUST be handled consistently across the application. Error messages MUST be specific (what went wrong), human-readable (not error codes or stack traces), and actionable (what the user can do). Form validation MUST follow a consistent pattern throughout the app: either inline validation, on-blur validation, or on-submit validation — not a mix. Network errors, empty states, and 404/500 pages MUST have designed, user-friendly error displays.

**Domain Application**
- **Error message format:** "[What went wrong] [What to do about it]". Example: "Email address is not valid. Please enter an email like name@example.com." Never: "Invalid input" or "Error 422."
- **Form validation consistency:** Choose one validation timing pattern and use it everywhere: (1) Inline: validate on blur after first submit attempt, (2) On-submit: validate all fields at once, show all errors, focus the first error field. Don't mix approaches within the same app.
- **Error proximity:** Place error messages directly adjacent to the element they describe. For forms: below the field or inline next to it. For page-level errors: at the top of the content area with a way to jump to the problem.
- **Recovery guidance:** Every error state should offer a recovery path: retry button for transient errors, edit field for validation errors, navigation link for 404s, contact support for unrecoverable errors.
- **Error styling:** Use consistent error styling throughout the app: same color (not just color — see ACC3), same icon, same positioning, same typography.

**Validation Criteria**
- [ ] Error messages are specific and actionable (not generic)
- [ ] Form validation follows a single consistent pattern across the app
- [ ] Error messages appear adjacent to the element they describe
- [ ] Every error state offers a recovery path
- [ ] Network/system errors have designed error displays (not browser defaults)
- [ ] Error styling is consistent throughout the app
- [ ] Error states are accessible (announced to screen readers, not color-only)

**Human Interaction Points**
- When error messages require domain-specific language or business logic.
- When error recovery requires decisions about data preservation vs. retry.
- When third-party API error codes need human-friendly translation.

**Cross-References**
- IX1 (Interaction Feedback) — errors are a form of feedback
- IX6 (Form Design) — form-specific error patterns
- ACC3 (Color and Contrast) — errors must not rely on color alone

---

### IX5: Component Selection Appropriateness (The Right Tool Statute)

**Constitutional Basis:** Derived from `Resource Efficiency & Waste Reduction` and `Context Engineering`.

**Why This Principle Matters**
AI selects components by name matching rather than UX appropriateness. It generates a modal dialog because the prompt mentioned "dialog" even when a toast notification would suffice. It uses a data table for 3 items when a simple list would be clearer. It reaches for a dropdown select when radio buttons (2-5 options) would reduce cognitive load and interaction cost. This happens because AI matches component names to patterns in training data rather than evaluating the user's actual interaction needs.

**Failure Mode**
UX-F17 (Component Misapplication): AI uses a full-screen modal for a success confirmation (toast would suffice). A dropdown select for a yes/no choice (toggle or radio buttons would be better). A data table with sorting/filtering for 3 static items (a simple list would be clearer). An accordion for 2 items (just show both). Observable symptoms: interactions require more user effort than necessary; the interface feels "heavy" for simple tasks.

**Definition**
Component selection MUST be driven by the interaction requirements, not by naming or pattern matching. The AI MUST evaluate: (1) how many options/items are involved, (2) how often the user interacts with this element, (3) what the simplest component is that meets the requirement, and (4) what information density is appropriate. Simpler components SHOULD be preferred when they adequately serve the need.

**Domain Application**
- **Selection components:** 2-3 options → radio buttons or segmented control. 4-7 options → radio buttons or dropdown. 8+ options → dropdown or searchable select. Binary choice → toggle switch or checkbox.
- **Feedback components:** System confirmation → toast notification (auto-dismiss). User decision required → inline confirmation or dialog. Critical/destructive confirmation → modal dialog.
- **Data display:** ≤5 items → simple list. 6-20 items with few properties → list or simple table. 20+ items with multiple properties → data table with search/sort/filter.
- **Content expansion:** 2-3 sections → just show them all. 4-7 sections → tabs or accordion. 8+ sections → sidebar navigation with sections.
- **Navigation:** ≤5 primary items → tab bar (mobile) or horizontal nav (desktop). 6-10 items → sidebar navigation. 11+ items → grouped sidebar or mega menu.

**Validation Criteria**
- [ ] Modals are used only when user decision/focus isolation is required
- [ ] Dropdown selects are not used for <4 options (use radio buttons)
- [ ] Data tables are not used for <6 items (use simple lists)
- [ ] Toast notifications are used for non-blocking confirmations
- [ ] Accordions are not used for <3 items (just show the content)
- [ ] Component choice rationale can be articulated based on interaction requirements

**Human Interaction Points**
- When component choice affects business flow (e.g., modal for legal agreement vs. inline checkbox).
- When design system has specific component guidelines that override general rules.
- When user research indicates a preference different from the default recommendation.

**Cross-References**
- DS2 (Component Consistency) — once selected, use components consistently
- IX1 (Interaction Feedback) — component choice affects feedback patterns
- PL1 (Platform Convention Compliance) — some component choices are platform-specific

---

### IX6: Form Design and Validation (The Data Entry Statute)

**Constitutional Basis:** Derived from `Verification & Validation` and `Context Engineering`.

**Why This Principle Matters**
Forms are the primary mechanism for user data input, and AI generates them with inconsistent patterns. Validation timing varies between fields in the same form. Error messages appear in different positions. Labels may be replaced with placeholder-only styling. Required fields may not be marked. These inconsistencies create cognitive overhead for users who must figure out a new interaction pattern for each form field.

**Failure Mode**
UX-F18 (Form Validation Inconsistency): AI generates a registration form where email validates on blur, password validates on submit, and username validates on keystroke. Error messages appear below some fields, inline for others, and in a toast for the submission error. Some required fields have asterisks, others don't. Observable symptoms: users don't know when to expect validation, can't predict where error messages will appear, and miss required fields.

**Definition**
Forms MUST follow consistent patterns within an application. All forms in an app MUST use the same: validation timing (inline/on-blur/on-submit), error message positioning, required field indication, label positioning, and field grouping approach. Single-column layouts SHOULD be used for most forms (research shows faster completion than multi-column). Labels MUST be visible (not placeholder-only).

**Domain Application**
- **Single-column layout:** Use single-column forms by default. Multi-column is acceptable only for closely-related short fields (city/state/zip, first/last name) and must be tested at mobile breakpoints.
- **Label positioning:** Labels above fields (best for most forms) or to the left (acceptable for short forms in wide layouts). Never use placeholder-only labels — they disappear when the user starts typing, removing context.
- **Required fields:** Mark all required fields consistently (asterisk with "* Required" legend, or mark optional fields as "Optional"). Don't leave field requirement ambiguous.
- **Validation timing:** Choose one pattern for the whole app. Recommended: validate on blur after first submit attempt (don't overwhelm users with errors before they've tried submitting).
- **Error placement:** Always below or inline next to the field. Never at the top of the form without also marking the individual fields. Use `aria-describedby` to associate error messages with fields.
- **Field grouping:** Use `<fieldset>` and `<legend>` for related field groups (address, payment info). Visual grouping should match semantic grouping.

**Validation Criteria**
- [ ] All forms use consistent validation timing within the app
- [ ] Error messages appear in consistent positions
- [ ] Required fields are consistently indicated
- [ ] Labels are visible at all times (not placeholder-only)
- [ ] Single-column layout used for standard forms
- [ ] Form fields have appropriate `type` and `inputmode` attributes
- [ ] Error messages associated with fields via `aria-describedby`

**Human Interaction Points**
- When form structure affects business logic (multi-step wizard vs. single page).
- When validation rules require business domain knowledge.
- When form length vs. completion rate trade-offs need balancing.

**Cross-References**
- IX4 (Error Handling) — form errors are a type of error handling
- ACC1 (Semantic Markup) — form accessibility requires semantic HTML
- RD2 (Touch Target Adaptation) — form inputs need appropriate touch target sizes

---

### IX7: Ethical Interaction Design (The Anti-Deception Statute)

**Constitutional Basis:** Derived from `Visible Reasoning & Traceability` and `Bias Awareness & Fairness`.

**Why This Principle Matters**
AI generates interfaces optimized for conversion metrics because training data is saturated with growth-hacked, A/B-tested patterns designed to maximize clicks, sign-ups, and purchases — regardless of whether those actions serve the user. Confirmshaming ("No thanks, I don't want to save money"), misdirecting color emphasis (bright "Accept All" vs. muted "Manage Preferences"), pre-checked opt-ins, hidden costs revealed late in checkout, and roach motel flows (easy to enter, hard to exit) all appear in AI-generated UIs unless explicitly prompted to avoid them. This is not a hypothetical concern: Serezlic & Quijada (2025) found that AI-generated e-commerce interfaces reliably contain dark patterns when optimized for conversion. Regulatory enforcement is accelerating — FTC, EU Digital Services Act, CPRA, and the European Accessibility Act all create legal liability for deceptive design.

**Failure Mode**
UX-F21 (Dark Pattern / Deceptive Design): AI generates a subscription page with pre-checked "annual billing" and the cancellation flow buried four levels deep. A cookie consent banner has a bright "Accept All" button and a text-only "Manage" link. A checkout flow reveals shipping costs only after the user enters payment information. An unsubscribe page uses confirmshaming copy: "No thanks, I prefer to miss out on exclusive deals." Observable symptoms: user actions that benefit the business but harm or mislead the user; asymmetric friction (easy to opt in, hard to opt out); information hidden until commitment point.

**Definition**
Interfaces MUST NOT use deceptive design patterns as categorized by the FTC: nagging, obstruction, sneaking, interface interference, and forced action. AI-generated UIs MUST be screened for dark pattern categories before deployment. Opt-in/opt-out flows MUST have symmetric friction — it must be as easy to decline, cancel, or unsubscribe as it is to accept, subscribe, or purchase. Pricing, costs, and commitments MUST be transparent from the beginning of the flow, not revealed incrementally.

**Domain Application**
- **Confirmshaming prevention:** Decline options must use neutral language ("No thanks" or "Skip"), never guilt-inducing copy ("No, I don't care about my health"). Both accept and decline options must have equal visual weight.
- **Symmetric friction:** If subscribing takes 1 click, unsubscribing must take ≤2 clicks. If opting in is a checkbox, opting out must be equally accessible. Cancellation flows must not require phone calls, chat sessions, or multi-page retention funnels.
- **Transparent pricing:** All costs (product, shipping, tax, fees) must be visible before the user enters payment information. No "drip pricing" where costs appear incrementally.
- **Cookie/consent banners:** "Accept" and "Reject" (or "Manage") must have equal visual prominence — same size, same styling weight. Pre-selected consent categories are not valid consent under GDPR.
- **Pre-selection prohibition:** Checkboxes for optional services, newsletter subscriptions, and data sharing must be unchecked by default. Users must opt in actively.
- **Clear exit paths:** Every flow must have a visible, accessible way to go back or cancel. Modal dialogs must have close buttons. Multi-step flows must have "Cancel" or "Back" at every step.

**Validation Criteria**
- [ ] No confirmshaming language in decline/cancel options
- [ ] Accept and decline options have equal visual prominence (same button style, not button vs. text link)
- [ ] No pre-checked opt-in checkboxes for optional services or marketing
- [ ] All costs visible before payment information is requested
- [ ] Cancellation/unsubscribe is accessible within 2 clicks from account settings
- [ ] No forced continuity without clear cancellation path
- [ ] Cookie/consent banners offer equally-prominent accept and reject options
- [ ] Exit paths (cancel, back, close) visible at every step of multi-step flows

**Human Interaction Points**
- When business requirements specify conversion-optimized patterns that may cross into dark pattern territory.
- When A/B testing results favor patterns that increase conversion through friction asymmetry.
- When legal compliance requirements (GDPR, CPRA, FTC) conflict with existing business flows.
- When third-party checkout or subscription services have built-in dark patterns.

**Cross-References**
- IX1 (Interaction Feedback) — transparent state communication prevents sneaking
- IX4 (Error Handling) — honest error messages, not error states that push upsells
- IX6 (Form Design) — form patterns must not use pre-selection or hidden defaults
- ACC1 (Semantic Markup) — deceptive patterns often correlate with poor markup (hidden elements, misleading labels)
- See also: title-15-ui-ux-cfr §3.5 (Dark Pattern Screening) — FTC 5-category checklist procedure
- See also: FTC "Bringing Dark Patterns to Light" (2022), EU Digital Services Act, CPRA
- See also: Storytelling domain — voice/tone consistency for microcopy overlaps with character voice principles

---

## PL-Series: Platform Principles

*Principles governing HOW AI respects platform conventions*

### PL1: Platform Convention Compliance (The When-In-Rome Statute)

**Constitutional Basis:** Derived from `Resource Efficiency & Waste Reduction` and `Context Engineering`.

**Why This Principle Matters**
Users develop expectations based on their platform. iOS users expect swipe-to-delete, bottom tab navigation, and SF Symbols. Android users expect the Material Design bottom app bar, floating action buttons, and system back navigation. Web users expect underlined links, browser back button behavior, and standard keyboard shortcuts. AI applies web conventions universally because training data is web-dominant, producing interfaces that feel foreign on native platforms. Per Jakob's Law, users spend most of their time on other apps — they expect your app to work the way those other apps work.

**Failure Mode**
UX-F3 (Platform Convention Violation): AI generates Material Design bottom navigation for an iPad app (Apple HIG uses sidebar navigation for iPad). AI uses a hamburger menu on desktop web (appropriate for mobile, not for wide viewports). AI implements a custom back button instead of using the system navigation. AI uses Android-style toggles in an iOS app. Observable symptoms: users can't find familiar controls; the app feels "wrong" even if they can't articulate why; platform accessibility features don't work.

**Definition**
Interfaces MUST respect the conventions of the target platform. For iOS: follow Apple Human Interface Guidelines. For Android: follow Material Design 3 guidelines. For web: follow web platform conventions (semantic HTML, standard controls, expected keyboard shortcuts). When building cross-platform: use a shared design language with platform-specific adaptations for navigation, input controls, and system integration.

**Domain Application**
- **iOS conventions:** Use SF Symbols for icons. Tab bar at bottom (≤5 items). Large title navigation bars. Swipe gestures for back navigation and list actions. Pull-to-refresh. Native-feeling transitions (push for drill-down, modal for new context).
- **Android/Material conventions:** Bottom app bar or navigation rail. Floating Action Button for primary action. Material motion (shared axis transitions). System back button support. Top app bar with contextual actions.
- **Web conventions:** Underlined or clearly-styled links. Standard keyboard shortcuts (Ctrl/Cmd+S for save, Escape for close). Browser back button must work (no breaking history). Focus visible for keyboard navigation. Standard form controls preferred over custom.
- **Platform-specific navigation:** iPad/desktop → sidebar navigation. Mobile phone → bottom tab bar. Web responsive → top navigation that collapses to hamburger on mobile.
- **System integration:** Respect platform dark mode settings. Support platform accessibility features (VoiceOver on iOS, TalkBack on Android). Use platform-native date pickers, file pickers, and share sheets where available.

**Validation Criteria**
- [ ] Target platform identified and conventions documented
- [ ] Navigation pattern matches platform convention
- [ ] Icons match platform expectations (SF Symbols for iOS, Material Icons for Android)
- [ ] Gestures and transitions match platform patterns
- [ ] System back navigation works correctly
- [ ] Platform dark mode is respected
- [ ] Platform accessibility features are supported (VoiceOver, TalkBack, screen readers)

**Human Interaction Points**
- When the application genuinely needs to diverge from platform conventions (document the rationale).
- When cross-platform consistency conflicts with platform-specific conventions.
- When platform guidelines are updated and the application needs to adapt (e.g., Liquid Glass).

**Cross-References**
- PL2 (Cross-Platform Adaptation) — how to handle platform differences
- ACC2 (Keyboard Navigation) — keyboard patterns are platform-specific
- RD2 (Touch Target Adaptation) — touch targets differ by platform (Apple 44pt, Material 48dp)

---

### PL2: Cross-Platform Adaptation (The Shared Language Statute)

**Constitutional Basis:** Derived from `Structural Foundations` and `Context Engineering`.

**Why This Principle Matters**
Cross-platform applications (React Native, Flutter, web apps used on mobile) face a tension between consistency across platforms and respecting each platform's conventions. AI either generates identical UI across all platforms (ignoring platform conventions) or generates platform-specific code without maintaining design consistency. The correct approach is a shared design language with platform-specific adaptations for navigation, interaction patterns, and system integration.

**Failure Mode**
UX-F3 (Platform Convention Violation — cross-platform variant): A React Native app looks identical on iOS and Android — using Material Design everywhere, which feels foreign to iOS users — or uses iOS conventions everywhere, which feels foreign to Android users. A responsive web app uses the same navigation pattern on mobile and desktop. Observable symptoms: the app feels native on one platform and foreign on others; platform-specific features (system back, dark mode, accessibility) don't work correctly on all platforms.

**Definition**
Cross-platform applications MUST maintain a consistent brand and design language across platforms while adapting interaction patterns, navigation, and system integration to each platform's conventions. The shared elements are: color palette, typography, spacing scale, and visual identity. The adapted elements are: navigation structure, icon sets, gesture patterns, transition animations, and system integration (pickers, share sheets, permissions).

**Domain Application**
- **Shared design language:** Color palette, type scale, spacing scale, border radius, shadow levels, and illustration style should be consistent across platforms. Users should recognize the brand regardless of platform.
- **Adapted navigation:** Bottom tabs on iOS, navigation rail or bottom bar on Android, sidebar or top nav on web. The navigation destinations can be the same; the UI chrome adapts.
- **Platform icons:** Use SF Symbols on iOS, Material Icons on Android, and SVG icons on web. Same metaphors (e.g., "share"), different visual representations per platform.
- **Input adaptation:** Use platform-native date pickers, color pickers, and file pickers where available. Custom pickers should match the platform's visual language.
- **Testing requirement:** Cross-platform apps must be tested on each target platform, not just the development platform.

**Validation Criteria**
- [ ] Shared design language is consistent across platforms (colors, typography, spacing)
- [ ] Navigation adapts to each platform's conventions
- [ ] Platform-native controls used where available (pickers, sheets, permissions)
- [ ] System integration works on each platform (dark mode, accessibility, back nav)
- [ ] App is tested on each target platform

**Human Interaction Points**
- When business requirements prioritize one platform's conventions over another.
- When cross-platform framework limitations prevent platform-specific adaptation.
- When platform update (iOS, Android, web standards) requires adaptation.

**Cross-References**
- PL1 (Platform Convention Compliance) — what conventions to follow per platform
- DS1 (Design Token Architecture) — tokens can express platform-specific values
- RD1 (Responsive Layout) — responsive design is a form of platform adaptation

---

## Meta-Principle ↔ Domain Crosswalk

This table maps each constitutional principle to its UI/UX domain applications:

| Constitutional Principle | UI/UX Application | Series |
|--------------------------|-------------------|--------|
| Bias Awareness & Fairness | WCAG 2.2 compliance, keyboard navigation, screen reader support, color contrast, touch targets | ACC, RD |
| Structural Foundations | Design token architecture, component consistency, visual grouping, layout structure | DS, VH |
| Resource Efficiency & Waste Reduction | Platform conventions (HIG, Material, Web), component selection appropriateness | PL, IX |
| Structural Foundations | Design tokens before components, spacing scale before layout, semantic HTML before ARIA | DS, ACC |
| Verification & Validation | Responsive testing, accessibility auditing, contrast checking, cross-platform validation | Methods §3 |
| Context Engineering | User viewport, device capabilities, platform conventions, existing design system discovery | DS, RD, PL |
| Discovery Before Commitment | Design system discovery, component inventory, pattern recognition before generation | DS |
| Visible Reasoning | Interaction feedback, loading states, state communication, error transparency | IX |
| Failure Recovery & Resilience | Error handling, graceful degradation, recovery guidance, state preservation | IX |
| Explicit Over Implicit | Affordances, discoverability, visible labels, clear interactive indicators | IX |
| Visible Reasoning & Traceability | Ethical interaction design, dark pattern prevention, symmetric friction | IX |
| Verification & Validation | WCAG AA compliance, contrast ratios, touch target sizes, CLS scores | All (validation criteria) |
| Verification & Validation | Progressive review gates, per-component testing, responsive spot-checks | Methods §3 |

---

## Domain Truth Sources

| Source | Authority Level | Application |
|--------|----------------|-------------|
| **Constitution (constitution.md)** | Supreme | All domain principles derive from here |
| **WCAG 2.2 / ISO/IEC 40500:2025** (W3C) | External Standard | Accessibility compliance requirements (Level AA). Adopted as international standard October 2025. |
| **Apple Human Interface Guidelines** | External Reference | iOS, macOS, iPadOS, visionOS conventions |
| **Material Design 3** (Google) | External Reference | Android, cross-platform conventions |
| **WAI-ARIA Authoring Practices** (W3C) | External Standard | Custom component accessibility patterns |
| **Nielsen's 10 Usability Heuristics** | External Reference | Foundational heuristic evaluation framework |
| **Laws of UX** | External Reference | Evidence-based interaction design laws |
| **WebAIM Million** | External Data | Annual accessibility analysis, ARIA error data |
| **W3C Design Tokens Community Group v2025.10** | External Standard | Stable specification for cross-platform design token format |
| **FTC Dark Patterns Report** (2022) | External Reference | Regulatory framework for deceptive design pattern categories |
| **GitClear Developer Reports** | External Data | Code clone and AI productivity data |

---

## Implementation Guidance

### When AI Generates UI Code

Apply principles in this order:
1. **Design System Discovery** — Discover existing tokens and components (DS3)
2. **Semantic Structure** — Use semantic HTML, not div soup (ACC1)
3. **Token Architecture** — Reference existing tokens, not hard-coded values (DS1)
4. **Visual Hierarchy** — Establish clear focal points and information hierarchy (VH1, VH2)
5. **Responsive Layout** — Ensure layout works across viewports (RD1, RD2)
6. **Interaction States** — Handle loading, error, empty, and transition states (IX1, IX2, IX4)
7. **Affordance** — Ensure interactive elements are discoverable (IX3)
8. **Ethical Design** — Screen for dark patterns and deceptive design (IX7)
9. **Platform Compliance** — Respect target platform conventions (PL1, PL2)
10. **Accessibility Audit** — Verify keyboard, contrast, ARIA completeness (ACC1, ACC2, ACC3)

### When AI Reviews UI Code

Check for failure modes in this priority:
1. **Accessibility violations** — UX-F1, UX-F10, UX-F14, UX-F19 (highest impact, legal risk)
2. **Deceptive design** — UX-F21 (legal liability, user harm)
3. **Design system drift** — UX-F2, UX-F5, UX-F15 (maintenance cost)
4. **Missing interaction states** — UX-F7, UX-F12, UX-F18 (user experience)
5. **Platform violations** — UX-F3 (user expectation mismatch)
6. **Visual hierarchy issues** — UX-F6, UX-F9, UX-F16 (usability)
7. **Component misapplication** — UX-F13, UX-F17 (interaction quality)

---

## Relationship to Methods

This Domain Principles document establishes WHAT governance applies to UI/UX. The companion methods document establishes HOW to implement these principles.

### Available Methods Documents

| Document | Version | Coverage |
|----------|---------|----------|
| **title-15-ui-ux-cfr.md** | v1.0.0 | Design-to-code workflow, component library governance, design review gates, accessibility testing, responsive breakpoint strategy, cross-platform adaptation, design system documentation, AI tooling integration |

**Methods document includes:**
- Section 1: Design-to-Code Workflow (Figma → implementation, design handoff, visual QA)
- Section 2: Component Library Governance (token management, atomic design hierarchy, naming)
- Section 3: Design Review and Validation Gates (accessibility audit, responsive check, platform check, dark pattern screening, Core Web Vitals)
- Section 4: Accessibility Testing and Auditing (WCAG checklist, screen reader testing, keyboard audit)
- Section 5: Responsive Breakpoint Strategy (breakpoint definition, testing matrix, content adaptation)
- Section 6: Cross-Platform Adaptation (shared vs. adapted elements, platform testing, convention currency verification)
- Section 7: Design System Documentation (token documentation, component catalog, pattern library)
- Section 8: AI Tooling Integration (Figma MCP, design token extraction, screenshot feedback loops)
- Section 9: UX Content and Microcopy Governance (voice/tone consistency, error messages, microcopy quality)

---

## Changelog

### v1.1.0 (Current)
- **Constitutional principle reference consolidation (Phase 5).** Updated stale principle names throughout: Accessibility and Inclusiveness → Bias Awareness & Fairness, Foundation-First Architecture → Structural Foundations, Verification Mechanisms Before Action → Verification & Validation, Transparent Reasoning and Traceability → Visible Reasoning & Traceability, Measurable Success Criteria → Verification & Validation, Incremental Validation → Verification & Validation. Updated gap table, Constitutional Basis lines, and meta-principle crosswalk table.

### v1.0.0
- Initial release + Phase 6 external review enhancements
- **Six series:** VH-Series (Visual Hierarchy), DS-Series (Design System), ACC-Series (Accessibility), RD-Series (Responsive Design), IX-Series (Interaction), PL-Series (Platform)
- **Twenty principles:** VH1-VH3, DS1-DS3, ACC1-ACC3, RD1-RD2, IX1-IX7, PL1-PL2
- **Eighteen failure modes:** UX-F1, UX-F2, UX-F3, UX-F5-UX-F10, UX-F12-UX-F19, UX-F21
- IX7 (Ethical Interaction Design): Dark pattern prevention per FTC categories, Serezlic & Quijada 2025
- UX-F19 (Motion/Animation Accessibility): `prefers-reduced-motion` requirement
- UX-F21 (Dark Pattern / Deceptive Design): Conversion-optimized deceptive patterns
- Evidence base expanded: ISO/IEC 40500:2025, DTCG v2025.10, WCAG 2.5.8, MobileSoft 2025, Serezlic & Quijada 2025, FTC dark patterns
- RD2 validation: WCAG 2.5.8 touch target thresholds added
- i18n/l10n flagged for future version
- Scope: Interactive software interfaces (web, desktop, mobile)
- Cross-references: ai-coding §2.4/§2.5 for process gates
- Domain classification: Type A (context-intensive)

---

*Version 1.2.0*
*Derived from: Constitution v2.4.1, AI Coding Methods v2.18.0*
