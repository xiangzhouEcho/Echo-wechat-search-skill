# Echo WeChat Search Skill · 关键词搜索微信公众号文章

![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)
![Skill](https://img.shields.io/badge/Skill-Agent-111111?style=flat-square)
![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square)
![Claude Code](https://img.shields.io/badge/Claude%20Code-Supported-6B5B95?style=flat-square)

> 🌏 **English version: [README.en.md](./README.en.md)**

一个适配 Claude Code / Codex 等 Agent 环境的技能，**按关键词搜索微信公众号文章**（走搜狗微信搜索，免账号），输出标题/公众号/日期/摘要/链接；可选把结果**尽力解析成真实文章链接**，并直接调用 [echo-wechat-skill](https://github.com/xiangzhouEcho/Echo-wechat-skill) 下载为 Markdown。

核心是一句话：**搜狗是唯一带微信文章库的搜索引擎**（腾讯旗下）。搜索本身稳定；结果给的是搜狗跳转链接，本技能用**纯 Python** 还原成真实 `mp.weixin.qq.com` 链接（拼 `src=11` 签名链 → 抓正文 → 取 `msg_link` 规范链接），**无需浏览器**。

- **免账号全网搜**：关键词 → 一页约 10 条，含公众号名、发布日期、摘要、缩略图
- **尽力解析真实链接**：`--resolve` 把搜狗跳转链还原成可直接抓取的 `mp.weixin.qq.com/s` 链接
- **搜到就下**：`--download` 把解析成功的文章交给 echo-wechat-skill 存 md/html/pdf
- **供程序消费**：`--json` 输出结构化结果，方便 Claude 等调用

## 30 秒开始

依赖由 [uv](https://github.com/astral-sh/uv) 按脚本内联声明自动安装，无需 `pip install`。在你希望产物落地的目录运行，用脚本绝对路径调用（不要 cd 进 skill 目录）：

```bash
SEARCH=~/.claude/skills/echo-wechat-search-skill/scripts/wechat_search.py

# 仅搜索
uv run "$SEARCH" "厄尔尼诺"

# 搜索 + 解析真实链接（JSON）
uv run "$SEARCH" "量子计算" --resolve --json

# 搜到就下：解析并用 echo-wechat-skill 存 markdown
uv run "$SEARCH" "海洋科学" --download --limit 5 --format md
```

在 Agent 里直接说「搜索关于 X 的公众号文章并下载」即可自动触发。

## 选项

| 选项 | 说明 | 默认 |
|------|------|------|
| `--pages N` | 搜索页数，每页约 10 条 | 1 |
| `--time` | 时间范围 `day`/`week`/`month`/`year` | 不限 |
| `--resolve` | 尽力把搜狗链接解析成真实文章链接 | 关 |
| `--download` | 解析后调 echo-wechat-skill 下载（隐含 --resolve） | 关 |
| `--format` | 下载格式：`md,html,pdf` | md |
| `--out DIR` | 下载输出目录 | ./wechat-download |
| `--limit N` | 最多解析/下载多少条 | 5 |
| `--delay S` | 请求间隔秒数 | 3 |
| `--json` | 以 JSON 输出结果 | 关 |

## 工作原理

1. **搜索**：先种搜狗 cookie，再 `weixin.sogou.com/weixin?type=2&query=<kw>`，解析结果（去关键词高亮）。
2. **解析（尽力、纯 Python）**：取搜狗 `/link?url=` 页 → 拼 `url += '...'` 分片得 `src=11` 签名链接（**注意不能 `html.unescape`，否则 `&timestamp` 会被误解成乘号 ×**）→ requests 抓完整正文 → 提取 `var msg_link`（带 `__biz&mid&idx&sn&chksm`）或 `og:url` 作规范链接。
3. **下载**：把规范链接传给 echo-wechat-skill 的 `wechat_dl.py` 存 md/html/pdf。

## 局限（技术边界）

- **搜狗按 IP 反爬**：高频会触发验证码（`antispider`）。调大 `--delay`、减小 `--limit/--pages`，或隔段时间/换网络重试。`--resolve` 比纯搜索更易被限速。
- **未登录约 10 页上限**，本技能不做搜狗登录。
- **不做指定公众号内搜**（那需公众号后台扫码登录）。
- 解析是 **best-effort**：被限速时可能部分/全部失败，此时仍可拿到搜狗跳转链接（浏览器可打开）。

## 依赖

- [uv](https://github.com/astral-sh/uv)
- Python 依赖（uv 自动）：`requests`、`beautifulsoup4`、`lxml`
- 下载功能依赖已安装的 [echo-wechat-skill](https://github.com/xiangzhouEcho/Echo-wechat-skill)

## 自检

```bash
uv run ~/.claude/skills/echo-wechat-search-skill/scripts/selftest.py   # 离线，零网络
```

## Echo 微信技能族

三个技能可组成流水线：**搜索 → 下载 → 排版发布**。

- [Echo-wechat-search-skill](https://github.com/xiangzhouEcho/Echo-wechat-search-skill) — 关键词搜索公众号文章，可一键串联下载 · 本仓库
- [Echo-wechat-skill](https://github.com/xiangzhouEcho/Echo-wechat-skill) — 免证书下载文章（单篇/合集/批量，md/html/pdf + 图片/视频/音频）
- [Echo-md2wechat-skill](https://github.com/xiangzhouEcho/Echo-md2wechat-skill) — Markdown 排版发布到公众号（内联样式 + 剪贴板 + 草稿 API）

## License

MIT © xiangzhouEcho
