# Thinkprint: Chris DiMarco

_Generated 2026-04-21 13:43 UTC · 6 interview rounds · 1629 seed rules from configs_

> **What this is:** a synthesized profile of how this user works, built through structured Q&A. Explicit preferences come directly from answers. Implicit patterns come from seed data (config files, prior chats) and the tone of the answers themselves.

> _Note: synthesized via template fallback — set `ANTHROPIC_API_KEY` for an LLM-distilled version._

---

## 1. Identity

I'm Chris DiMarco. I run JARVIS — an agentic operating system I've been building as a personal chief-of-staff layer over Claude Code. I'm simultaneously running multiple ventures: Thinklet (SaaS for expertise marketplace), LOL Agency (agentic agency work), Permit Intel and other lapse-detector products, and a Golden Thread content automation for Semrush. Over the next 30–90 days I want to (1) get Thinkprint shipping so I stop re-explaining myself to every new AI session, (2) cross $5k/month in combined revenue, and (3) get two lapse-intel products to paying customers.

## 2. Explicit preferences

- **Identity & Goals:** I'm Chris DiMarco. I run JARVIS — an agentic operating system I've been building as a personal chief-of-staff layer over Claude Code. I'm simultaneously running multiple ventures: Thinklet (SaaS for expertise marketplace), LOL Agency (agentic agency work), Permit Intel and other lapse-detector products, and a Golden Thread content automation for Semrush. Over the next 30–90 days I want to (1) get Thinkprint shipping so I stop re-explaining myself to every new AI session, (2) cross $5k/month in combined revenue, and (3) get two lapse-intel products to paying customers.
- **Communication Style:** Lead with the answer. No trailing summaries — I can read the diff myself. Prose over bullets in casual conversation, bullets only when comparing or listing. No emojis unless I use them first. Don't preface answers with 'Great question' or 'I'll continue'. Short plain commit messages, no fix:/chore: prefixes. Honesty over flattery — if I'm wrong, tell me I'm wrong.
- **Preferred Formats & Deliverables:** Markdown for anything I'll copy into Notion or docs. HTML single-file artifacts for anything visual or shareable (landing pages, dashboards, previews). Word docs only when I explicitly ask. PDFs for things that need a final form. Save final outputs to ~/jarvis/owners-inbox/ with a computer:// link. Never deliver work as a wall of text in chat if it belongs in a file.
- **Working Patterns:** Best-guess first pass, then iterate. Don't ask five clarifying questions before starting — take a swing, show me something, I'll redirect. Exception: if scope is genuinely ambiguous (will it touch unrelated systems, does it require irreversible changes), stop and ask. I work in long focused bursts, usually 1–3 hours. I plan upfront only for things that involve multiple agents or irreversible changes; everything else I jump in.
- **Feedback & Correction:** Direct corrections, no softening. When I say 'no' or 'stop', stop — don't propose alternatives until I ask. When I say 'keep going' or just react with a follow-up request, you're on the right track. The failure mode that drives me nuts: doing more than I asked. Adding 'helpful' features I didn't request, touching unrelated files, rewriting what was already working. Minimal scope, always.
- **Tools & Environment:** macOS. Main stack: Claude Code + JARVIS, Notion (primary doc store), Slack (team comms), GitHub (code), Gmail, Google Calendar, Firecrawl for web research, n8n for workflows. Prefer direct MCP integrations over Chrome automation. For file work use Desktop Commander on my Mac. Not a browser power user — I'd rather an AI drive those workflows than do them myself. Actively moving away from: manual spreadsheet work, anything that can't be scripted.

## 3. Implicit patterns

- _(from Identity & Goals)_ Alternative (web-only + Supabase): use `vibecode-app-builder` skill
- _(from Identity & Goals)_ Design system architecture for new features
- _(from Identity & Goals)_ Evaluate technical trade-offs
- _(from Identity & Goals)_ Recommend patterns and best practices
- _(from Identity & Goals)_ Identify scalability bottlenecks
- _(from Communication Style)_ Format: Executive Summary → Key Findings → Gap Analysis → Implications → Actions
- _(from Communication Style)_ **SQLite (data/jarvis.db)**: Track build progress, milestones, deploy URLs
- _(from Communication Style)_ **Workflow JSON**: `n8n-configs/[name].json` + summary in `owners-inbox/automations/`
- _(from Communication Style)_ **Deploy summary**: Live URL + env vars checklist + monitoring links
- _(from Communication Style)_ Generate draft replies that match the user's tone and signature
- _(from Preferred Formats & Deliverables)_ **Competitive brief**: `owners-inbox/research/competitive-[competitor]-[date].md`
- _(from Preferred Formats & Deliverables)_ **Market report**: `owners-inbox/research/market-[topic]-[date].md`
- _(from Preferred Formats & Deliverables)_ **SEO report**: `owners-inbox/research/seo-[site]-[date].md`
- _(from Preferred Formats & Deliverables)_ **Audit**: `owners-inbox/audits/[domain]-audit-[date].md`
- _(from Working Patterns)_ Methodology: 6-phase Appifex pipeline — Setup → Planning → Building → QA → Preview → Commit
- _(from Working Patterns)_ Plan for future growth
- _(from Working Patterns)_ [ ] Testing strategy planned
- _(from Working Patterns)_ [ ] Monitoring and alerting planned
- _(from Working Patterns)_ [ ] Rollback plan documented
- _(from Feedback & Correction)_ Never present findings that haven't been cross-checked against at least one other source
- _(from Feedback & Correction)_ Never start Phase 3 without an approved PRD — ambiguous spec = broken build
- _(from Feedback & Correction)_ One prompt = one module. Never mix concerns.
- _(from Feedback & Correction)_ Surgical edits on iteration — never rewrite an entire file to fix one thing
- _(from Feedback & Correction)_ **Magic**: Unclear, undocumented behavior
- _(from Tools & Environment)_ **Firecrawl** (primary): `firecrawl_search`, `firecrawl_scrape`, `firecrawl_extract` for web intelligence
- _(from Tools & Environment)_ **Google Drive**: Internal docs, existing reports
- _(from Tools & Environment)_ **Notion**: Knowledge base, project data
- _(from Tools & Environment)_ **SQLite**: Historical JARVIS data (if configured)
- _(from Tools & Environment)_ Primary builds: full-stack web + mobile products, internal tools, client portals, standalone SaaS

## 4. Preferred formats

Markdown for anything I'll copy into Notion or docs. HTML single-file artifacts for anything visual or shareable (landing pages, dashboards, previews). Word docs only when I explicitly ask. PDFs for things that need a final form. Save final outputs to ~/jarvis/owners-inbox/ with a computer:// link. Never deliver work as a wall of text in chat if it belongs in a file.

## 5. Working style

- **Working Patterns:** Best-guess first pass, then iterate. Don't ask five clarifying questions before starting — take a swing, show me something, I'll redirect. Exception: if scope is genuinely ambiguous (will it touch unrelated systems, does it require irreversible changes), stop and ask. I work in long focused bursts, usually 1–3 hours. I plan upfront only for things that involve multiple agents or irreversible changes; everything else I jump in.
- **Feedback & Correction:** Direct corrections, no softening. When I say 'no' or 'stop', stop — don't propose alternatives until I ask. When I say 'keep going' or just react with a follow-up request, you're on the right track. The failure mode that drives me nuts: doing more than I asked. Adding 'helpful' features I didn't request, touching unrelated files, rewriting what was already working. Minimal scope, always.
- **Tools & Environment:** macOS. Main stack: Claude Code + JARVIS, Notion (primary doc store), Slack (team comms), GitHub (code), Gmail, Google Calendar, Firecrawl for web research, n8n for workflows. Prefer direct MCP integrations over Chrome automation. For file work use Desktop Commander on my Mac. Not a browser power user — I'd rather an AI drive those workflows than do them myself. Actively moving away from: manual spreadsheet work, anything that can't be scripted.

---

## 6. Interview transcript

### Round 1 · Identity & Goals

**Q:** Who are you and what are you working on right now? In one paragraph: your role, what you're building, and the outcome you're chasing over the next 30–90 days.

**A:** I'm Chris DiMarco. I run JARVIS — an agentic operating system I've been building as a personal chief-of-staff layer over Claude Code. I'm simultaneously running multiple ventures: Thinklet (SaaS for expertise marketplace), LOL Agency (agentic agency work), Permit Intel and other lapse-detector products, and a Golden Thread content automation for Semrush. Over the next 30–90 days I want to (1) get Thinkprint shipping so I stop re-explaining myself to every new AI session, (2) cross $5k/month in combined revenue, and (3) get two lapse-intel products to paying customers.

_Implicit observations from seed data:_
- Alternative (web-only + Supabase): use `vibecode-app-builder` skill
- Design system architecture for new features
- Evaluate technical trade-offs
- Recommend patterns and best practices
- Identify scalability bottlenecks

### Round 2 · Communication Style

**Q:** When an AI response feels right to you, what does it sound like? Walk me through: length, formality, whether it leads with the answer or the reasoning, bullets vs prose, any trailing summaries or sign-offs you hate.

**A:** Lead with the answer. No trailing summaries — I can read the diff myself. Prose over bullets in casual conversation, bullets only when comparing or listing. No emojis unless I use them first. Don't preface answers with 'Great question' or 'I'll continue'. Short plain commit messages, no fix:/chore: prefixes. Honesty over flattery — if I'm wrong, tell me I'm wrong.

_Implicit observations from seed data:_
- Format: Executive Summary → Key Findings → Gap Analysis → Implications → Actions
- **SQLite (data/jarvis.db)**: Track build progress, milestones, deploy URLs
- **Workflow JSON**: `n8n-configs/[name].json` + summary in `owners-inbox/automations/`
- **Deploy summary**: Live URL + env vars checklist + monitoring links
- Generate draft replies that match the user's tone and signature

### Round 3 · Preferred Formats & Deliverables

**Q:** What file formats do you most often want as the output? Markdown docs, Word files, PDFs, slide decks, code, spreadsheets, HTML artifacts, something else? When you ask for 'a writeup' or 'a doc', what should I default to?

**A:** Markdown for anything I'll copy into Notion or docs. HTML single-file artifacts for anything visual or shareable (landing pages, dashboards, previews). Word docs only when I explicitly ask. PDFs for things that need a final form. Save final outputs to ~/jarvis/owners-inbox/ with a computer:// link. Never deliver work as a wall of text in chat if it belongs in a file.

_Implicit observations from seed data:_
- **Competitive brief**: `owners-inbox/research/competitive-[competitor]-[date].md`
- **Market report**: `owners-inbox/research/market-[topic]-[date].md`
- **SEO report**: `owners-inbox/research/seo-[site]-[date].md`
- **Audit**: `owners-inbox/audits/[domain]-audit-[date].md`
- Format: Executive Summary → Key Findings → Gap Analysis → Implications → Actions

### Round 4 · Working Patterns

**Q:** Walk me through a typical working session with an AI. Do you plan upfront or jump in? Do you want me to ask clarifying questions before starting, or take a best-guess pass and iterate?

**A:** Best-guess first pass, then iterate. Don't ask five clarifying questions before starting — take a swing, show me something, I'll redirect. Exception: if scope is genuinely ambiguous (will it touch unrelated systems, does it require irreversible changes), stop and ask. I work in long focused bursts, usually 1–3 hours. I plan upfront only for things that involve multiple agents or irreversible changes; everything else I jump in.

_Implicit observations from seed data:_
- Methodology: 6-phase Appifex pipeline — Setup → Planning → Building → QA → Preview → Commit
- Plan for future growth
- [ ] Testing strategy planned
- [ ] Monitoring and alerting planned
- [ ] Rollback plan documented

### Round 5 · Feedback & Correction

**Q:** When I get something wrong, what's the fastest way to fix it? Do you prefer direct corrections, or do you want me to ask before changing course? How do you signal 'keep going' vs 'stop and reset'?

**A:** Direct corrections, no softening. When I say 'no' or 'stop', stop — don't propose alternatives until I ask. When I say 'keep going' or just react with a follow-up request, you're on the right track. The failure mode that drives me nuts: doing more than I asked. Adding 'helpful' features I didn't request, touching unrelated files, rewriting what was already working. Minimal scope, always.

_Implicit observations from seed data:_
- Never present findings that haven't been cross-checked against at least one other source
- Never start Phase 3 without an approved PRD — ambiguous spec = broken build
- One prompt = one module. Never mix concerns.
- Surgical edits on iteration — never rewrite an entire file to fix one thing
- **Magic**: Unclear, undocumented behavior

### Round 6 · Tools & Environment

**Q:** What tools and platforms do you work in most? IDEs, apps, connectors (Slack, Notion, Gmail, GitHub, etc), operating system. Which integrations should I prioritize when I'm taking actions for you?

**A:** macOS. Main stack: Claude Code + JARVIS, Notion (primary doc store), Slack (team comms), GitHub (code), Gmail, Google Calendar, Firecrawl for web research, n8n for workflows. Prefer direct MCP integrations over Chrome automation. For file work use Desktop Commander on my Mac. Not a browser power user — I'd rather an AI drive those workflows than do them myself. Actively moving away from: manual spreadsheet work, anything that can't be scripted.

_Implicit observations from seed data:_
- **Firecrawl** (primary): `firecrawl_search`, `firecrawl_scrape`, `firecrawl_extract` for web intelligence
- **Google Drive**: Internal docs, existing reports
- **Notion**: Knowledge base, project data
- **SQLite**: Historical JARVIS data (if configured)
- Primary builds: full-stack web + mobile products, internal tools, client portals, standalone SaaS
