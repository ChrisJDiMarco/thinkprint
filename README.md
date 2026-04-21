# Thinkprint

> **Your portable AI working profile.** A short Q&A interview, fused with implicit signals from your AI configs, produces a structured markdown profile your AI reads at session start. Stop re-explaining how you work every time you open a new chat.

A Thinkprint is a synthesized profile of how you work — built through a structured Q&A interview that fuses the **explicit** answers you give with **implicit** observations drawn from your configs and chat history. The finished profile lives in `thinkprint.md` and is served to any MCP-compatible client.

---

## Why this exists

Every major "AI memory" product today (Mem0, Letta, Zep) stores only what you **explicitly state**. Independent benchmarks put their *implicit* preference accuracy at **30–45%** because they don't infer behavior from interaction patterns. Pure config scrapers have the opposite problem: they capture behavior but miss goals, projects, and the why behind the rules.

Thinkprint sits in the middle. A ~15-minute Q&A interview asks six pointed questions (identity, communication, format, working patterns, feedback, tools). Before each question, the interviewer mines your `~/.claude/` configs and chat exports for implicit observations relevant to that topic and shows them to you. You confirm, correct, or override. The answers and observations are then synthesized — optionally with Claude — into a clean, topic-grouped profile.

**The wedge:** elicit preferences through structured Q&A, ground them in observed behavior, serve the result over MCP. Everything else (swipe UI, absorption loop, sanitizer) is Phase 2.

---

## What a Thinkprint looks like

`thinkprint.md` has six synthesized sections plus a full transcript:

1. **Identity** — who you are, what you're building, 30–90 day goals.
2. **Explicit preferences** — communication style, feedback style, working patterns *you stated*.
3. **Implicit patterns** — behaviors inferred from your configs and chats (e.g. "uses short plain commit messages, no `fix:` prefixes").
4. **Preferred formats** — markdown vs HTML vs docx vs PDF, save locations, delivery norms.
5. **Working style** — session length, planning cadence, when to ask vs. when to jump in.
6. **Interview transcript** — the raw Q&A for audit and re-synthesis.

See [`examples/sample_thinkprint.md`](examples/sample_thinkprint.md) for a real run.

---

## How it works

```
 ┌───────────────┐     ┌──────────────────┐     ┌────────────────────┐     ┌───────────┐
 │  Seed extract │ ──► │   Q&A interview  │ ──► │  Synthesize profile│ ──► │ MCP serve │
 │  (configs,    │     │  6 rounds,       │     │  (Claude or        │     │           │
 │   chat logs)  │     │  explicit +      │     │   template fallback)│    │           │
 │  = implicit   │     │  implicit shown  │     │                    │     │           │
 └───────────────┘     └──────────────────┘     └────────────────────┘     └───────────┘
```

1. **Seed extract (silent pre-step).** Parses `~/.claude/CLAUDE.md`, project CLAUDE.md, `~/.claude/agents/*.md`, `~/.claude/commands/*.md`, `.cursorrules`, `.windsurfrules`. Produces implicit observations only — never shipped as output on its own.
2. **Q&A interview.** Six questions covering the six dimensions. Each round shows relevant implicit observations before asking, so you can confirm or override.
3. **Synthesize.** With `ANTHROPIC_API_KEY`, Claude distills answers + observations into the six sections. Without it, a template fallback writes the sections directly from the transcript.
4. **Serve over MCP.** A FastMCP server exposes the profile as a resource plus `get_rules(topic)` and `list_thinkprint_topics()` tools.

---

## What's deliberately out of scope

Per the spec, the MVP ships only the interview → synthesis → MCP loop. The following are Phase 2:

- Next.js frontend / swipe review UI
- Nightly absorption loop — writeback signals from live MCP usage
- PII/trade-secret sanitizer for publishing profiles
- Cross-site integration with Thinklet
- Cognitive Signature / versioning
- Classifier-based injection detection (LLM Guard / Prompt Shield)

The wedge earns the right to build these.

---

## Install

```bash
git clone https://github.com/ChrisJDiMarco/thinkprint.git
cd thinkprint
pip install -e .
```

Requires Python 3.10+. For Claude-synthesized output set `ANTHROPIC_API_KEY`; without it, the template fallback still produces a valid profile.

---

## Quickstart

**1. Run the interview:**

```bash
# Interactive — prompts you through the 6 questions
thinkprint interview --claude-dir ~/.claude --project . --label "Thinkprint: Chris"

# Batch — non-interactive, answers loaded from JSON
thinkprint interview --answers examples/sample_answers.json
```

Outputs go to `./thinkprint.md`, with the raw transcript at `./.thinkprint/interview.json`.

**2. Inspect:**

```bash
cat thinkprint.md                        # the profile
thinkprint show                          # seed rules table (from extract step)
thinkprint show --topic "code"           # filter seed rules by topic
thinkprint topics                        # topic -> rule count
```

**3. Serve over MCP:**

```bash
thinkprint serve
```

Then in Claude Desktop `claude_desktop_config.json` (or Claude Code's MCP config), add:

```json
{
  "mcpServers": {
    "thinkprint": {
      "command": "thinkprint",
      "args": ["serve", "--db", "/absolute/path/to/.thinkprint/thinkprint.db"]
    }
  }
}
```

Restart the client. Your AI can now read the Thinkprint resource and call `get_rules(topic="writing")` at the start of any relevant conversation.

---

## Seed extraction (optional pre-step)

`thinkprint extract` runs only the config/chat-log extraction step. It's a way to seed the implicit-observation pool before an interview — or to audit what the interviewer will surface. It is **not** a finished Thinkprint.

```bash
# Configs only — no LLM
thinkprint extract --claude-dir ~/.claude --no-llm

# Full seed — configs + chat history, clustered and labeled with Claude
thinkprint extract \
  --claude-dir ~/.claude \
  --project . \
  --chatgpt-export ~/Downloads/chatgpt-export/conversations.json \
  --claude-export ~/Downloads/claude-export.json
```

---

## How to get your chat exports

- **ChatGPT:** Settings → Data Controls → Export data → email arrives with a zip → `conversations.json`.
- **Claude:** Settings → Privacy → Export your data → email arrives with a zip.
- **Cursor:** chat history lives locally in SQLite — Phase 2 will parse it directly; for now, not supported.

All parsing is local. The only text that leaves your machine is the cluster-scoped, truncated content sent to Anthropic for Tier 2 seed synthesis and Thinkprint synthesis — and only if you have `ANTHROPIC_API_KEY` set.

---

## Project layout

```
thinkprint/
├── src/thinkprint/
│   ├── models.py                 # Pydantic data models (Message, Rule, Evidence, ...)
│   ├── interview/
│   │   ├── questions.py          # the 6-round question bank
│   │   └── session.py            # interview runner + transcript models
│   ├── synthesis/
│   │   └── profile.py            # synthesize transcript + seeds → thinkprint.md
│   ├── extractors/
│   │   ├── config_files.py       # seed: CLAUDE.md, .cursorrules, ...
│   │   └── chat_exports.py       # seed: ChatGPT + Claude export parsers
│   ├── filter/
│   │   ├── noise.py              # drop greetings/acks/short msgs
│   │   └── injection.py          # layer-1 heuristic injection flagging
│   ├── archaeology/
│   │   ├── clusterer.py          # TF-IDF + KMeans topic clusters
│   │   ├── signals.py            # rephrase + acceptance signal detectors
│   │   └── synthesizer.py        # per-cluster Claude call → Rule objects
│   ├── storage.py                # SQLite persistence for seed rules
│   ├── output.py                 # markdown rendering for seed rules
│   ├── mcp_server.py             # FastMCP server
│   ├── pipeline.py               # seed extraction orchestration
│   └── cli.py                    # click-based CLI
├── tests/                        # pytest; runs without API key
├── examples/
│   ├── sample_answers.json       # batch-mode answer file
│   └── sample_thinkprint.md      # real output from the interview
└── pyproject.toml
```

---

## Tests

```bash
pip install -e ".[dev]"
pytest
```

All tests run without an API key — they cover the question bank, batch interview round-trip, synthesizer template fallback, extractors, filters, signal detection, clustering, and storage round-trips.

---

## Roadmap

**Phase 2** (earned once the wedge has ~50 users actively running MCP queries):

- Swipe UI for rule review and refinement (per spec: 20–30 min session with probe questions)
- Absorption loop — writeback signals from live MCP usage, nightly batch, LLM-recommends / user-decides diffs
- Sanitizer for publishing profiles publicly (PII + trade-secret sweeps)
- Classifier-based injection detection (LLM Guard or Microsoft Prompt Shield) replacing the current heuristic layer
- Cursor / Windsurf local SQLite parsers
- Cognitive Signature versioning and rollback

**Phase 3** (if Phase 2 works):

- Next.js frontend at thinkprint.io
- Cross-site integration with Thinklet
- Public profile publishing

---

## License

MIT — see [LICENSE](LICENSE).

---

## Contributing

Early and scrappy. Open an issue before opening a PR so we can scope it together. Tests must pass and new behavior needs a test.

Built by [@ChrisJDiMarco](https://github.com/ChrisJDiMarco).
