---
version: "1.0.0"
status: "active"
effective_date: "2026-05-14"
domain: "accounting"
governance_level: "federal-regulations"
---

# Accounting Methods v1.0.0
## Procedures for AI-Assisted Financial Record-Keeping, Reconciliation, and Compliance

**Version:** 1.0.0
**Status:** Active
**Effective Date:** 2026-05-14
**Governance Level:** Methods (Code of Federal Regulations equivalent)

> **SYSTEM INSTRUCTION FOR AI AGENTS:**
> This methods document provides HOW-TO procedures for implementing accounting domain principles, including business setup, transaction recording, reconciliation, period-end close, year-end processes, real estate procedures, AI interaction patterns, and platform-specific integration guidance. It implements the constitutional principle `meta-core-informational-readiness` for the accounting domain.

---

### Legal System Analogy

| Legal Concept | Framework Equivalent | Purpose |
|---------------|---------------------|---------|
| Bill of Rights | S-Series (constitution.md) | Immutable safety guardrails with veto authority |
| Constitution | Meta-Principles (constitution.md) | Universal reasoning laws |
| Federal Statutes | title-22-accounting.md | Domain-specific binding law |
| Rules of Procedure | rules-of-procedure.md | How the framework evolves and maintains itself |
| **Federal Regulations (CFR)** | **This document** | **Operational rules implementing statutes** |
| Agency SOPs | Tool-specific guides | Platform-specific execution |
| Secondary Authority | Reference Library | Informative (non-overriding) |

---

## Situation Index

*When you encounter this situation, go to this section.*

| Situation | Section |
|-----------|---------|
| "Setting up a new business in accounting software" | §1 (Business Setup Sequence) |
| "Creating or modifying a chart of accounts" | §1.2 (Chart of Accounts Setup) |
| "Recording a sale, invoice, or revenue" | §2.1 (Sales and Revenue) |
| "Recording a purchase, bill, or expense" | §2.2 (Purchases and Expenses) |
| "Recording a payment (sent or received)" | §2.3 (Payments) |
| "Creating a journal entry" | §2.4 (Journal Entries) |
| "Recording payroll" | §2.5 (Payroll Recording) |
| "Reconciling a bank or credit card account" | §3 (Reconciliation Workflow) |
| "Closing a month or quarter" | §4 (Period-End Close) |
| "Preparing for year-end / tax season" | §5 (Year-End Processes) |
| "Managing rental property accounting" | §6 (Real Estate & Property Procedures) |
| "Handling a 1031 exchange" | §6.4 (Like-Kind Exchanges) |
| "Setting up security deposit tracking" | §6.3 (Security Deposits & Escrow) |
| "Deciding what the AI should do vs. what needs human review" | §7 (AI Interaction Patterns) |
| "Integrating with QuickBooks Online" | Appendix A (QuickBooks Online Integration) |
| "Evaluating accounting tools or platforms" | Appendix B (Domain Tools & Platform Integrations) |
| "Computing financial values with Python/code" | §7.4 (Deterministic Compute Pattern) |

---

## §1 Business Setup Sequence

**Applies To:** Initial setup of accounting for a new business entity, migrating to a new accounting system, or configuring AI-assisted accounting for an existing business. Implements LE1 (Double-Entry Balance Invariant), EC5 (Entity & Fund Isolation), TC8 (Temporal Authority).

### 1.1 Entity Configuration

Before recording any transaction, establish the accounting entity:

1. **Legal entity identification** — Business name, EIN/SSN, entity type (sole proprietor, LLC, S-Corp, C-Corp, partnership), state of formation.
2. **Fiscal year** — Calendar year (Jan–Dec) or fiscal year. Most small businesses use calendar year. Once chosen, changing requires IRS approval (Form 1128).
3. **Accounting basis** — Cash or accrual. Cash basis recognizes revenue when received and expenses when paid. Accrual basis recognizes when earned/incurred. Small businesses under $29M average annual gross receipts may use cash basis (IRC §448). Must be consistent per entity.
4. **Functional currency** — USD for domestic entities. Multi-currency requires exchange rate tracking.
5. **Multi-entity setup** — Each LLC, corporation, or legal entity requires its own complete set of books, bank accounts, and reporting. Per EC5, never share accounts across entities.

### 1.2 Chart of Accounts Setup

The chart of accounts (COA) is the classification taxonomy for all financial transactions. Structure scales with business size:

**Small Business (sole proprietor, single-member LLC, <$500K revenue):**
- 5 top-level categories: Assets, Liabilities, Equity, Revenue, Expenses
- ~20-40 accounts, flat structure
- Standard expense categories: advertising, insurance, office, professional services, rent, repairs, supplies, taxes, travel, utilities
- Add accounts as needed — resist pre-creating accounts "just in case"

**Medium Business ($500K–$5M revenue, multiple revenue streams):**
- Same 5 categories with sub-accounts for departments or locations
- ~40-80 accounts, 2-level hierarchy
- Classes or departments for segment reporting
- Separate tracking for cost of goods sold (COGS) vs. operating expenses

**Large Business ($5M+ revenue, multi-entity, departmental):**
- Full hierarchical COA with numbered account ranges (1000s = Assets, 2000s = Liabilities, etc.)
- ~80-200+ accounts, 3+ level hierarchy
- Department codes, location codes, project codes
- Intercompany accounts for eliminations
- Cost centers for budgeting

**For all sizes:**
- Never delete accounts with transaction history — make them inactive
- Numbering convention should allow inserting new accounts between existing ones
- Review COA annually for unused accounts and missing categories

### 1.3 Bank Account Connection

1. **Separate bank accounts** — Each entity needs its own bank account(s). Per EC5, trust/escrow accounts must be separate from operating accounts.
2. **Bank feed setup** — Connect bank feeds for automated transaction import. Bank feeds reduce manual entry but require classification review (per EC6).
3. **Opening balances** — Enter opening balances as of the conversion date. For migrations, reconcile opening balances against the source system's trial balance.

### 1.4 Tax Configuration

1. **Tax ID assignment** — Associate EIN/SSN with the entity.
2. **Tax form mapping** — Configure which tax forms the entity files (1040 Schedule C, 1065, 1120, 1120-S).
3. **1099 vendor tracking** — Flag vendors who require 1099-NEC reporting (contractors paid ≥$600/year).
4. **Sales tax** — Configure nexus states, tax rates, and exemptions if applicable.

---

## §2 Transaction Recording Procedures

**Applies To:** Day-to-day transaction entry for any business type. Implements LE1 (balance), LE2 (immutability), LE3 (precision), EC6 (classification), EC7 (materiality review).

### 2.1 Sales and Revenue

**Recording sales invoices:**
1. Create invoice with customer, date, line items, amounts, and payment terms.
2. Debit: Accounts Receivable. Credit: Revenue (appropriate category).
3. Sales tax: If applicable, credit Sales Tax Payable for the tax portion.
4. When payment received: Debit Cash/Bank, Credit Accounts Receivable.

**Cash sales (no invoice):**
1. Debit: Cash/Bank. Credit: Revenue.
2. Record at point of sale with date and description.

**Advance payments / deposits received:**
1. Debit: Cash/Bank. Credit: Unearned Revenue (liability).
2. Recognize as revenue only when earned (goods delivered or services performed for accrual basis).
3. Per TC8, advance rent is always current-period income for tax purposes.

### 2.2 Purchases and Expenses

**Recording bills (accrual basis):**
1. Create bill with vendor, date, line items, amounts, and payment terms.
2. Debit: Expense or Asset account (per EC6 classification). Credit: Accounts Payable.
3. **Capitalization check:** If purchase exceeds capitalization threshold (IRS de minimis safe harbor: $2,500 per invoice/item), capitalize as asset and depreciate per TC9.
4. When payment made: Debit Accounts Payable, Credit Cash/Bank.

**Direct expenses (cash basis or immediate payment):**
1. Debit: Expense or Asset account. Credit: Cash/Bank or Credit Card.
2. Attach receipt or source document.

**Classification confidence check (per EC6, EC7):**
- Vendor name alone → low confidence → flag for human review.
- Vendor + memo + amount pattern + account history → higher confidence → may auto-categorize for known patterns.
- New vendor with no history → always flag for human review on first occurrence.

### 2.3 Payments

**Outgoing payments:**
1. Match payment to outstanding bill (Accounts Payable).
2. Debit: Accounts Payable. Credit: Cash/Bank.
3. If no bill exists (direct payment): Debit: Expense. Credit: Cash/Bank.
4. Record check number, transfer reference, or payment method.

**Incoming payments:**
1. Match payment to outstanding invoice (Accounts Receivable).
2. Debit: Cash/Bank. Credit: Accounts Receivable.
3. If partial payment: apply to oldest invoice first (unless customer specifies otherwise).
4. Record payment method and reference number.

**Owner draws / distributions:**
1. Debit: Owner's Draw (equity). Credit: Cash/Bank.
2. Per EC5, clearly distinguish from business expenses — owner draws are NOT deductible.

### 2.4 Journal Entries

Journal entries are the most flexible and most dangerous transaction type. Per EC7, journal entries always require human review.

**Standard journal entry workflow:**
1. **Draft:** Create the entry with date, accounts, debits, credits, and memo.
2. **Balance check:** Verify total debits = total credits (per LE1). Reject if unbalanced.
3. **Review:** Present draft for human approval before posting.
4. **Post:** After human approval, post the entry.
5. **Document:** Attach source documents and record the business reason in the memo.

**Common journal entry types:**
- **Adjusting entries** — Accruals, deferrals, depreciation, bad debt provisions.
- **Correcting entries** — Fix errors in posted transactions (per LE2, never edit the original).
- **Closing entries** — Revenue/expense to retained earnings at year-end.
- **Reclassification entries** — Move amounts between accounts when original classification was wrong.

### 2.5 Payroll Recording

Payroll involves multiple accounts and tax withholdings. AI should present payroll entries for review, not auto-post.

**Basic payroll entry:**
1. Debit: Salary/Wage Expense (gross pay).
2. Credit: Federal Tax Payable, State Tax Payable, FICA Payable (employee withholdings).
3. Credit: Cash/Bank (net pay to employee).
4. Debit: Payroll Tax Expense. Credit: FICA Payable, FUTA Payable, SUTA Payable (employer portion).

**Payroll taxes are time-sensitive** — deposit deadlines vary (semi-weekly, monthly, quarterly) depending on the employer's total tax liability. Late deposits incur penalties.

---

## §3 Reconciliation Workflow

**Applies To:** Monthly bank reconciliation, credit card reconciliation, loan balance verification. Implements RC11 (Reconciliation Checkpoint), LE1 (balance verification).

### 3.1 Bank Reconciliation Procedure

1. **Obtain statement** — Download or receive the bank statement for the reconciliation period.
2. **Match transactions** — Compare each bank statement line to internal records.
   - **Automatic matching:** Match by date (±3 days), exact amount, and payee/description similarity.
   - **Manual matching:** For unclear matches, present candidates ranked by confidence for human review.
3. **Identify exceptions:**
   - **Outstanding checks** — Recorded in books but not yet cleared at bank.
   - **Deposits in transit** — Recorded in books but not yet credited by bank.
   - **Bank charges/interest** — On bank statement but not yet in books (create matching entries).
   - **Errors** — Discrepancies that don't fit the above categories.
4. **Reconcile balance:**
   - Book balance ± adjustments = Bank balance ± outstanding items.
   - If balanced within tolerance ($0 preferred, <$1.00 acceptable): mark reconciled.
   - If not balanced: investigate — do NOT force-match or drop exceptions (per RC11).
5. **Document and close** — Record reconciliation date, any adjustments made, and remaining exceptions with investigation notes.

### 3.2 Credit Card Reconciliation

Same procedure as bank reconciliation, but additionally:
- Verify all charges are business-related (per EC5, personal charges must be flagged).
- Match rewards/credits to the correct income or contra-expense account.
- Ensure statement closing date aligns with your reconciliation period.

### 3.3 Loan and Liability Reconciliation

- Compare book balance to lender statement.
- Verify interest expense matches lender's calculation.
- Ensure principal and interest portions of payments are correctly split.

---

## §4 Period-End Close

**Applies To:** Monthly, quarterly, and annual closing procedures. Implements TC8 (Temporal Authority), RC11 (Reconciliation Checkpoint), LE2 (Audit Trail Immutability).

### 4.1 Monthly Close Checklist

1. **Reconcile all accounts** — Bank, credit card, loans, intercompany (per §3). Period close blocked until reconciliation complete (per RC11).
2. **Review outstanding receivables** — Age analysis, collection follow-up, bad debt assessment.
3. **Review outstanding payables** — Verify all received bills are entered, early payment discounts captured.
4. **Post recurring entries** — Depreciation (per TC9), amortization, recurring accruals.
5. **Review classifications** — Scan recent transactions for misclassifications (per EC6). Correct with journal entries (per LE2, never edit-in-place).
6. **Run trial balance** — Verify debits = credits across all accounts.
7. **Generate financial statements** — P&L, Balance Sheet. Compare to prior period for reasonableness.
8. **Close period** — Mark the period as closed to prevent future posting without authorization (per TC8).

### 4.2 Depreciation Posting

Each period, post depreciation expense for all depreciable assets:
1. Debit: Depreciation Expense. Credit: Accumulated Depreciation.
2. Use the correct depreciation method and schedule per TC9.
3. Pro-rate for partial periods (assets placed in service mid-period).
4. Maintain the depreciation schedule as a supporting document.

### 4.3 Accrual Adjustments (Accrual Basis Only)

For accrual-basis entities, post adjusting entries for:
- **Accrued revenue** — Revenue earned but not yet billed.
- **Accrued expenses** — Expenses incurred but not yet billed (e.g., utilities, interest).
- **Prepaid expenses** — Amortize prepaid items (insurance, rent) to expense.
- **Unearned revenue** — Recognize the earned portion of advance payments.

---

## §5 Year-End Processes

**Applies To:** Annual closing, tax preparation support, information return generation. Implements TC8 (Temporal Authority), TC10 (Regulatory Compliance Boundary), RC12 (Record Retention & Audit Readiness).

### 5.1 Year-End Close Procedure

1. Complete all monthly closes for the year (per §4).
2. **Final depreciation** — Post the last period's depreciation and verify annual totals match the depreciation schedule.
3. **Inventory adjustments** — If applicable, adjust for physical count vs. book value.
4. **Closing entries** — Close revenue and expense accounts to Retained Earnings (corporations) or Owner's Equity (sole proprietors, partnerships).
5. **Run annual financial statements** — Full P&L, Balance Sheet, Cash Flow Statement. Compare to prior year.

### 5.2 Tax Preparation Support

Per TC10, AI performs preparation (computing from recorded data), not advice (strategy or interpretation).

**Permitted preparation activities:**
- Summarize revenue and expenses by tax category.
- Compute depreciation per published IRS schedules.
- Identify deductions with supporting documentation.
- Generate draft tax worksheets for professional review.
- Flag transactions that need professional judgment (mixed-use assets, home office, vehicle).

**Prohibited advice activities:**
- Recommending entity elections or changes.
- Suggesting tax strategies (income timing, retirement contribution optimization).
- Interpreting ambiguous tax situations.
- Taking positions on aggressive deductions.

### 5.3 1099 Generation

1. **Identify reportable vendors** — Vendors paid ≥$600 in the tax year for services (1099-NEC), rent (1099-MISC), or other reportable categories.
2. **Verify vendor information** — Name, address, TIN/SSN on W-9. Flag vendors missing W-9 forms.
3. **Generate 1099 forms** — Present drafts for review. Filing deadline: January 31 (1099-NEC).
4. **Record filing** — Track that forms were filed and copies sent to vendors.

### 5.4 IRS Record Retention Periods

Per RC12, retain records for the applicable period:

| Scenario | Retention Period |
|----------|-----------------|
| Standard income tax return | 3 years from filing date |
| Income understatement >25% | 6 years from filing date |
| Employment tax records | 4 years after tax due date |
| General business records | 7 years (recommended safe harbor) |
| Property/asset records | Until disposition + 3 years (or 6 years if understatement risk) |
| Fraud or unfiled returns | Indefinite (no statute of limitations) |
| 1031 exchange records | Life of replacement property + disposition + applicable period |

**Default recommendation:** When uncertain, apply the 7-year safe harbor. For property records, retain indefinitely until disposition.

---

## §6 Real Estate & Property Procedures

**Applies To:** Rental property accounting, investment property management, real estate LLCs. Implements TC9 (Depreciation & Asset Lifecycle), EC5 (Entity & Fund Isolation), TC8 (Temporal Authority).

### 6.1 Property-Level Tracking

Each property should be tracked as its own profit center:
1. **Property record** — Address, acquisition date, cost basis (purchase price + closing costs + improvements), land allocation, building allocation.
2. **Land vs. building allocation** — Required for depreciation (land is never depreciable). Use appraisal or property tax assessment ratios as starting point; significant properties require independent appraisal.
3. **Per-property P&L** — Track income and expenses by property for management reporting and Schedule E preparation.
4. **Improvement tracking** — Capitalize improvements (new roof, HVAC, appliances >$2,500) as separate depreciable assets. Repairs and maintenance (fixing a leak, patching drywall) are current-year expenses.

### 6.2 Depreciation Schedules

**Residential rental property:**
- Depreciable life: 27.5 years (MACRS, straight-line).
- Placed in service: the date the property is available for rent (not the purchase date, if renovation is needed).
- Mid-month convention: depreciation starts mid-month of the placed-in-service month.

**Commercial property:**
- Depreciable life: 39 years (MACRS, straight-line).
- Same mid-month convention.

**Land improvements:**
- Depreciable life: 15 years (fencing, landscaping, paving, drainage).
- 200% declining balance method.

**Personal property in rental:**
- Appliances, carpeting, furniture: 5-7 years depending on asset class.
- 200% declining balance method.

**Cost segregation:**
- Engineering study that reclassifies building components (electrical, plumbing, cabinetry) from 27.5/39 years to 5/7/15 years for accelerated depreciation.
- Economically beneficial for properties >$1M acquisition cost (general guideline — actual benefit depends on specific property).
- Requires professional cost segregation study — AI should flag the opportunity, not perform the study.

### 6.3 Security Deposits & Escrow

Per EC5, security deposits and escrow funds must be segregated:

1. **Separate bank account** — 22 states require a separate bank account for security deposits. Even where not legally required, best practice is separation.
2. **Liability recording** — Security deposits are liabilities (you owe them back to the tenant). Debit: Cash (security deposit bank account). Credit: Security Deposits Held (liability).
3. **Interest requirements** — Some jurisdictions require interest payment on security deposits. Track and accrue as required.
4. **Disposition** — When tenant moves out: if returning deposit, reverse the liability entry. If retaining for damages, reclassify from liability to income with documentation of the damages.
5. **Never commingled** — Security deposits must never be used for operating expenses. Per EC5, this is a legal violation in most jurisdictions, not just a best practice.

### 6.4 Like-Kind Exchanges (§1031)

1031 exchanges allow deferral of capital gains tax when exchanging like-kind investment properties.

**Basis carryforward rule (per TC9):**
1. The replacement property's depreciable basis is NOT its fair market value — it carries forward the relinquished property's adjusted basis.
2. If boot is received (cash or unlike property), that portion is taxable.
3. The replacement property may have two depreciation schedules: (a) carryforward basis continuing the old schedule, (b) any additional basis from boot paid, starting a new schedule.

**AI's role:**
- Record the exchange transactions with correct basis carryforward.
- Maintain documentation linking the relinquished and replacement properties.
- Flag 1031 exchanges for professional review (per TC10 — the tax implications require professional judgment).
- Track identification and closing deadlines (45-day identification, 180-day closing).

**AI must NOT:**
- Advise whether to do a 1031 exchange (this is tax advice per TC10).
- Determine boot calculation or tax treatment without professional review.
- Set up a 1031 exchange structure (qualified intermediary selection, etc.).

### 6.5 Rent Roll and Income Tracking

1. **Tenant ledger** — Track each tenant's lease terms, rent amount, payment history, security deposit.
2. **Rent recognition** — Per TC8:
   - Cash basis: recognize when received.
   - Accrual basis: recognize when due per lease terms.
   - Advance rent: always current-period income for tax purposes, regardless of lease period covered.
3. **Late fees and other income** — Track separately from rent for reporting purposes.
4. **Vacancy tracking** — Track vacancy dates and lost revenue for management reporting.

---

## §7 AI Interaction Patterns

**Applies To:** All AI-assisted accounting activities. Defines how the AI should interact with financial data and humans. Implements EC7 (Materiality-Gated Review), TC10 (Regulatory Compliance Boundary), LE4 (Computational Integrity).

### 7.1 Three-Tier Approval Model

| Tier | Actions | AI Authority | Human Role |
|------|---------|-------------|------------|
| **Always Human** | Journal entries, voids, deletes, period close, entity changes, transactions above materiality threshold, correcting entries, year-end close, 1099 filing | Draft and present | Approve and execute |
| **Configurable** | Categorization of known patterns, recurring transactions, bank feed matching for high-confidence matches, standard report generation | Execute with undo window | Review periodically; adjust rules |
| **Auto-Execute** | Read operations, balance queries, account lookups, report viewing, reconciliation matching proposals | Execute immediately | No review needed |

### 7.2 Draft-First Write Pattern

For any write operation to a financial system (creating invoices, recording bills, posting entries):

1. **Draft** — Create the transaction in draft/preview state.
2. **Validate** — Verify balance (LE1), classification (EC6), entity (EC5), period (TC8).
3. **Present** — Show the draft to the human with all relevant details.
4. **Confirm** — Wait for explicit human confirmation before posting.
5. **Post** — Execute the write operation.
6. **Verify** — Confirm the post succeeded and the resulting balances are correct.

### 7.3 Classification Confidence Thresholds

| Evidence Available | Confidence Level | AI Action |
|-------------------|-----------------|-----------|
| Vendor name + memo + amount pattern + account history | High | Auto-categorize (Configurable tier) |
| Vendor name + one corroborating signal (memo OR amount pattern) | Medium | Auto-categorize with flag for periodic review |
| Vendor name only | Low | Route to human review |
| New vendor, no history | Very Low | Always route to human review |

### 7.4 Deterministic Compute Pattern

When performing financial calculations, prefer deterministic computation over LLM reasoning:

**Recommended approach:**
- Use Python code execution (pandas, openpyxl, decimal module) for all financial arithmetic.
- Claude's Python code execution produces deterministic results — the risk is logic errors in the code, not arithmetic errors.
- Governance focus: validate the formula and data types, not the computation itself.

**What to validate:**
- Are `Decimal` types used for currency values (not `float`)?
- Is the formula correct for the business context?
- Are rounding rules applied consistently?
- Do intermediate results make business sense?

**Anti-patterns:**
- Asking the LLM to "calculate" a financial total in natural language.
- Using training-data knowledge for tax rates, depreciation schedules, or other values that should come from authoritative sources.
- Accepting a computed result without verifying the formula.

### 7.5 Financial Disclaimers

When presenting financial computations, include context:

- **Tax computations:** "This is a draft computation for professional review. The taxpayer bears full liability for positions taken on tax returns. Consult a qualified tax professional before filing."
- **Projections:** "This projection is based on [stated assumptions]. Actual results may differ. This is not financial advice."
- **Year-end summaries:** "This summary is prepared from the recorded transactions and may not reflect all adjustments. Review with your accountant or tax preparer."

---

## Appendix A: QuickBooks Online Integration

**Importance: 🔵 REFERENCE — For projects integrating with QuickBooks Online**

**Applies To:** AI agents interacting with QuickBooks Online via MCP server or API. Implements all accounting domain principles in the QBO-specific context.

**Information Currency:** Verified 2026-05-14 against intuit/quickbooks-online-mcp-server (v1.x, Apache-2.0). Verify current API behavior at the source — QBO API evolves independently.

### A.1 QBO MCP Server Overview

**Source:** [intuit/quickbooks-online-mcp-server](https://github.com/intuit/quickbooks-online-mcp-server) (213 stars, Apache-2.0)

The official Intuit MCP server provides 144 tools covering 29 entities and 11 reports. It gives AI agents direct access to QBO data and operations.

**Key capabilities:**
- CRUD operations on invoices, bills, payments, journal entries, customers, vendors, accounts
- Report generation: P&L, Balance Sheet, Trial Balance, A/R Aging, A/P Aging, Cash Flow, General Ledger
- Account and entity management
- Search and query across all entity types

### A.2 QBO API Characteristics

**Rate limits:**
- 500 requests per minute per realm (company)
- 10 concurrent requests maximum
- Throttling returns HTTP 429 — implement exponential backoff

**Write semantics (critical for LE2):**
- QBO has **no PUT/PATCH** — all updates are full-object POST.
- Every write operation requires the current `SyncToken` for optimistic concurrency.
- A stale SyncToken produces a validation error, not a silent overwrite.
- This full-POST model means AI can inadvertently overwrite fields it didn't intend to change if it doesn't preserve the full object.

**Idempotency pattern:**
1. **Search before create** — Before creating any entity, search for existing matches to prevent duplicates.
2. **RequestID header** — Use unique request IDs for write operations to prevent duplicate submissions on retry.
3. **SyncToken validation** — Always read the current entity, verify SyncToken, then write. Never cache SyncTokens.

**Data synchronization:**
- **Change Data Capture (CDC)** — Poll for changes since a timestamp. Use for batch sync operations.
- **Webhooks** — Real-time notifications of changes. Use for event-driven sync.
- **Recommended:** CDC for initial sync and catch-up; webhooks for ongoing real-time updates.

### A.3 QBO-Specific Gotchas

**Closed books (TC8 risk):**
- QBO allows closing the books with a password. However, the closed-books status is **not detectable via API**.
- Workaround: attempt to post to the closed period — the API will return an error. Handle this gracefully.
- Governance implication: the AI cannot proactively check if a period is closed; it must handle the error case.

**Tags (read-only via API):**
- QBO tags are visible via API but **cannot be created or modified via API**.
- Use Classes (requires Plus plan) or custom fields for categorization that needs API writability.

**Custom fields:**
- Limited to 3 string-type custom fields.
- Requires QBO Advanced plan.
- Not available on Simple Start or Essentials plans.

**Bank feeds:**
- Bank feed transactions are **not accessible via API**.
- Bank feed matching happens only in the QBO UI.
- Workaround: use CDC to detect when bank feed transactions are matched/recorded.

**Multi-entity (per EC5):**
- Each LLC or legal entity requires a **separate QBO subscription**.
- There is no multi-company view in QBO (that's QuickBooks Desktop Enterprise).
- Intercompany transactions require journal entries in each entity's separate QBO instance.

**Plan tier requirements:**
- **Simple Start:** Basic invoicing, expenses, reports.
- **Essentials:** Bills, multiple users, time tracking.
- **Plus:** Classes, locations, inventory, purchase orders, budgets.
- **Advanced:** Custom fields, custom reports, batch transactions, workflows.

### A.4 OAuth and Authentication

- QBO API uses OAuth 2.0 with authorization code flow.
- Access tokens expire after 1 hour; refresh tokens after 100 days.
- The MCP server handles token refresh, but monitor for refresh token expiration (requires re-authorization).
- Store credentials securely — never in source code, environment variables preferred, secrets manager recommended.

### A.5 Sandbox Testing

- Intuit provides a sandbox environment with test data for development.
- Always test API integrations in sandbox before connecting to production.
- Sandbox has the same API behavior as production but with fake data.
- Create sandbox apps at [developer.intuit.com](https://developer.intuit.com).

### A.6 Governance Mapping for QBO Operations

| QBO Operation | Approval Tier | Governing Principle |
|---------------|---------------|---------------------|
| Read/query any entity | Auto-Execute | — |
| Run reports | Auto-Execute | — |
| Create/update invoice | Configurable | LE1, EC6, TC8 |
| Create/update bill | Configurable | LE1, EC6, TC8 |
| Record payment | Configurable | LE1, EC5 |
| Create journal entry | Always Human | LE1, LE2, EC7 |
| Void transaction | Always Human | LE2, EC7 |
| Delete transaction | Always Human | LE2, EC7 |
| Modify closed period | Always Human | TC8, EC7 |
| Create/modify account (COA) | Always Human | EC6, EC7 |

---

## Appendix B: Domain Tools & Platform Integrations

**Importance: 🟢 OPTIONAL — Reference catalog for project-level tool selection**

This appendix catalogs the accounting tool ecosystem for AI-assisted accounting projects. Each entry includes governance-relevant metadata. This is a reference catalog — tool selection is project-specific, not domain-mandated.

Structural pattern: follows the domain-tools → CFR appendices pattern per BACKLOG #10. Mirrors Appendix A in the AI-Coding CFR (meta-level tools) and Appendix A in the UI/UX CFR (design tools). This appendix covers domain-level accounting tools.

**Information Currency:** All entries verified 2026-05-14. Entries >90 days since verification should be re-verified per C-109 domain-tool Information Currency check.

---

### B.1 Ledger Engines

Open-source double-entry accounting engines that can serve as backends for AI-assisted bookkeeping.

| Tool | Stars | License | Language | Capability | Governance Notes |
|------|-------|---------|----------|------------|------------------|
| **beancount/beancount** | 5,600 | GPL-2.0 | Python | Plain-text double-entry accounting. Two MCP servers available for AI integration. | Strong audit trail (text files in git). GPL-2.0 requires derivative distribution under GPL. |
| **arrobalytics/django-ledger** | 1,300 | GPL-3.0 | Python/Django | Django ORM-based double-entry engine. More mature API than python-accounting. | Good for Django-based projects. GPL-3.0 copyleft. |
| **ekmungai/python-accounting** | 197 | MIT | Python | GAAP+IFRS compliant double-entry engine. Supports multiple currencies. | MIT license — most permissive. Smaller community. |
| **datasignstech/pyluca** | — | MIT | Python | Minimal headless ledger module. | Lightweight. Suitable for embedding in larger systems. |

### B.2 Full-Stack Accounting Platforms

Complete accounting platforms with UI, API, and reporting.

| Tool | Stars | License | Capability | Governance Notes |
|------|-------|---------|------------|------------------|
| **bigcapitalhq/bigcapital** | 3,600 | AGPL-3.0 | Headless API-first accounting platform. SMB-focused. REST API for AI integration. | Most mature OSS accounting platform. AGPL-3.0 requires source disclosure for network use. |
| **frappe/erpnext** | — | GPL-3.0 | Comprehensive ERP including full accounting module. Chart of accounts, invoicing, reporting, inventory. | Reference implementation for enterprise accounting patterns. Heavy for accounting-only use. |

### B.3 AI Agent Layers

AI-native accounting tools and agent frameworks.

| Tool | Stars | License | Capability | Governance Notes |
|------|-------|---------|------------|------------------|
| **anthropics/financial-services** | 22,400 | Apache-2.0 | 11 financial agents: GL Reconciler, Month-End Closer, Statement Auditor, Valuation Reviewer, and more. Official Anthropic project. | Reference implementation for AI financial agents. Patterns for approval gates, audit trails, human-in-the-loop. |
| **MikeChongCan/cfo-stack** | 36 | MIT | AI CFO built on Beancount + Claude Code. Small business targeting. | Demonstrates beancount + AI integration pattern. |
| **vas3k/TaxHacker** | 5,600 | MIT | Self-hosted LLM-powered receipt and invoice processing. OCR + classification. | Useful pattern for document intake automation. |

### B.4 Knowledge Bases

Accounting knowledge resources for AI agent reference.

| Tool | Stars | License | Capability | Governance Notes |
|------|-------|---------|------------|------------------|
| **openaccountants/openaccountants** | 63 | AGPL-3.0 | 371 tax skills covering 134 countries. 8 countries have complete workflows; remainder are stubs. | **Quality caveat:** Most skills are Q3 (AI-drafted with citations), not CPA-verified. "CPA-verified" claims in documentation are inaccurate. AGPL-3.0. |
| **openaccountant/skills** | 13 | MIT | 44 operational accounting skills focused on practical bookkeeping procedures. | Smaller but higher-quality per skill. MIT license. |

### B.5 Platform Connectors

Tools for connecting AI agents to accounting platforms.

| Tool | Stars | License | Capability | Governance Notes |
|------|-------|---------|------------|------------------|
| **intuit/quickbooks-online-mcp-server** | 213 | Apache-2.0 | Official Intuit MCP server. 144 tools, 29 entities, 11 reports. | See Appendix A for detailed integration guidance. |
| **ej2/python-quickbooks** | 462 | MIT | Most-starred Python QBO SDK. Full API coverage. | For Python-based QBO integrations outside MCP. |

### B.6 Claude Platform Capabilities

Anthropic platform features relevant to accounting workflows.

**Claude for Small Business (Cowork):**
- Launched 2026-05-13 via Anthropic's Cowork product.
- 15 predefined skills across 7 apps, including payroll planning, monthly close, cash flow analysis, tax prep workflows.
- Includes built-in approval gates for financial actions.
- **Availability:** Claude.ai / Cowork only — not available in Claude Code or via API.
- **Governance note:** Consumer-grade financial assistance. Our governance MCP provides the compliance/oversight layer it lacks — principle-based guardrails, audit trails, and structured approval workflows.

**Claude for Excel (Add-in):**
- GA January 2026. Reads and modifies Excel workbooks, preserves formula dependencies.
- Anthropic warns: not recommended for audit-critical calculations without verification.
- Useful for financial report formatting and data extraction, not for authoritative financial computation.

**Python Code Execution:**
- Available in Claude.ai (analysis tool) and Claude Code (natively).
- Deterministic financial compute via pandas, openpyxl, decimal module.
- 83% accuracy on Financial Modeling World Cup tasks (Anthropic benchmark).
- See §7.4 (Deterministic Compute Pattern) for governance guidance.

### B.7 Architecture References

Repositories useful as design references, not production dependencies.

| Tool | Stars | License | Notes |
|------|-------|---------|-------|
| **panaversity/accounts_ai** | 9 | — | Spec document only (2 commits). Useful as AI accounting system design reference. |
| **heysarver/double-entry-accounting** | — | — | Minimal 2-table schema reference for double-entry implementation. |

---

## Changelog

### v1.0.0 (Current)
- Initial release: 7 method sections + 2 appendices
- §1 Business Setup Sequence (entity config, COA by business size, bank accounts, tax config)
- §2 Transaction Recording (sales, purchases, payments, journal entries, payroll)
- §3 Reconciliation Workflow (bank, credit card, loan reconciliation)
- §4 Period-End Close (monthly checklist, depreciation posting, accrual adjustments)
- §5 Year-End Processes (close procedure, tax prep support, 1099 generation, IRS retention periods)
- §6 Real Estate & Property Procedures (property tracking, depreciation schedules, security deposits, 1031 exchanges, rent rolls)
- §7 AI Interaction Patterns (three-tier approval, draft-first writes, classification confidence, deterministic compute, disclaimers)
- Appendix A: QuickBooks Online Integration (MCP server, API characteristics, gotchas, OAuth, sandbox, governance mapping)
- Appendix B: Domain Tools & Platform Integrations (ledger engines, platforms, AI agents, knowledge bases, connectors, Claude capabilities, architecture references)

---

*Version 1.0.0*
*Companion to: Accounting Domain Principles v1.0.0*
