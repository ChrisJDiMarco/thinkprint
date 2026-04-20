# Thinkprint

> **Your portable AI working profile.** Extract behavioral rules from your AI chat history and config files. Serve them to any AI client — Claude Code, Cursor, Claude Desktop — over MCP.

Thinkprint turns the preferences you've *actually* demonstrated in thousands of AI chats into a structured profile your AI can read at session start. Stop re-explaining how you work every time you open a new chat.

---

## Why this exists

Every major "AI memory" product today (Mem0, Letta, Zep) stores facts the user **explicitly states** — "I prefer TypeScript", "my company is X". Independent benchmarks put Mem0's *implicit* preference accuracy at **30–45%** because it doesn't infer behavior from interaction patterns.

Thinkprint starts from the other end: your chat history and your config files already contain the ground truth of how you work. A rephrase event ("make it shorter") is a real signal. A CLAUDE.md file is a literal preference manifesto. Extract those, encode them as rules, and serve them over MCP.

**The wedge:** behavioral rule extraction from chat history + config files, served to any MCP-compatible client. Everything else (swipe UI, publishing, absorption loop, sanitizer) is Phase 2.

---

## What Thinkprint does today (MVP)

- **Tier 1 extraction (zero LLM):** parses `~/.claude/CLAUDE.md`, project-level `CLAUDE.md`, `~/.claude/agents/*.md`, `~/.claude/commands/*.md`, `.cursorrules`, `.windsurfrules` into explicit behavioral rules.
- **Tier 2 extraction (LLM-assisted):** parses ChatGPT and Claude chat exports, strips noise, flags prompt-injection attempts (soft-quarantine only), clusters by topic, detects rephrase + acceptance signals, synthesizes behavioral rules per cluster with Claude.
- **Storage + output:** persists rules to SQLite; renders a human-readable `thinkprint.md` grouped by topic with evidence inline.
- **MCP server:** exposes the profile over MCP so any compatible client can query `get_rules(topic)`, `list_thinkprint_topics()`, or read the full markdown resource.

## What's deliberately out of scope

Per the spec, the MVP ships only the core extraction wedge. The following are Phase 2:

- Next.js frontend / swipe review UI
- Nightly absorption loop and writeback signals
- PII/trade-secret sanitizer for publishing
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

Requires Python 3.10+. For Tier 2 synthesis set `ANTHROPIC_API_KEY`; without it, Tier 1 still works.

---

## Quickstart

**1. Extract your profile:**

```bash
# Full pipeline — Tier 1 config files + Tier 2 chat history
thinkprint extract \
  --claude-dir ~/.claude \
  --project . \
  --chatgpt-export ~/Downloads/chatgpt-export/conversations.json \
  --claude-export ~/Downloads/claude-export.json

# Tier 1 only — no LLM calls, no API key needed
thinkprint extract --claude-dir ~/.claude --no-llm
```

Outputs go to `./thinkprint.md` and `./.thinkprint/thinkprint.db`.

**2. Inspect:**

```bash
thinkprint show                       # full table of rules
thinkprint show --topic "code"        # filter by substring
thinkprint topics                     # topic -> rule count
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

Restart the client. Your AI can now call `get_rules(topic="writing")` at the start of any relevant conversation.

---

## How to get your chat exports

- **ChatGPT:** Settings → Data Controls → Export data → email arrives with a zip → `conversations.json`.
- **Claude:** Settings → Privacy → Export your data → email arrives with a zip.
- **Cursor:** chat history lives locally in SQLite — Phase 2 will parse it directly; for now, not supported.

All parsing is local. Nothing leaves your machine except the (cluster-scoped, truncated) text sent to Anthropic for Tier 2 synthesis, and only if you pass `--claude-export`/`--chatgpt-export` and have `ANTHROPIC_API_KEY` set.

---

## Architecture

```
inputs                                  pipeline                             outputs
──────                                  ────────                             ───────
~/.claude/CLAUDE.md       ┐
~/.claude/agents/*.md     │──► extract_config_rules ──────────► Tier 1 rules ┐
~/.claude/commands/*.md   │     (no LLM)                                     │
.cursorrules              │                                                  │
.windsurfrules            │                                                  │
                          │                                                  ├──► SQLite + thinkprint.md
ChatGPT export ──► parse ─┤                                                  │
Claude export  ──► parse ─┴──► strip_noise ──► flag_injection ──► cluster ──►│
                                                                  │          │
                                                                  ▼          │
                                                            detect signals   │
                                                                  │          │
                                                                  ▼          │
                                                         synthesize (Claude) ┘
                                                              Tier 2 rules

                                                                     │
                                                                     ▼
                                                              MCP server (FastMCP)
                                                              ├─ thinkprint://rules/all
                                                              ├─ get_rules(topic, limit)
                                                              └─ list_thinkprint_topics()
```

Key design decisions:

- **Cluster first, LLM second** — never send 5k messages to one call; one focused call per topical cluster.
- **Soft quarantine, never hard-block** — injection heuristics flag but never delete; matches the spec's "user has final say" principle.
- **TF-IDF instead of embeddings for MVP** — pure sklearn, installs in seconds. Swap to sentence-transformers later without changing the public API.
- **SQLite, not a service** — zero deployment friction; one file on disk.

---

## Project layout

```
thinkprint/
├── src/thinkprint/
│   ├── models.py                 # Pydantic data models (Message, Rule, Evidence, ...)
│   ├── extractors/
│   │   ├── config_files.py       # Tier 1: CLAUDE.md, .cursorrules, ...
│   │   └── chat_exports.py       # Tier 2: ChatGPT + Claude export parsers
│   ├── filter/
│   │   ├── noise.py              # drop greetings/acks/short msgs
│   │   └── injection.py          # layer-1 heuristic injection flagging
│   ├── archaeology/
│   │   ├── clusterer.py          # TF-IDF + KMeans topic clusters
│   │   ├── signals.py            # rephrase + acceptance signal detectors
│   │   └── synthesizer.py        # per-cluster Claude call → Rule objects
│   ├── storage.py                # SQLite persistence
│   ├── output.py                 # markdown rendering
│   ├── mcp_server.py             # FastMCP server
│   ├── pipeline.py               # end-to-end orchestration
│   └── cli.py                    # click-based CLI
├── tests/                        # pytest; runs without API key
├── examples/                     # sample CLAUDE.md + sample thinkprint.md
└── pyproject.toml
```

---

## Tests

```bash
pip install -e ".[dev]"
pytest
```

All tests run without an API key — they cover extractors, filters, signal detection, clustering, and storage round-trips.

---

## Roadmap

**Phase 2** (earned once the wedge has ~50 users actively running MCP queries):

- Swipe UI for rule review and refinement (per spec: 20-30 min session with probe questions)
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
