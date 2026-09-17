from __future__ import annotations

import random
import re
import time
from datetime import datetime, timezone
from urllib.parse import quote

import requests
from bs4 import BeautifulSoup

DESKTOP_UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
)
BASE = "https://weixin.sogou.com"
TSN = {"day": 1, "week": 2, "month": 3, "year": 4}


class AntiSpider(Exception):
    pass


def build_session() -> requests.Session:
    s = requests.Session()
    s.headers.update(
        {
            "User-Agent": DESKTOP_UA,
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Referer": BASE + "/",
        }
    )
    try:
        s.get(BASE + "/", timeout=20)
    except requests.RequestException:
        pass
    return s


def _check_antispider(resp: requests.Response) -> None:
    if "antispider" in resp.url or "/antispider/" in resp.text or "seccodeInput" in resp.text:
        raise AntiSpider("搜狗反爬触发（antispider/验证码），请降低频率、稍后重试或更换网络")


def search(
    keyword: str,
    page: int = 1,
    session: requests.Session | None = None,
    time_range: str | None = None,
) -> list[dict]:
    session = session or build_session()
    params = {"type": "2", "query": keyword, "page": str(page), "ie": "utf8"}
    if time_range in TSN:
        params["tsn"] = str(TSN[time_range])
    resp = session.get(BASE + "/weixin", params=params, timeout=30)
    _check_antispider(resp)
    resp.encoding = "utf-8"
    return _parse_results(resp.text)


def _clean_text(el) -> str:
    if el is None:
        return ""
    for em in el.find_all("em"):
        em.unwrap()
    return el.get_text("", strip=True)


def _first_text(node, selector: str) -> str:
    return _clean_text(node.select_one(selector))


def _parse_results(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "lxml")
    out = []
    for li in soup.select("li[id^=sogou_vr_]"):
        a = li.select_one(".txt-box h3 a")
        if not a:
            continue
        href = a.get("href", "")
        link = href if href.startswith("http") else BASE + href
        sp = li.select_one(".s-p")
        account = ""
        if sp:
            span = sp.find("span")
            account = span.get_text(strip=True) if span else ""
        m = re.search(r"timeConvert\('(\d+)'\)", str(li))
        date = ""
        if m:
            date = datetime.fromtimestamp(int(m.group(1)), tz=timezone.utc).astimezone().strftime("%Y-%m-%d")
        img = li.select_one(".img-box img")
        thumb = ""
        if img:
            thumb = img.get("data-src") or img.get("src") or ""
            if thumb.startswith("//"):
                thumb = "https:" + thumb
        out.append(
            {
                "title": _clean_text(a),
                "account": account,
                "date": date,
                "summary": _first_text(li, ".txt-box .txt-info"),
                "thumbnail": thumb,
                "sogou_link": link,
                "url": "",
                "resolved": False,
            }
        )
    return out


def polite_sleep(delay: float) -> None:
    if delay > 0:
        time.sleep(delay + random.uniform(0, delay * 0.4))


def search_pages(keyword: str, pages: int = 1, delay: float = 3.0, time_range: str | None = None) -> list[dict]:
    session = build_session()
    results: list[dict] = []
    for p in range(1, pages + 1):
        try:
            batch = search(keyword, page=p, session=session, time_range=time_range)
        except AntiSpider:
            if not results:
                raise
            break
        if not batch:
            break
        results.extend(batch)
        if p < pages:
            polite_sleep(delay)
    return _dedupe(results)


def _dedupe(results: list[dict]) -> list[dict]:
    seen = set()
    out = []
    for r in results:
        key = (r["title"], r["account"])
        if key in seen:
            continue
        seen.add(key)
        out.append(r)
    return out
