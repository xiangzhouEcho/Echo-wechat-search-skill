# Echo WeChat Search Skill · Search WeChat Official Account Articles by Keyword

![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)
![Skill](https://img.shields.io/badge/Skill-Agent-111111?style=flat-square)
![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square)
![Claude Code](https://img.shields.io/badge/Claude%20Code-Supported-6B5B95?style=flat-square)

> 🌏 **中文版：[README.md](./README.md)**

A skill for Claude Code / Codex and similar agents that **searches WeChat Official Account (微信公众号) articles by keyword** (via Sogou WeChat search, no account needed), returning title / account / date / summary / link. It can optionally **best-effort resolve results into real article URLs** and hand them to [echo-wechat-skill](https://github.com/xiangzhouEcho/Echo-wechat-skill) to download as Markdown.

Core idea: **Sogou is the only search engine with the WeChat article corpus** (Tencent-owned). Search itself is stable; results are Sogou redirect links, which this skill turns into real `mp.weixin.qq.com` URLs in **pure Python** (rebuild the `src=11` signed link → fetch the article → extract the `msg_link` canonical URL) — **no browser required**.

- **Account-free web-wide search**: keyword → ~10 results/page with account name, date, summary, thumbnail
- **Best-effort link resolution**: `--resolve` turns Sogou redirects into directly-fetchable `mp.weixin.qq.com/s` URLs
- **Search-then-download**: `--download` passes resolved articles to echo-wechat-skill for md/html/pdf
- **Machine-consumable**: `--json` for agents to call

## 30-Second Start

Dependencies are declared inline (PEP 723) and installed automatically by [uv](https://github.com/astral-sh/uv). Run from the directory where you want output, calling the script by absolute path (don't `cd` into the skill dir):

```bash
SEARCH=~/.claude/skills/echo-wechat-search-skill/scripts/wechat_search.py

# Search only
uv run "$SEARCH" "厄尔尼诺"

# Search + resolve real links (JSON)
uv run "$SEARCH" "量子计算" --resolve --json

# Search then download as markdown via echo-wechat-skill
uv run "$SEARCH" "海洋科学" --download --limit 5 --format md
```

Inside an agent, just say "search WeChat articles about X and download them".

## Options

| Option | Meaning | Default |
|--------|---------|---------|
| `--pages N` | Result pages, ~10 per page | 1 |
| `--time` | Time range `day`/`week`/`month`/`year` | all |
| `--resolve` | Best-effort resolve Sogou links to real URLs | off |
| `--download` | Resolve then download via echo-wechat-skill (implies --resolve) | off |
| `--format` | Download format: `md,html,pdf` | md |
| `--out DIR` | Download output dir | ./wechat-download |
| `--limit N` | Max items to resolve/download | 5 |
| `--delay S` | Seconds between requests | 3 |
| `--json` | Output results as JSON | off |

## How It Works

1. **Search**: seed Sogou cookies, then `weixin.sogou.com/weixin?type=2&query=<kw>`, parse results (strip keyword highlight).
2. **Resolve (best-effort, pure Python)**: fetch the Sogou `/link?url=` page → join the `url += '...'` fragments into the `src=11` signed link (**do not `html.unescape` — it would turn `&timestamp` into the × sign**) → fetch that with requests to get the full article → extract `var msg_link` (with `__biz&mid&idx&sn&chksm`) or `og:url` as the canonical URL.
3. **Download**: pass canonical URLs to echo-wechat-skill's `wechat_dl.py`.

## Limitations

- **Sogou rate-limits by IP**: high frequency triggers a captcha (`antispider`). Increase `--delay`, lower `--limit/--pages`, or retry later / change network. `--resolve` is more rate-limited than plain search.
- **~10 pages max without login**; this skill does not log into Sogou.
- **No in-account search** (that needs a WeChat backend QR login).
- Resolution is **best-effort**: when rate-limited it may partially/fully fail; you still get the Sogou redirect links (openable in a browser).

## Dependencies

- [uv](https://github.com/astral-sh/uv)
- Python deps (auto): `requests`, `beautifulsoup4`, `lxml`
- Download requires [echo-wechat-skill](https://github.com/xiangzhouEcho/Echo-wechat-skill) installed

## Self-Test

```bash
uv run ~/.claude/skills/echo-wechat-search-skill/scripts/selftest.py   # offline
```

## License

MIT © xiangzhouEcho
