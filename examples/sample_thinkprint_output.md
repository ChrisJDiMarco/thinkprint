# Thinkprint

_Generated 2026-04-20 22:44 UTC · 20 rules across 5 topics_

> **What this is:** behavioral rules extracted from your AI chat history and config files.
> Tier 1 = explicit (from your CLAUDE.md, .cursorrules etc). Tier 2 = inferred from chat patterns.

---

## Checklist

### Always check for SQL injection vulnerabilities
*Topic: `checklist` · Tier 1 · Confidence: high*

**Evidence:**
- `claude_agent`: Always check for SQL injection vulnerabilities

### Always verify error handling is comprehensive
*Topic: `checklist` · Tier 1 · Confidence: high*

**Evidence:**
- `claude_agent`: Always verify error handling is comprehensive

### Never approve code with hardcoded secrets
*Topic: `checklist` · Tier 1 · Confidence: high*

**Evidence:**
- `claude_agent`: Never approve code with hardcoded secrets

### Prefer parameterized queries in all database code
*Topic: `checklist` · Tier 1 · Confidence: high*

**Evidence:**
- `claude_agent`: Prefer parameterized queries in all database code


## Code Standards

### Always write tests first (TDD)
*Topic: `code_standards` · Tier 1 · Confidence: high*

**Evidence:**
- `claude_md`: Always write tests first (TDD)

### Keep files under 800 lines
*Topic: `code_standards` · Tier 1 · Confidence: high*

**Evidence:**
- `claude_md`: Keep files under 800 lines

### Prefer immutable data structures
*Topic: `code_standards` · Tier 1 · Confidence: high*

**Evidence:**
- `claude_md`: Prefer immutable data structures

### Use early returns over nested conditionals
*Topic: `code_standards` · Tier 1 · Confidence: high*

**Evidence:**
- `claude_md`: Use early returns over nested conditionals


## Communication Style

### Always be terse and direct
*Topic: `communication_style` · Tier 1 · Confidence: high*

**Evidence:**
- `claude_md`: Always be terse and direct

### Avoid emojis unless requested
*Topic: `communication_style` · Tier 1 · Confidence: high*

**Evidence:**
- `claude_md`: Avoid emojis unless requested

### Never use trailing summaries
*Topic: `communication_style` · Tier 1 · Confidence: high*

**Evidence:**
- `claude_md`: Never use trailing summaries

### Prefer plain text over bullet points for conversational responses
*Topic: `communication_style` · Tier 1 · Confidence: high*

**Evidence:**
- `claude_md`: Prefer plain text over bullet points for conversational responses


## Cursor

### Always validate API inputs with zod
*Topic: `cursor` · Tier 1 · Confidence: high*

**Evidence:**
- `cursor_rules`: Always validate API inputs with zod

### Never mutate props
*Topic: `cursor` · Tier 1 · Confidence: high*

**Evidence:**
- `cursor_rules`: Never mutate props

### Prefer functional React components
*Topic: `cursor` · Tier 1 · Confidence: high*

**Evidence:**
- `cursor_rules`: Prefer functional React components

### Use TypeScript strict mode
*Topic: `cursor` · Tier 1 · Confidence: high*

**Evidence:**
- `cursor_rules`: Use TypeScript strict mode


## Process

### Always create a PR with test plan
*Topic: `process` · Tier 1 · Confidence: high*

**Evidence:**
- `claude_command`: Always create a PR with test plan

### Keep commit messages short and plain
*Topic: `process` · Tier 1 · Confidence: high*

**Evidence:**
- `claude_command`: Keep commit messages short and plain

### Never push to main branch directly
*Topic: `process` · Tier 1 · Confidence: high*

**Evidence:**
- `claude_command`: Never push to main branch directly

### Run full test suite before shipping
*Topic: `process` · Tier 1 · Confidence: high*

**Evidence:**
- `claude_command`: Run full test suite before shipping
