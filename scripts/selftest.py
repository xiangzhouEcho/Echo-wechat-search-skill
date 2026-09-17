# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "requests",
#   "beautifulsoup4",
#   "lxml",
# ]
# ///
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import resolve
import sogou

FIXTURE = """
<ul class="news-list">
<li id="sogou_vr_11002601_box_0">
  <div class="img-box"><a><img src="//img.sogou.com/thumb0.jpg"></a></div>
  <div class="txt-box">
    <h3><a href="/link?url=ABC123def&type=2&query=%E6%B5%8B%E8%AF%95&token=TK">
      <em>厄尔尼诺</em>到来基本已成定局</a></h3>
    <p class="txt-info">这是<em>厄尔尼诺</em>相关的摘要文本内容示例。</p>
    <div class="s-p" data-isv="0">
      <span class="all-time-y2">果壳</span>
      <span class="s2"><script>document.write(timeConvert('1686196812'))</script></span>
    </div>
  </div>
</li>
<li id="sogou_vr_11002601_box_1">
  <div class="img-box"><a><img data-src="//img.sogou.com/thumb1.jpg"></a></div>
  <div class="txt-box">
    <h3><a href="/link?url=XYZ789ghi&type=2">第二篇<em>测试</em>文章</a></h3>
    <p class="txt-info">第二条摘要。</p>
    <div class="s-p"><span class="all-time-y2">中国国家地理</span>
      <span class="s2"><script>document.write(timeConvert('1700000000'))</script></span></div>
  </div>
</li>
</ul>
"""


def check(cond, msg):
    if not cond:
        raise AssertionError(msg)
    print(f"  ok: {msg}")


def main():
    res = sogou._parse_results(FIXTURE)
    check(len(res) == 2, f"解析出 2 条, got {len(res)}")
    r0 = res[0]
    check(r0["title"] == "厄尔尼诺到来基本已成定局", "标题去除 <em> 高亮空格")
    check(r0["account"] == "果壳", "公众号名解析")
    check(r0["date"] == "2023-06-08", f"日期由 epoch 转换, got {r0['date']}")
    check(r0["summary"] == "这是厄尔尼诺相关的摘要文本内容示例。", "摘要去除 <em>")
    check(r0["sogou_link"].startswith("https://weixin.sogou.com/link?url=ABC123"), "搜狗跳转链接补全域名")
    check(r0["thumbnail"] == "https://img.sogou.com/thumb0.jpg", "缩略图补全协议")
    check(r0["url"] == "" and r0["resolved"] is False, "初始未解析")
    check(res[1]["account"] == "中国国家地理", "第二条公众号名")

    dup = sogou._dedupe(res + [dict(res[0])])
    check(len(dup) == 2, "按标题+公众号去重")

    frag_page = "a.href='';url += 'https://mp.';url += 'weixin.qq.c';url += 'om/s?src=11';url += '&timestamp=';url += '1&ver=6&sig';"
    src11 = resolve.reconstruct_src11(frag_page)
    check(src11 == "https://mp.weixin.qq.com/s?src=11&timestamp=1&ver=6&sig", f"src11 拼接正确(不误伤 &timestamp), got {src11}")
    check("×" not in src11 and "%C3%97" not in src11, "&timestamp 未被当作乘号实体解码")
    art = 'x<div id="js_content"></div>var msg_link = "http://mp.weixin.qq.com/s?__biz=Mz==&amp;mid=99&amp;idx=1&amp;sn=ab&amp;chksm=cd&amp;scene=27#wechat_redirect";'
    canon = resolve._extract_canonical(art)
    check(canon == "https://mp.weixin.qq.com/s?__biz=Mz==&mid=99&idx=1&sn=ab&chksm=cd&scene=27", f"从正文提取规范链接(带chksm), got {canon}")
    canon2 = resolve._extract_canonical('<meta property="og:url" content="https://mp.weixin.qq.com/s/ABC"> id="js_content"')
    check(canon2 == "https://mp.weixin.qq.com/s/ABC", "og:url 兜底提取")

    import wechat_search
    check(wechat_search.WECHAT_DL.name == "wechat_dl.py", "下载指向 echo-wechat-skill 的 wechat_dl.py")
    check("echo-wechat-skill" in str(wechat_search.WECHAT_DL), "下载路径指向 echo-wechat-skill")

    print("\nselftest: ALL PASS")


if __name__ == "__main__":
    main()
