# Session Export

A Codex skill for exporting local Codex session transcripts as readable
Markdown and PDF archives. It can also save Markdown transcripts directly into
an Obsidian vault with the `se-obsi` shortcut.

## Install

Clone this repository into your Codex skills directory:

```bash
git clone https://github.com/jwliuiiii0520-shape-it/session-export.git \
  ~/.codex/skills/session-export
```

Start a new Codex session so the skill can be discovered.

## Usage

Ask Codex:

```text
Use $session-export to export the current session.
```

Or run the script directly:

```bash
python3 scripts/export_session.py current
python3 scripts/export_session.py latest
python3 scripts/export_session.py --list
python3 scripts/export_session.py <session-id>
```

The default destination is `./session-exports/`. The default export format is
Markdown plus PDF. `current` resolves the active Codex thread through
`CODEX_THREAD_ID` when available; `latest` selects the most recently updated
visible thread.

## Obsidian Shortcut

Ask Codex:

```text
se-obsi
```

This exports Markdown into:

```text
<vault>/Codex Sessions/
```

The vault is resolved in this order:

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

## PDF Dependencies

PDF rendering requires:

```bash
pip install markdown weasyprint
```

Markdown-only and Obsidian exports do not require these packages.

## Privacy

The default export includes visible user messages, Codex replies, and a compact
tool-name summary. It excludes system prompts, developer instructions,
reasoning traces, token counters, and raw tool output.

`--include-tools` adds best-effort redacted arguments and truncated outputs.
Review any generated transcript before sharing it: visible conversation text
and project output may still contain sensitive information.
