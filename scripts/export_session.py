#!/usr/bin/env python3
"""Export Codex rollout JSONL sessions to readable Markdown and PDF."""

from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Iterable


CODEX_HOME = Path(os.environ.get("CODEX_HOME", Path.home() / ".codex"))
SESSIONS_DIR = CODEX_HOME / "sessions"
SESSION_INDEX = CODEX_HOME / "session_index.jsonl"
CONFIG_PATH = Path.home() / ".config" / "session-export" / "config.json"
DEFAULT_OBSIDIAN_SUBDIR = "Codex Sessions"


def read_jsonl(path: Path) -> Iterable[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            try:
                yield json.loads(line)
            except json.JSONDecodeError as exc:
                print(f"warning: skipped invalid JSON at {path}:{line_number}: {exc}", file=sys.stderr)


def index_titles() -> dict[str, str]:
    if not SESSION_INDEX.exists():
        return {}
    titles: dict[str, str] = {}
    for item in read_jsonl(SESSION_INDEX):
        session_id = item.get("id")
        if session_id:
            titles[str(session_id)] = str(item.get("thread_name") or session_id)
    return titles


def rollout_files() -> list[Path]:
    if not SESSIONS_DIR.exists():
        return []
    return sorted(SESSIONS_DIR.rglob("rollout-*.jsonl"), key=lambda path: path.stat().st_mtime, reverse=True)


def visible_rollout_files() -> list[Path]:
    files = rollout_files()
    titles = index_titles()
    visible = [path for path in files if session_id_from_path(path) in titles]
    return visible or files


def read_config() -> dict[str, Any]:
    if not CONFIG_PATH.exists():
        return {}
    try:
        return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"Could not read config {CONFIG_PATH}: {exc}")


def obsidian_config_paths() -> list[Path]:
    candidates = [
        Path.home() / "Library" / "Application Support" / "obsidian" / "obsidian.json",
        Path.home() / ".config" / "obsidian" / "obsidian.json",
    ]
    if os.environ.get("APPDATA"):
        candidates.append(Path(os.environ["APPDATA"]) / "obsidian" / "obsidian.json")
    return candidates


def detected_obsidian_vaults() -> list[tuple[Path, bool]]:
    for config_path in obsidian_config_paths():
        if not config_path.exists():
            continue
        try:
            data = json.loads(config_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise SystemExit(f"Could not read Obsidian config {config_path}: {exc}")
        vaults = []
        for item in (data.get("vaults") or {}).values():
            path = item.get("path")
            if path:
                vaults.append((Path(path).expanduser(), bool(item.get("open"))))
        return vaults
    return []


def resolve_obsidian_vault(explicit_vault: Path | None) -> Path:
    config = read_config()
    configured = explicit_vault or os.environ.get("SESSION_EXPORT_OBSIDIAN_VAULT") or config.get("obsidian_vault")
    if configured:
        vault = Path(configured).expanduser().resolve()
        if not vault.is_dir():
            raise SystemExit(f"Configured Obsidian vault is not a directory: {vault}")
        return vault

    vaults = detected_obsidian_vaults()
    open_vaults = [path for path, is_open in vaults if is_open and path.is_dir()]
    existing_vaults = [path for path, _ in vaults if path.is_dir()]
    if len(open_vaults) == 1:
        return open_vaults[0].resolve()
    if len(existing_vaults) == 1:
        return existing_vaults[0].resolve()

    detected = "\n".join(f"- {path}" for path, _ in vaults) or "- none"
    raise SystemExit(
        "Could not choose an Obsidian vault automatically.\n"
        f"Detected vaults:\n{detected}\n"
        "Set SESSION_EXPORT_OBSIDIAN_VAULT, add obsidian_vault to "
        f"{CONFIG_PATH}, or pass --obsidian-vault."
    )


def session_id_from_path(path: Path) -> str:
    match = re.search(r"([0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12})\.jsonl$", path.name)
    return match.group(1) if match else path.stem


def resolve_session(selector: str) -> Path:
    candidate = Path(selector).expanduser()
    if candidate.is_file():
        return candidate.resolve()

    files = rollout_files()
    if not files:
        raise SystemExit(f"No rollout JSONL files found under {SESSIONS_DIR}")

    if selector == "current":
        current_thread_id = os.environ.get("CODEX_THREAD_ID")
        if current_thread_id:
            matches = [path for path in files if current_thread_id in path.name]
            if len(matches) == 1:
                return matches[0]
        return visible_rollout_files()[0]

    if selector == "latest":
        return visible_rollout_files()[0]

    matches = [path for path in files if selector in path.name]
    if len(matches) == 1:
        return matches[0]
    if not matches:
        raise SystemExit(f"No session rollout matched {selector!r}")
    raise SystemExit(f"Session selector {selector!r} matched multiple rollouts; use a longer ID")


def redact(text: str) -> str:
    home = str(Path.home())
    text = text.replace(home, "~")
    patterns = [
        (r"(?i)(authorization\s*[:=]\s*bearer\s+)[^\s\"']+", r"\1[REDACTED]"),
        (r"(?i)((?:api[_-]?key|token|password|secret)\s*[:=]\s*)[^\s,\"'}]+", r"\1[REDACTED]"),
        (r"(?i)(sk-[a-z0-9_-]{12,})", "[REDACTED]"),
    ]
    for pattern, replacement in patterns:
        text = re.sub(pattern, replacement, text)
    return text


def message_text(payload: dict[str, Any]) -> str:
    message = payload.get("message")
    if isinstance(message, str):
        return message.strip()
    return ""


def parse_rollout(path: Path, include_tools: bool, max_tool_output: int) -> dict[str, Any]:
    transcript: list[tuple[str, str, str | None]] = []
    tools: list[dict[str, str]] = []
    metadata: dict[str, str] = {}
    pending_tools: dict[str, dict[str, str]] = {}

    for item in read_jsonl(path):
        payload = item.get("payload") or {}
        item_type = item.get("type")

        if item_type == "session_meta":
            for key in ("id", "cwd", "timestamp", "model_provider"):
                if payload.get(key) is not None:
                    metadata[key] = str(payload[key])
            continue

        if item_type == "event_msg":
            payload_type = payload.get("type")
            if payload_type == "user_message":
                text = message_text(payload)
                if text:
                    transcript.append(("User", text, None))
            elif payload_type == "agent_message":
                text = message_text(payload)
                if text:
                    transcript.append(("Codex", text, payload.get("phase")))
            continue

        if item_type != "response_item":
            continue
        payload_type = payload.get("type")
        if payload_type == "function_call":
            call = {
                "name": str(payload.get("name") or "unknown"),
                "arguments": redact(str(payload.get("arguments") or "")),
                "output": "",
            }
            tools.append(call)
            if payload.get("call_id"):
                pending_tools[str(payload["call_id"])] = call
        elif include_tools and payload_type == "function_call_output":
            call = pending_tools.get(str(payload.get("call_id") or ""))
            if call is not None:
                output = redact(str(payload.get("output") or ""))
                if len(output) > max_tool_output:
                    output = output[:max_tool_output] + "\n...[truncated]"
                call["output"] = output

    metadata.setdefault("id", session_id_from_path(path))
    metadata["rollout_path"] = str(path)
    return {"metadata": metadata, "transcript": transcript, "tools": tools}


def safe_slug(text: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9_-]+", "-", text).strip("-").lower()
    return slug[:72] or "codex-session"


def fenced(text: str) -> str:
    fence = "```"
    if "```" in text:
        fence = "````"
    return f"{fence}text\n{text}\n{fence}"


def compact(text: str, limit: int = 240) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    return text if len(text) <= limit else text[: limit - 3].rstrip() + "..."


def build_markdown(
    data: dict[str, Any],
    title: str,
    include_tools: bool,
    exported_files: list[Path],
) -> str:
    metadata = data["metadata"]
    transcript = data["transcript"]
    tools = data["tools"]
    first_request = next((text for role, text, _ in transcript if role == "User"), "")
    user_count = sum(role == "User" for role, _, _ in transcript)
    codex_count = sum(role == "Codex" for role, _, _ in transcript)
    lines = [
        f"# {title}",
        "",
        f"- Session ID: `{metadata.get('id', '')}`",
        f"- Started: `{metadata.get('timestamp', '')}`",
        f"- Working directory: `{redact(metadata.get('cwd', ''))}`",
        f"- Source: `{redact(metadata.get('rollout_path', ''))}`",
        "- Exported files:",
        *[f"  - `{path}`" for path in exported_files],
        "",
        "## Session Summary",
        "",
        f"{title}. {compact(first_request)}",
        "",
        f"This archive contains {user_count} user message(s), {codex_count} Codex message(s), and {len(tools)} tool call(s).",
        "",
        "## Conversation",
        "",
    ]
    for role, text, phase in transcript:
        phase_suffix = f" ({phase})" if role == "Codex" and phase else ""
        lines.extend([f"### {role}{phase_suffix}", "", text, ""])

    lines.extend(["## Tool Summary", ""])
    if not tools:
        lines.append("No tool calls recorded.")
    else:
        counts: dict[str, int] = {}
        for tool in tools:
            counts[tool["name"]] = counts.get(tool["name"], 0) + 1
        for name, count in sorted(counts.items()):
            lines.append(f"- `{name}`: {count}")

    if include_tools and tools:
        lines.extend(["", "## Tool Details", "", "> Best-effort redaction applied. Review before sharing.", ""])
        for index, tool in enumerate(tools, start=1):
            lines.extend([f"### {index}. `{tool['name']}`", ""])
            if tool["arguments"]:
                lines.extend(["Arguments:", "", fenced(tool["arguments"]), ""])
            if tool["output"]:
                lines.extend(["Output:", "", fenced(tool["output"]), ""])

    return "\n".join(lines).rstrip() + "\n"


def write_pdf(markdown_text: str, output_path: Path, title: str) -> None:
    try:
        import markdown
        from weasyprint import HTML
    except ImportError as exc:
        raise RuntimeError("PDF export requires Python packages: markdown and weasyprint") from exc

    body = markdown.markdown(markdown_text, extensions=["fenced_code", "tables"])
    document = f"""<!doctype html>
<html><head><meta charset="utf-8"><style>
@page {{ size: A4; margin: 18mm 17mm 20mm; @bottom-center {{ content: counter(page); color: #888; font-size: 9pt; }} }}
body {{ font-family: -apple-system, BlinkMacSystemFont, "PingFang SC", "Helvetica Neue", Arial, sans-serif; color: #243447; font-size: 10.5pt; line-height: 1.65; }}
h1 {{ color: #123b66; font-size: 24pt; border-bottom: 2px solid #dbe6ef; padding-bottom: 8px; }}
h2 {{ color: #185f91; margin-top: 24px; border-bottom: 1px solid #e5edf3; }}
h3 {{ color: #314e64; margin: 18px 0 6px; }}
pre {{ background: #f5f7f9; border: 1px solid #e1e7eb; padding: 10px; white-space: pre-wrap; overflow-wrap: anywhere; font-size: 8.5pt; }}
code {{ background: #f5f7f9; padding: 1px 3px; overflow-wrap: anywhere; }}
blockquote {{ color: #566b78; border-left: 3px solid #b8c9d4; margin-left: 0; padding-left: 12px; }}
li {{ margin: 3px 0; }}
</style><title>{html.escape(title)}</title></head><body>{body}</body></html>"""
    HTML(string=document).write_pdf(str(output_path))


def list_sessions(limit: int) -> None:
    titles = index_titles()
    print("SESSION ID                            UPDATED              TITLE")
    for path in visible_rollout_files()[:limit]:
        session_id = session_id_from_path(path)
        updated = dt.datetime.fromtimestamp(path.stat().st_mtime).astimezone().strftime("%Y-%m-%d %H:%M")
        print(f"{session_id:<36}  {updated:<19}  {titles.get(session_id, '')}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("session", nargs="?", default="current", help="current thread, latest visible thread, session ID, or rollout JSONL path")
    parser.add_argument("--format", choices=("both", "md", "pdf"), default="both")
    parser.add_argument("--output-dir", type=Path, default=Path.cwd() / "session-exports")
    parser.add_argument("--obsidian", action="store_true", help="export Markdown to an Obsidian vault")
    parser.add_argument("--obsidian-vault", type=Path, help="explicit Obsidian vault path")
    parser.add_argument("--obsidian-subdir", help=f"vault-relative export directory (default: {DEFAULT_OBSIDIAN_SUBDIR!r})")
    parser.add_argument("--include-tools", action="store_true", help="include redacted tool arguments and truncated outputs")
    parser.add_argument("--max-tool-output", type=int, default=4000)
    parser.add_argument("--list", action="store_true", help="list recent local Codex sessions")
    parser.add_argument("--limit", type=int, default=20, help="number of sessions shown by --list")
    args = parser.parse_args()

    if args.list:
        list_sessions(args.limit)
        return 0

    if args.obsidian_vault or args.obsidian_subdir:
        args.obsidian = True
    if args.obsidian:
        config = read_config()
        vault = resolve_obsidian_vault(args.obsidian_vault)
        subdir = args.obsidian_subdir or os.environ.get("SESSION_EXPORT_OBSIDIAN_SUBDIR") or config.get("obsidian_subdir") or DEFAULT_OBSIDIAN_SUBDIR
        output_dir = (vault / subdir).resolve()
        if vault != output_dir and vault not in output_dir.parents:
            raise SystemExit(f"Obsidian export directory must stay inside the vault: {output_dir}")
        args.output_dir = output_dir
        args.format = "md"

    path = resolve_session(args.session)
    data = parse_rollout(path, args.include_tools, args.max_tool_output)
    session_id = data["metadata"]["id"]
    title = index_titles().get(session_id, f"Codex Session {session_id}")
    timestamp = dt.datetime.now().astimezone().strftime("%Y-%m-%d-%H%M")
    stem = f"{timestamp}-{safe_slug(title)}"

    output_dir = args.output_dir.expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    markdown_path = output_dir / f"{stem}.md"
    pdf_path = output_dir / f"{stem}.pdf"
    exported_files = []
    if args.format in {"both", "md"}:
        exported_files.append(markdown_path)
    if args.format in {"both", "pdf"}:
        exported_files.append(pdf_path)
    markdown_text = build_markdown(data, title, args.include_tools, exported_files)

    if args.format in {"both", "md"}:
        markdown_path.write_text(markdown_text, encoding="utf-8")
        print(f"Markdown: {markdown_path}")
    if args.format in {"both", "pdf"}:
        write_pdf(markdown_text, pdf_path, title)
        print(f"PDF: {pdf_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
