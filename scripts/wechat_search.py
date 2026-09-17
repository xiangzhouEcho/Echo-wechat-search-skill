# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "requests",
#   "beautifulsoup4",
#   "lxml",
# ]
# ///
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

import sogou

WECHAT_DL = Path.home() / ".claude" / "skills" / "echo-wechat-skill" / "scripts" / "wechat_dl.py"


def _print_table(results, show_url):
    for i, r in enumerate(results, 1):
        link = r["url"] if (show_url and r["url"]) else r["sogou_link"]
        flag = "✓" if r["resolved"] else ("·" if show_url else "")
        print(f"[{i:2d}] {r['title']}")
        print(f"     {r['account']}  {r['date']}  {flag}")
        if r["summary"]:
            print(f"     {r['summary'][:70]}")
        print(f"     {link}")
        print()


def _download(results, formats, out, delay):
    urls = [r["url"] for r in results if r.get("resolved") and r["url"]]
    if not urls:
        print("没有可下载的真实链接（解析全部失败，可能被搜狗反爬限速；稍后重试或降低频率）", file=sys.stderr)
        return
    if not WECHAT_DL.is_file():
        print(f"未找到 echo-wechat-skill: {WECHAT_DL}", file=sys.stderr)
        return
    cmd = ["uv", "run", str(WECHAT_DL), *urls, "--format", formats, "--out", out, "--delay", str(delay)]
    print(f"\n调用 echo-wechat-skill 下载 {len(urls)} 篇 -> {out}\n")
    subprocess.run(cmd, check=False)


def main(argv=None):
    ap = argparse.ArgumentParser(
        prog="wechat_search.py",
        description="按关键词搜索微信公众号文章（搜狗）；可尽力解析成真实链接并调用 echo-wechat-skill 下载为 markdown。",
    )
    ap.add_argument("keyword", help="搜索关键词")
    ap.add_argument("--pages", type=int, default=1, help="搜索页数，每页约 10 条 (默认 1)")
    ap.add_argument("--time", choices=list(sogou.TSN), help="时间范围: day/week/month/year")
    ap.add_argument("--resolve", action="store_true", help="用系统 Chrome 尽力解析成真实文章链接")
    ap.add_argument("--download", action="store_true", help="解析后调用 echo-wechat-skill 下载 md (隐含 --resolve)")
    ap.add_argument("--format", default="md", help="下载格式，传给 wechat-skill: md,html,pdf (默认 md)")
    ap.add_argument("--out", default="./wechat-download", help="下载输出目录 (默认 ./wechat-download)")
    ap.add_argument("--limit", type=int, default=5, help="最多解析/下载多少条 (默认 5)")
    ap.add_argument("--delay", type=float, default=3.0, help="请求间隔秒数 (默认 3)")
    ap.add_argument("--json", action="store_true", help="以 JSON 输出结果")
    args = ap.parse_args(argv)

    try:
        results = sogou.search_pages(args.keyword, pages=args.pages, delay=args.delay, time_range=args.time)
    except sogou.AntiSpider as exc:
        print(f"搜索失败: {exc}", file=sys.stderr)
        raise SystemExit(3)

    if not results:
        print("没有搜到结果", file=sys.stderr)
        raise SystemExit(0)

    want_resolve = args.resolve or args.download
    if want_resolve:
        import resolve as resolver
        session = sogou.build_session()
        resolver.resolve_results(results, session, delay=max(args.delay, 2.0), limit=args.limit)

    if args.json:
        print(json.dumps(results, ensure_ascii=False, indent=2))
    else:
        print(f"\n关键词「{args.keyword}」共 {len(results)} 条：\n")
        _print_table(results, show_url=want_resolve)

    if args.download:
        _download(results, args.format, args.out, args.delay)


if __name__ == "__main__":
    main()
