# Session Export

**中文** | [English](README_EN.md)

在 Codex 会话被淹没在历史列表之前，把它保存为清晰、可搜索、方便回看的归档。

`session-export` 是一个 Codex Skill 和本地 Python 工具，可以将 Codex 对话导出为
Markdown、PDF，或直接保存到 Obsidian。它只保留真正有用的内容，默认排除内部提示词，
并在文档顶部附上简短摘要和实际保存路径。

## 为什么值得使用？

- 一条命令归档正在处理的 Codex 对话。
- 用 Markdown 建立可搜索的长期会话知识库。
- 输入 `se-obsi`，直接把重要对话保存到 Obsidian。
- 需要分享或离线阅读时，生成排版清晰的 PDF。
- 只有明确开启审计模式时，才附带工具调用详情。

## 安装

将仓库克隆到 Codex Skill 目录：

```bash
git clone https://github.com/jwliuiiii0520-shape-it/session-export.git \
  ~/.codex/skills/session-export
```

启动一个新的 Codex Session，让 Skill 被自动发现。

如果需要导出 PDF，还需要安装：

```bash
pip install markdown weasyprint
```

只导出 Markdown 或保存到 Obsidian 时，不需要这两个 PDF 依赖。

## 快速开始

### 导出当前对话

在 Codex 中输入：

```text
使用 $session-export 导出当前会话
```

也可以直接运行：

```bash
python3 ~/.codex/skills/session-export/scripts/export_session.py current
```

默认会在当前工作目录下同时生成 Markdown 和 PDF：

```text
./session-exports/
```

### 把当前对话保存到 Obsidian

在 Codex 中输入：

```text
se-obsi
```

Markdown 会保存到：

```text
<你的 Obsidian 仓库>/Codex Sessions/
```

### 导出以前的对话

先列出本地 Session：

```bash
python3 ~/.codex/skills/session-export/scripts/export_session.py --list
```

再使用指定 ID 导出：

```bash
python3 ~/.codex/skills/session-export/scripts/export_session.py <session-id>
```

## 到底会导出哪一条 Session？

| 参数 | 含义 | 推荐场景 |
| --- | --- | --- |
| `current` | 当前正在操作的 Codex 对话。环境支持时通过 `CODEX_THREAD_ID` 精确定位。 | 日常使用的默认选择。 |
| `latest` | 本机最近更新过的可见 Codex 对话。 | 明确希望导出最近活动的 Session 时使用。 |
| `<session-id>` | 通过 `--list` 选中的指定 Session。 | 导出历史对话，或需要绝对精确时使用。 |
| `/path/to/rollout.jsonl` | 指定本地 rollout 文件。 | 高级恢复或调试。 |

如果环境没有提供 `CODEX_THREAD_ID`，`current` 才会回退为 `latest`。需要绝对确定时，
请先使用 `--list`，再传入指定 Session ID。

`se-obsi` 使用 `current`，因此在 Codex Desktop 等支持 `CODEX_THREAD_ID` 的环境中，
它保存的是你正在操作的这条对话。

## 常用命令

```bash
# 导出当前对话：Markdown + PDF
python3 scripts/export_session.py current

# 只导出 Markdown
python3 scripts/export_session.py current --format md

# 只导出 PDF
python3 scripts/export_session.py current --format pdf

# 导出最近更新的可见对话
python3 scripts/export_session.py latest

# 指定保存目录
python3 scripts/export_session.py current --output-dir ~/Documents/session-exports

# 保存到 Obsidian
python3 scripts/export_session.py current --obsidian

# 附带脱敏后的工具参数和截断后的工具输出
python3 scripts/export_session.py current --include-tools
```

## 导出的文档里有什么？

文档顶部包含：

- Session ID 和时间
- 工作目录和 rollout 来源
- 实际生成文件的绝对路径
- 一段简短的确定性摘要
- 用户消息、Codex 消息和工具调用数量

对话正文包含：

- 用户消息
- Codex 的 commentary 和最终回复
- 工具名称和调用次数摘要

## 默认隐私保护

默认不会导出：

- 系统提示词
- Developer 指令
- 推理过程
- Token 计数
- 原始工具参数和工具输出

开启 `--include-tools` 后，文档会附带经过尽力脱敏的参数和截断后的工具输出。
分享归档文件前仍应自行检查：可见对话文本和项目输出中依然可能包含隐私信息。

所有处理都在本机完成。脚本不会上传任何 Session 内容。

## Obsidian 配置

Skill 不会写死任何人的仓库名称或个人路径。它按照以下顺序查找 Obsidian 仓库：

1. `--obsidian-vault /path/to/vault`
2. `SESSION_EXPORT_OBSIDIAN_VAULT`
3. `~/.config/session-export/config.json`
4. Obsidian 本机配置中唯一存在或当前打开的仓库

可选配置文件：

```json
{
  "obsidian_vault": "~/Documents/My Vault",
  "obsidian_subdir": "Codex Sessions"
}
```

也可以覆盖仓库内的保存目录：

```bash
SESSION_EXPORT_OBSIDIAN_SUBDIR="AI/Codex Sessions" \
  python3 scripts/export_session.py current --obsidian
```

如果存在多个仓库且无法可靠判断，脚本会停止并提示用户明确配置，不会自行猜测。

## 补充说明

- 本地 Codex rollout 文件来自 `~/.codex/sessions/`。
- 可见 Session 标题来自 `~/.codex/session_index.jsonl`。
- `current` 面向 Codex Desktop，以及其他会提供 `CODEX_THREAD_ID` 的环境。
- 默认 Obsidian 子目录为 `Codex Sessions/`。

## License

MIT

