# Security Scan Procedure

## Phase 1: Secrets Detection

Scan the codebase for exposed secrets, credentials, and sensitive data.

### 1.1 High-Confidence Patterns

Run grep-based detection for common secret patterns. These regex patterns have high true-positive rates:

```bash
# AWS keys
grep -rn "AKIA[0-9A-Z]\{16\}" . --include="*.py" --include="*.js" --include="*.ts" --include="*.json" --include="*.yaml" --include="*.yml" --include="*.env*" --include="*.toml" --include="*.cfg" --include="*.ini"

# Generic API keys and tokens (high-confidence patterns)
grep -rn "sk-[a-zA-Z0-9]\{20,\}" . --include="*.py" --include="*.js" --include="*.ts" --include="*.json" --include="*.yaml" --include="*.yml" --include="*.env*"
grep -rn "sk_live_[a-zA-Z0-9]\{20,\}" . --include="*.py" --include="*.js" --include="*.ts"
grep -rn "ghp_[a-zA-Z0-9]\{36\}" . --include="*.py" --include="*.js" --include="*.ts"
grep -rn "gho_[a-zA-Z0-9]\{36\}" . --include="*.py" --include="*.js" --include="*.ts"

# Private keys
grep -rn "BEGIN.*PRIVATE KEY" . --include="*.pem" --include="*.key" --include="*.py" --include="*.js" --include="*.ts" --include="*.env*"

# Password assignments
grep -rn "password\s*=\s*[\"'][^\"']\+[\"']" . --include="*.py" --include="*.js" --include="*.ts" --include="*.yaml" --include="*.yml" --include="*.json" --include="*.env*"
```

**Exclude from scan:** `node_modules/`, `.git/`, `__pycache__/`, `dist/`, `build/`, `*.lock`, test fixtures with clearly fake values (e.g., `test_password = "fake123"`).

### 1.2 Configuration Files

Check common configuration files for exposed secrets:

- `.env`, `.env.local`, `.env.production` — should be in `.gitignore`
- `config.json`, `settings.json` — check for hardcoded credentials
- `docker-compose.yml` — check for inline passwords
- CI/CD files (`.github/workflows/*.yml`, `.gitlab-ci.yml`) — check for hardcoded secrets (should use repository secrets)

### 1.3 Git History (Quick Check)

```bash
# Check if .env files were ever committed
git log --all --diff-filter=A -- "*.env" "*.env.*" 2>/dev/null | head -5

# Check for recent secret additions in staged changes
git diff --cached -S "password" -S "secret" -S "api_key" -S "token" --stat 2>/dev/null
```

## Phase 2: Dependency Audit

Detect the package manager and run the appropriate audit tool.

### 2.1 Detect Package Manager

Check for the presence of these files (in order):

| File | Manager | Audit Command |
|------|---------|---------------|
| `package-lock.json` or `yarn.lock` | npm/yarn | `npm audit --json 2>/dev/null` or `yarn audit --json 2>/dev/null` |
| `requirements.txt` or `pyproject.toml` | pip | `pip-audit 2>/dev/null` or `safety check 2>/dev/null` |
| `Gemfile.lock` | bundler | `bundle audit check 2>/dev/null` |
| `go.sum` | go | `govulncheck ./... 2>/dev/null` |
| `Cargo.lock` | cargo | `cargo audit 2>/dev/null` |

### 2.2 Run Audit

Run the appropriate audit command. If the tool is not installed, note it as a finding:

```
**SEVERITY:** MEDIUM
**Location:** [package manifest file]
**Issue:** Dependency audit tool not available — cannot verify dependency security
**Fix:** Install [tool name]: `[install command]`
```

### 2.3 Interpret Results

For each vulnerable dependency found:
- Severity from the advisory (CRITICAL, HIGH, MEDIUM, LOW)
- Package name and version
- CVE or advisory identifier
- Whether a fix version is available
- Whether the package is a direct or transitive dependency

## Phase 3: Basic Auth Pattern Check

Review code for common authentication and authorization anti-patterns.

### 3.1 Hardcoded Credentials
- Default usernames/passwords in source code (not test fixtures)
- Admin credentials in seed files or migration scripts
- Service account credentials in application code

### 3.2 Authentication Gaps
- API endpoints that modify state but lack authentication middleware
- Routes or handlers without auth decorators/middleware when siblings have them
- Missing CSRF protection on state-changing endpoints

### 3.3 Session/Token Issues
- Session tokens in URLs or query parameters
- Missing token expiration
- Tokens stored in localStorage (XSS-vulnerable) instead of httpOnly cookies

## Output Format

Present findings grouped by phase, with severity gating:

```markdown
## Security Scan: [project name or path]

**Scanned:** [date]
**Phases:** Secrets Detection, Dependency Audit, Auth Patterns

### CRITICAL
- `file:line` — [Issue] → [Fix]
  ```
  [quoted code]
  ```

### HIGH
- `file:line` — [Issue] → [Fix]

### MEDIUM (Summary)
- [count] dependency vulnerabilities with available fixes
- [count] configuration recommendations

### LOW (Summary)
- [count] informational findings

### Clean Areas
- [What passed cleanly — e.g., "No secrets detected in source code", "All dependencies up to date"]
```

## When to Escalate

Stop and ask the user before proceeding when:
- **Cryptographic code** — custom encryption, key management, or certificate handling requires specialized review
- **High-confidence secret found** — if a real API key or credential is detected, alert the user immediately rather than continuing the scan
- **Regulatory compliance code** — HIPAA, PCI-DSS, SOX, or GDPR-related logic where incorrect assessment could have legal consequences
- **Uncertain findings** — you cannot determine whether a pattern is a genuine vulnerability or an intentional design choice

## Limitations

This scan covers mechanical, portable security concerns. It does NOT cover:
- Full OWASP Top 10 systematic review
- Attack surface mapping and threat modeling
- Data flow tracing (input → processing → storage → output)
- Business logic vulnerabilities
- Infrastructure security (network, firewall, IAM)

For comprehensive security analysis, perform a dedicated manual security review with project-specific context.
