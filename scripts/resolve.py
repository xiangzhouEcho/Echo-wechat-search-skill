from __future__ import annotations

import re
import time

import requests

from sogou import DESKTOP_UA

_FRAG = re.compile(r"url \+= '([^']*)'")
_MSG_LINK = re.compile(r'var\s+msg_link\s*=\s*"([^"]*)"')
_OG_URL = re.compile(r'property="og:url"\s+content="([^"]*)"')


def _clean_url(u: str) -> str:
    u = u.replace("&amp;", "&").replace("\\x26", "&")
    if u.startswith("http://"):
        u = "https://" + u[len("http://"):]
    return u.split("#")[0]


def reconstruct_src11(link_page_html: str) -> str:
    parts = _FRAG.findall(link_page_html)
    if not parts:
        return ""
    url = "".join(parts).replace("&amp;", "&")
    return url if "mp.weixin.qq.com" in url else ""


def _extract_canonical(article_html: str) -> str:
    m = _MSG_LINK.search(article_html)
    if m and m.group(1):
        return _clean_url(m.group(1))
    m = _OG_URL.search(article_html)
    if m and m.group(1):
        return _clean_url(m.group(1))
    return ""


def resolve_one(sogou_link: str, session: requests.Session) -> str:
    headers = {"User-Agent": DESKTOP_UA, "Referer": "https://weixin.sogou.com/weixin?type=2"}
    lr = session.get(sogou_link, headers=headers, timeout=25)
    if "antispider" in lr.url or "antispider" in lr.text:
        raise RuntimeError("antispider")
    src11 = reconstruct_src11(lr.text)
    if not src11:
        return ""
    ar = session.get(src11, headers={"User-Agent": DESKTOP_UA, "Referer": "https://weixin.sogou.com/"}, timeout=30)
    ar.encoding = "utf-8"
    h = ar.text
    if 'id="js_content"' not in h and 'id="js_article"' not in h:
        return ""
    return _extract_canonical(h)


def resolve_results(results, session, delay: float = 2.0, limit: int = 0):
    todo = [r for r in results if not r.get("url")]
    if limit and limit > 0:
        todo = todo[:limit]
    for i, r in enumerate(todo):
        try:
            url = resolve_one(r["sogou_link"], session)
        except RuntimeError as exc:
            if str(exc) == "antispider":
                break
            url = ""
        except requests.RequestException:
            url = ""
        if url:
            r["url"] = url
            r["resolved"] = True
        if i < len(todo) - 1:
            time.sleep(delay + delay * 0.3)
    return results
