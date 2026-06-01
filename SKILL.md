---
name: session-export
description: Export Codex session conversation records into readable Markdown and PDF archives or save Markdown transcripts into an Obsidian vault. Use when the user asks to export, archive, save, print, or preserve a Codex session, chat transcript, conversation history, or thread as .md or .pdf files, or says `se-obsi` to export the current session into Obsidian. Supports the current session, the latest visible session, a session ID, or a rollout JSONL path.
---

# Session Export

Export a readable transcript with `scripts/export_session.py`. Keep the default
privacy-preserving output unless the user explicitly asks for tool details.

## Quick Start

Export the current Codex session to both Markdown and PDF:

```bash
python3 scripts/export_session.py current
```

Export a specific session:

```bash
python3 scripts/export_session.py <session-id>
```

Useful options:

```bash
python3 scripts/export_session.py --list
python3 scripts/export_session.py current --format md
python3 scripts/export_session.py current --output-dir /path/to/exports
python3 scripts/export_session.py current --include-tools
```

## Obsidian Shortcut

When the user says `se-obsi`, export the current Codex session as Markdown into
the user's Obsidian vault:

```bash
python3 scripts/export_session.py current --obsidian
```

Default Obsidian destination:

```text
<vault>/Codex Sessions/
```

For a public skill, never hardcode a vault name or personal path. Resolve the
vault in this order:

1. `--obsidian-vault /path/to/vault`
2. `SESSION_EXPORT_OBSIDIAN_VAULT`
3. `~/.config/session-export/config.json`
4. A unique or currently open vault from Obsidian's local configuration

Optional portable configuration:

```json
{
  "obsidian_vault": "~/Documents/My Vault",
  "obsidian_subdir": "Codex Sessions"
}
```

The environment variable `SESSION_EXPORT_OBSIDIAN_SUBDIR` and option
`--obsidian-subdir` can override the default subdirectory. If vault detection
is ambiguous, report the detected vaults and ask the user to configure one.

## Workflow

1. Run the script from the user's intended project or output directory.
2. Use `current` for the active Codex thread. It resolves `CODEX_THREAD_ID`
   when available and falls back to the most recently updated visible rollout.
   Use `latest` explicitly for the most recently updated visible rollout. If
   exact selection matters and `CODEX_THREAD_ID` is unavailable, run `--list`
   and use a Session ID.
3. Report the generated `.md` and `.pdf` paths.
4. Warn the user before using `--include-tools`: command arguments and truncated
   tool outputs may still contain sensitive project data after best-effort
   redaction.

## Output Policy

- Include user messages and Codex commentary/final responses.
- Add a top-level session summary and the absolute paths of generated files.
- Exclude system prompts, developer instructions, reasoning traces, token
  counters, and raw tool output by default.
- Add a compact tool-name summary by default.
- Add redacted arguments and truncated outputs only with `--include-tools`.
- Treat generated transcripts as local artifacts that may still contain
  sensitive information from the visible conversation itself.

## PDF Dependencies

PDF export uses Python packages `markdown` and `weasyprint`. If they are
missing, export Markdown first and tell the user PDF generation requires those
packages. Do not install dependencies without approval.
