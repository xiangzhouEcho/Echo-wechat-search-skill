---
name: echo-wechat-search-skill
description: Use when searching WeChat Official Account (微信公众号) articles by keyword — finding public-account articles about a topic, getting a ranked list with title/account/date/summary, and optionally resolving real article links and downloading them as Markdown. Uses Sogou WeChat search (no account needed). Also triggers on Chinese phrasings such as 搜索公众号文章, 按关键词搜公众号, 搜微信文章, 找公众号文章, 关键词搜文章, 搜一搜公众号.
---

# Echo WeChat Search Skill — 关键词搜索公众号文章

## Overview

按关键词搜索微信公众号文章（走搜狗微信搜索，免账号），输出标题/公众号/日期/摘要/链接；可选把结果尽力解析成真实文章链接，并直接调用 echo-wechat-skill 下载为 Markdown。

**Core principle:** 搜狗是唯一带微信文章库的搜索引擎（腾讯旗下）。搜索本身稳定；结果给的是搜狗跳转链接，本 skill 用纯 Python 把它还原成真实 `mp.weixin.qq.com` 链接（拼出 `src=11` 签名链→抓正文→取 `msg_link` 规范链接），无需浏览器。

## When to Use

- 想按关键词找某话题的公众号文章（免账号、全网范围）
- 需要一份带标题/公众号/日期/摘要的结果列表（`--json` 供程序消费）
- 想「搜到就下」：`--download` 解析真实链接并交给 echo-wechat-skill 存 md

**Not for:**
- 在**指定某个公众号内**搜（那需要公众号后台扫码登录，本 skill 不做）
- 高频/大批量抓取 —— 搜狗按 IP 反爬，超量会触发验证码（antispider）
- 阅读数/评论等数据

## Requirements

- **uv** 必须已安装（用来运行脚本并自动装 Python 依赖）。
- **仅 `--download` 需要**已安装 [echo-wechat-skill](https://github.com/xiangzhouEcho/Echo-wechat-skill)（本机应位于 `~/.claude/skills/echo-wechat-skill`）；未安装时 `--download` 会打印明确错误并跳过下载，搜索/解析/`--json` 不受影响。

## Quick Start

**执行位置（重要）**：在你希望下载产物落地的目录运行，用脚本**绝对路径**调用；不要 `cd` 进 skill 目录。本机脚本绝对路径为 `~/.claude/skills/echo-wechat-search-skill/scripts/wechat_search.py`。

```bash
SEARCH=~/.claude/skills/echo-wechat-search-skill/scripts/wechat_search.py

# 仅搜索，人类可读列表
uv run "$SEARCH" "厄尔尼诺"

# 搜索 + 尽力解析真实链接（JSON 输出，供程序消费）
uv run "$SEARCH" "量子计算" --resolve --json

# 搜到就下：解析真实链接并用 echo-wechat-skill 存成 markdown
uv run "$SEARCH" "海洋科学" --download --limit 5 --format md

# 限定最近一周
uv run "$SEARCH" "台风" --time week
```

`--download` 会隐式启用解析，把解析成功的文章交给 echo-wechat-skill 下载。

## Options

| 选项 | 说明 | 默认 |
|------|------|------|
| `--pages N` | 搜索页数，每页约 10 条 | 1 |
| `--time` | 时间范围 `day`/`week`/`month`/`year` | 不限 |
| `--resolve` | 尽力把搜狗链接解析成真实文章链接 | 关 |
| `--download` | 解析后调 echo-wechat-skill 下载（隐含 --resolve） | 关 |
| `--format` | 下载格式，**逗号分隔可多选**（如 `md,html,pdf` 同时出三种） | md |
| `--out DIR` | 下载输出目录 | ./wechat-download |
| `--limit N` | 最多**解析/下载**多少条（对纯搜索的列表长度无效）；解析被限速时实际下载可能少于此数 | 5 |
| `--delay S` | 请求间隔秒数 | 3 |
| `--json` | 以 JSON 输出结果 | 关（人类可读） |

## How It Works

1. **搜索**：先 GET 搜狗首页种 cookie，再 `weixin.sogou.com/weixin?type=2&query=<kw>&page=N`，解析结果（去 `<em>` 高亮）。
2. **解析（best-effort，纯 Python）**：GET 搜狗 `/link?url=` 页 → 拼接 `url += '...'` 分片得 `src=11` 签名链接（**不能 html.unescape，否则 `&timestamp` 会被误解码成 `×`**）→ 用 requests 抓该链接的完整正文 → 从中提取 `var msg_link`（带 `__biz&mid&idx&sn&chksm`）或 `og:url` 作为规范链接。
3. **下载**：把解析成功的规范链接传给 `echo-wechat-skill` 的 `wechat_dl.py` 存 md/html/pdf。

## Common Mistakes

| 症状 | 处理 |
|------|------|
| `搜索失败: antispider` | 触发搜狗反爬。调大 `--delay`、减小 `--limit`/`--pages`，隔一段时间再试或换网络/IP |
| 解析全部失败但搜索正常 | 同上（`/link` 解析比搜索更易被限速）；降低频率重试 |
| 只想要列表不想下载 | 不加 `--download`；要真实链接加 `--resolve` |
| 结果只有约 10 页 | 搜狗未登录上限；本 skill 不做登录 |

## Verify

```bash
uv run ~/.claude/skills/echo-wechat-search-skill/scripts/selftest.py   # 离线自检，零网络
```
