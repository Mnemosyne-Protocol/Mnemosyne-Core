# Secure_Repo_Bootstrap_Template

**Status:** Active  
**Owner:** Mnemosyne Labs  
**Scope:** New repositories, public open-core repositories, local-first development environments on M3  
**Operating Principle:** Fail-Closed by Default

---

## 1. Purpose

This template defines the minimum security and public-surface discipline required when bootstrapping any new Mnemosyne repository.

Its goals are:

- prevent accidental leakage of local-only workflow files
- block secrets before they enter Git history
- keep public repositories product-facing
- ensure local tooling remains local
- make repository hygiene enforceable at Git level, not only by memory

This template is the repository-level equivalent of a seatbelt:
small, always-on, and designed to prevent expensive mistakes.

---

## 2. Core Principle

A secure repository should not depend on:

- memory
- discipline alone
- “I will remember later”
- cleanup after exposure

Instead, it should begin from:

- strict ignore defaults
- automatic commit-time checks
- repeatable local setup
- CI-side mirror verification

**Rule:**  
Security should be present at repository creation, not added later.

---

## 3. Repository Bootstrap Components

Every new Mnemosyne repository should begin with:

- a strict `.gitignore`
- a local pre-commit guard
- a CI-side mirror check
- public-facing discipline files where appropriate:
  - `AGENTS.md`
  - `ARCHITECTURE.md`
  - `INVARIANTS.md`
  - `SECURITY.md`
  - `TESTING.md`

---

## 4. Strict `.gitignore` Baseline

The following block should be added to the root `.gitignore` of all new repositories.

```gitignore
# === Local-only Mnemosyne workflow ===
.claude/
.cursor/
.codex/
.zed/
.agents/

# Local overlays / personal notes
*_local.md
*_private.md
AGENT_LOCAL.md
TOOL_LOCAL.md
WORKING-CONTEXT.local.md

# Local Mnemosyne machine context
mnemosyne-local/
**/mnemosyne-local/

# Secrets / env
.env
.env.*
*.env
secrets/
private/
keys/
*.key
*.pem
*.p12
*.pfx
*.mobileprovision

# Local auth / tokens
.auth/
.tokens/
.credentials/
.aws/
.gcp/
.azure/

# OS/editor/log/temp noise
.DS_Store
Thumbs.db
*.log
*.tmp
*.temp
.cache/
dist-local/
build-local/

# Sensitive exports / scratchpads
scratch/
drafts-private/
exports-private/