#!/usr/bin/env python3
"""Add articles rendered from i18n/articles/ to the zh-Hans (/blog/) and en (/blog/en/) hubs and feeds.

Idempotent: a card already present (by href) is not added twice. Updates the article count,
the Blog JSON-LD blogPost list and the RSS feeds (/blog/feed.xml, /blog/en/feed.xml).
"""
import html
import json
import os
import re
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(__file__))
from articles import ART, parse, url_for, article_langs  # noqa: E402
from site_config import SITE  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HUB = {"zh-Hans": ("blog/index.html", "blog/feed.xml", "{n} 篇文章", "分钟阅读"), "en": ("blog/en/index.html", "blog/en/feed.xml", "{n} articles", "min read")}
E = html.escape


def new_articles():
    out = []
    for slug in sorted(os.listdir(ART)):
        meta = json.load(open(os.path.join(ART, slug, "meta.json"), encoding="utf-8"))
        hls = article_langs(slug)
        out.append((meta, slug, {h: url_for(slug, h, meta) for h in hls}))
    out.sort(key=lambda x: x[0]["published"], reverse=True)
    return out


def hub_card(meta, d, url, alt, read_label):
    return ('<a class="card" href="%s" data-cat="%s">\n        <div class="im"><picture><source type="image/webp" srcset="/assets/blog/hero/%s-768.webp">'
            '<img src="/assets/blog/hero/%s.jpg" alt="%s" width="1536" height="1024" loading="lazy"></picture></div>\n'
            '        <div class="tx"><div class="eyebrow">%s</div><h3>%s</h3><p>%s</p><div class="meta"><span>%s %s</span></div></div>\n      </a>\n'
            % (url, meta["cat"], meta["hero"], meta["hero"], E(alt, quote=True), E(d["section"]), E(d["title"]), E(d["dek"]), d["read"], read_label))


def rfc822(iso):
    dt = datetime.fromisoformat(iso)
    return dt.strftime("%a, %d %b %Y %H:%M:%S %z")


def main():
    arts = new_articles()
    for hl, (hub, feed, count_fmt, read_label) in HUB.items():
        p = os.path.join(ROOT, hub)
        s = open(p, encoding="utf-8").read()
        cards, posts, items = [], [], []
        for meta, slug, versions in arts:
            if hl not in versions:
                continue
            url = versions[hl]
            d = parse(os.path.join(ART, slug, hl + ".txt"))
            page = open(os.path.join(ROOT, url.strip("/"), "index.html"), encoding="utf-8").read()
            alt = html.unescape(re.search(r'<figure class="hero-fig">.*?alt="([^"]*)"', page, re.S).group(1))
            if 'href="%s"' % url not in s:
                cards.append(hub_card(meta, d, url, alt, read_label))
            if '"url":"%s%s"' % (SITE, url) not in s:
                posts.append('{"@type":"BlogPosting","headline":%s,"url":"%s%s","inLanguage":"%s"}' % (json.dumps(d["title"], ensure_ascii=False), SITE, url, hl))
            items.append((url, d, meta))
        if cards:
            s = s.replace('<div class="grid" id="cards">\n', '<div class="grid" id="cards">\n      ' + "      ".join(cards), 1)
        if posts:
            s = re.sub(r'("@type":"Blog".*?"blogPost":\[)', lambda m: m.group(1) + ",".join(posts) + ",", s, count=1, flags=re.S)
        total = len(re.findall(r'<a class="(?:card|feat)[^"]*" href=', s))
        s = re.sub(r"\b\d+ 篇文章" if hl == "zh-Hans" else r"\b\d+ articles", count_fmt.format(n=total), s)
        open(p, "w", encoding="utf-8").write(s)
        # feed
        fp = os.path.join(ROOT, feed)
        f = open(fp, encoding="utf-8").read()
        new_items = []
        for url, d, meta in items:
            if "<link>%s%s</link>" % (SITE, url) in f:
                continue
            new_items.append("<item>\n<title>%s</title>\n<link>%s%s</link>\n<guid isPermaLink=\"true\">%s%s</guid>\n<description>%s</description>\n<category>%s</category>\n<pubDate>%s</pubDate>\n</item>\n"
                             % (E(d["title"]), SITE, url, SITE, url, E(d["desc"]), E(d["section"]), rfc822(meta["published"])))
        if new_items:
            f = f.replace("<item>", "".join(new_items) + "<item>", 1)
            f = re.sub(r"<lastBuildDate>[^<]*</lastBuildDate>", "<lastBuildDate>%s</lastBuildDate>" % rfc822(arts[0][0]["published"]), f, count=1)
            open(fp, "w", encoding="utf-8").write(f)
        print(hl, "hub cards added:", len(cards), "total", total, "feed items added:", len(new_items))


if __name__ == "__main__":
    main()
