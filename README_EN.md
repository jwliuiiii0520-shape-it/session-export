# Session Export

<p align="center">
  <a href="./README.md">中文</a> · English
</p>

Some Codex sessions are more than temporary chats.

They may contain a complete investigation, the reasoning behind an important
decision, reusable prompts, or the full context of a project from diagnosis to
implementation. Leaving them in a session list makes them hard to find and
awkward to revisit later.

`session-export` saves important Codex conversations as Markdown, PDF, or
Obsidian notes. The result is not just a short summary. It is a readable
long-term archive of the full conversation: user messages, Codex responses,
and a compact tool-call summary, with internal prompts excluded by default.

## Why Use It?

- **Review the full conversation:** revisit the analysis process, not only the final answer.
- **Build a knowledge base:** keep valuable sessions searchable as Markdown instead of losing them in a history list.
- **Preserve project context:** save key discussions, decisions, and implementation history for future handoffs.
- **Archive to Obsidian:** type `se-obsi` to save the active conversation into your personal knowledge base.
- **Read or share offline:** generate a clean PDF when a session deserves a durable copy.
- **Audit when needed:** include tool details only when you explicitly request them.

## Install

Clone this repository into your Codex skills directory:

```bash
git clone https://github.com/jwliuiiii0520-shape-it/session-export.git \
  ~/.codex/skills/session-export
```

Start a new Codex session so the skill can be discovered.

PDF export additionally requires:

```bash
pip install markdown weasyprint
```

Markdown and Obsidian exports work without these PDF packages.

## Quick Start

### Export The Current Conversation

Ask Codex:

```text
Use $session-export to export this session.
```

Or run:

```bash
python3 ~/.codex/skills/session-export/scripts/export_session.py current
```

The default output is Markdown plus PDF in:

```text
./session-exports/
```

### Save The Current Conversation To Obsidian

Ask Codex:

```text
se-obsi
```

This exports Markdown into:

```text
<your-vault>/Codex Sessions/
```

### Export A Previous Conversation

List local sessions:

```bash
python3 ~/.codex/skills/session-export/scripts/export_session.py --list
```

Then export one by ID:

```bash
python3 ~/.codex/skills/session-export/scripts/export_session.py <session-id>
```

## Which Session Gets Exported?

| Selector | Meaning | Recommended use |
| --- | --- | --- |
| `current` | The active Codex conversation. It uses `CODEX_THREAD_ID` when available. | Default for normal use. |
| `latest` | The most recently updated visible local Codex conversation. | Use when you intentionally want the newest local activity. |
| `<session-id>` | The exact session you selected from `--list`. | Use for older sessions or when exact selection matters. |
| `/path/to/rollout.jsonl` | An explicit local rollout file. | Advanced recovery or debugging. |

If `CODEX_THREAD_ID` is unavailable, `current` falls back to `latest`. When
exact selection matters, use `--list` and pass a session ID.

`se-obsi` uses `current`, so it saves the conversation you are actively working
in whenever `CODEX_THREAD_ID` is available.

## Common Commands

```bash
# Markdown + PDF for the active conversation
python3 scripts/export_session.py current

# Markdown only
python3 scripts/export_session.py current --format md

# PDF only
python3 scripts/export_session.py current --format pdf

# Most recently updated visible conversation
python3 scripts/export_session.py latest

# Choose a destination
python3 scripts/export_session.py current --output-dir ~/Documents/session-exports

# Save Markdown into Obsidian
python3 scripts/export_session.py current --obsidian

# Include redacted tool arguments and truncated tool output
python3 scripts/export_session.py current --include-tools
```

## What Gets Exported?

The generated archive starts with:

- Session ID and timestamp
- Working directory and rollout source
- Absolute paths of generated files
- A short deterministic session summary
- Counts for user messages, Codex messages, and tool calls

The conversation body includes:

- User messages
- Codex commentary and final responses
- A compact summary of tool names and call counts

## Privacy Defaults

By default, the exporter excludes:

- System prompts
- Developer instructions
- Reasoning traces
- Token counters
- Raw tool arguments and output

`--include-tools` adds best-effort redacted arguments and truncated output.
Review any generated archive before sharing it: visible conversation text and
project output can still contain private information.

Everything runs locally. The script does not upload session content anywhere.

## Obsidian Configuration

The skill never hardcodes a personal vault name or path. It resolves the vault
in this order:

1. `--obsidian-vault /path/to/vault`
2. `SESSION_EXPORT_OBSIDIAN_VAULT`
3. `~/.config/session-export/config.json`
4. A unique or currently open vault from Obsidian's local configuration

Optional configuration:

```json
{
  "obsidian_vault": "~/Documents/My Vault",
  "obsidian_subdir": "Codex Sessions"
}
```

You can also override the vault-relative destination:

```bash
SESSION_EXPORT_OBSIDIAN_SUBDIR="AI/Codex Sessions" \
  python3 scripts/export_session.py current --obsidian
```

If multiple vaults exist and the exporter cannot choose one safely, it stops
and asks you to configure a vault explicitly.

## Notes

- Local Codex rollout files are read from `~/.codex/sessions/`.
- Visible session titles are read from `~/.codex/session_index.jsonl`.
- `current` is designed for Codex Desktop and other environments that expose
  `CODEX_THREAD_ID`.
- The default Obsidian subdirectory is `Codex Sessions/`.

## License

MIT
