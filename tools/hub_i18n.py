#!/usr/bin/env python3
"""Render /blog/<code>/ hubs from the English hub (/blog/en/) for every further site language.

Chrome text comes from i18n/ui.json (article chrome) and i18n/pages.json["hub"] translated through
i18n/<code>.json. Cards link to the article in that language when it exists, otherwise to the
English version (marked lang="en" with an "English" badge).
"""
import html
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(__file__))
from site_config import L, ORDER, SITE, page_url, CODE2HL, NEW_LANGS  # noqa: E402
from registry import registry  # noqa: E402
from localize import load_tm, sid, PAGES, coverage, MIN_COVERAGE  # noqa: E402
import langmenu  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UI = json.load(open(os.path.join(ROOT, "i18n", "ui.json"), encoding="utf-8"))
E = html.escape


def hub_versions():
    v = {"zh-Hans": "/blog/", "en": "/blog/en/"}
    for hl in NEW_LANGS:
        if os.path.exists(os.path.join(ROOT, "blog", L[hl]["code"], "index.html")):
            v[hl] = page_url("hub", hl)
    return v


def render(hl):
    code = L[hl]["code"]
    tm = load_tm(code)
    u = UI[hl]
    H = {k: tm.get(sid(v), v) for k, v in PAGES["hub"].items()}
    reg = registry()
    by_en = {}
    for slug, e in reg.items():
        for h, p in e["versions"].items():
            by_en[p] = e
    src = open(os.path.join(ROOT, "blog/en/index.html"), encoding="utf-8").read()
    path = page_url("hub", hl)
    url = SITE + path
    n_local = 0

    def card(m):
        nonlocal n_local
        whole, href = m.group(0), m.group(2)
        e = by_en.get(href)
        if not e:
            return whole
        pg = e["pages"].get(hl)
        whole = re.sub(r'(<div class="eyebrow">)[^<]*(</div>)', lambda mm: mm.group(1) + E(u["cats"].get(pg["cat"] if pg else e["pages"]["en"]["cat"], mm.group(0)[22:-6])) + mm.group(2), whole, count=1)
        whole = re.sub(r"(<span>)(\d+) min read(</span>)", lambda mm: mm.group(1) + u["read"].format(n=mm.group(2)) + mm.group(3), whole)
        if pg:
            n_local += 1
            whole = whole.replace('href="%s"' % href, 'href="%s"' % pg["path"], 1)
            whole = re.sub(r"(<h[23]>).*?(</h[23]>)", lambda mm: mm.group(1) + E(pg["title"]) + mm.group(2), whole, count=1, flags=re.S)
            whole = re.sub(r'(<div class="tx">.*?</h[23]><p>).*?(</p>)', lambda mm: mm.group(1) + E(pg["dek"]) + mm.group(2), whole, count=1, flags=re.S)
            whole = whole.replace('<div class="tx">', '<div class="tx" lang="%s">' % hl, 1)
        else:
            whole = whole.replace('<div class="tx">', '<div class="tx" lang="en" dir="ltr">', 1)
            whole = re.sub(r'(<div class="meta">)', r'\1<span class="lg">English</span>', whole, count=1)
        return whole

    body = src[src.find("<body>"):]
    head = src[:src.find("<body>")]
    body = re.sub(r'<a class="(card|feat)"[^>]*href="([^"]+)"[^>]*>.*?</a>', card, body, flags=re.S)

    # series list
    def series(m):
        href = m.group(1)
        e = by_en.get(href)
        pg = e["pages"].get(hl) if e else None
        if pg:
            return '<li><a href="%s">%s</a></li>' % (pg["path"], E(pg["title"]))
        return '<li><a href="%s" lang="en" dir="ltr">%s</a></li>' % (href, m.group(2))
    body = re.sub(r'<li><a href="([^"]+)">(.*?)</a></li>', series, body)

    total = len(re.findall(r'<a class="(?:card|feat)', body))
    rep = [
        ('<a class="skip" href="#main">On this page</a>', '<a class="skip" href="#main">%s</a>' % E(u["skip"])),
        ('<a href="/?lang=en">Home</a>', '<a href="%s">%s</a>' % (page_url("home", hl), E(u["home"]))),
        ('<a href="/?lang=en#products">Products</a>', '<a href="%s#products">%s</a>' % (page_url("home", hl), E(u["products"]))),
        ('<a href="/?lang=en#faq">FAQ</a>', '<a href="%s#faq">%s</a>' % (page_url("home", hl), E(u["faq_nav"]))),
        ('<a href="/pro/?lang=en">ToucHigh PRO</a>', '<a href="%s">ToucHigh PRO</a>' % page_url("pro", hl)),
        ('<a href="/blog/en/" class="on">Blog</a>', '<a href="%s" class="on">%s</a>' % (path, E(u["blog"]))),
        ('>Log in</a>', '>%s</a>' % E(u["login"])),
        ('>Book a call</a>', '>%s</a>' % E(u["book"])),
        ('<a href="/?lang=en">Home</a><span>/</span><span>Blog</span>', '<a href="%s">%s</a><span>/</span><span>%s</span>' % (page_url("home", hl), E(u["home"]), E(u["blog"]))),
        ('<h1>Growth notes on SEO, GEO and social for brands going global</h1>', "<h1>%s</h1>" % E(H["h1"])),
        ('aria-label="Topic"', 'aria-label="%s"' % E(H["topic"])),
        ('<button class="chip on" data-v="all">All topics</button>', '<button class="chip on" data-v="all">%s</button>' % E(H["all_topics"])),
        ('>Series · Going global<', ">%s<" % E(H["series_eyebrow"])),
        ('<h2>SEO, AEO, GEO and thought leadership for Chinese factories and e-commerce brands</h2>', "<h2>%s</h2>" % E(H["series_title"])),
        ('aria-label="SEO, AEO, GEO and thought leadership for Chinese factories and e-commerce brands"', 'aria-label="%s"' % E(H["series_title"])),
        ("<p>Ten pieces on getting found — and trusted — by overseas buyers who now research with AI.</p>", "<p>%s</p>" % E(H["series_desc"])),
        ("<h2>See where you&#39;re invisible in US AI search</h2>", "<h2>%s</h2>" % E(u["side"])),
        ("<p>Book a free 30-minute call and we&#39;ll run a live AI-visibility read on your store.</p>", "<p>%s</p>" % E(u["final_p"])),
        (">Book a 30-min strategy call →</a>", ">%s</a>" % E(u["book30"])),
        (">Log in to ToucHigh</a>", ">%s</a>" % E(u["login_th"])),
        ("AI search visibility, social and ads on autopilot — for SMEs and cross-border sellers.", E(u["tagline"])),
        ('<a href="/">Home</a>', '<a href="%s">%s</a>' % (page_url("home", hl), E(u["home"]))),
        ('<a href="/#geo">', '<a href="%s#geo">' % page_url("home", hl)),
        ('<a href="/#social">', '<a href="%s#social">' % page_url("home", hl)),
        ('<a href="/pro/">ToucHigh PRO</a>', '<a href="%s">ToucHigh PRO</a>' % page_url("pro", hl)),
        ("<div><h4>Blog</h4><a href=\"/blog/en/\">Blog</a><a href=\"/blog/en/feed.xml\">RSS</a>", "<div><h4>%s</h4><a href=\"%s\">%s</a>" % (E(u["blog"]), path, E(u["blog"]))),
        ("<div><h4>Log in</h4>", "<div><h4>%s</h4>" % E(u["login"])),
    ]
    for a_, b_ in rep:
        body = body.replace(a_, b_)
    for k, v in json.load(open(os.path.join(ROOT, "i18n", "ui.json"), encoding="utf-8"))["en"]["cats"].items():
        body = body.replace('data-v="%s">%s</button>' % (k, E(v)), 'data-v="%s">%s</button>' % (k, E(u["cats"][k])))
    body = re.sub(r'<div class="eyebrow">The ToucHigh blog · \d+ articles</div>', '<div class="eyebrow">%s</div>' % E(H["eyebrow"].format(n=total)), body)
    body = re.sub(r"(<section class=\"hub-hero\">.*?<h1>.*?</h1>\s*)<p>.*?</p>", lambda m: m.group(1) + "<p>%s</p>" % E(H["intro"]), body, count=1, flags=re.S)
    body = re.sub(r'<p class="hub-note">.*?</p>', '<p class="hub-note">%s</p>' % E(H["note"]), body, count=1, flags=re.S)

    # head
    title = H["title"]
    desc = H["description"]
    head = re.sub(r'<html lang="en">', '<html lang="%s"%s>' % (hl, ' dir="rtl"' if L[hl]["dir"] == "rtl" else ""), head, count=1)
    head = re.sub(r"<title>.*?</title>", "<title>%s</title>" % E(title), head, count=1)
    for attr, k, v in (("name", "description", desc), ("property", "og:url", url), ("property", "og:title", title), ("property", "og:description", desc),
                       ("property", "og:image:alt", title), ("property", "og:locale", L[hl]["locale"]), ("name", "twitter:title", title),
                       ("name", "twitter:description", desc), ("name", "twitter:image:alt", title)):
        head = re.sub(r'(<meta %s="%s" content=")[^"]*(")' % (attr, re.escape(k)), lambda m: m.group(1) + E(v, quote=True) + m.group(2), head, count=1)
    head = head.replace('<link rel="canonical" href="https://touchigh.ai/blog/en/">', '<link rel="canonical" href="%s">' % url)
    head = head.replace('<link rel="alternate" type="application/rss+xml" title="ToucHigh Blog" href="/blog/en/feed.xml">\n', "")
    posts = [{"@type": "BlogPosting", "headline": e["pages"][hl]["title"], "url": SITE + e["pages"][hl]["path"], "inLanguage": hl}
             for e in reg.values() if hl in e["pages"]]
    blog = {"@context": "https://schema.org", "@type": "Blog", "@id": url + "#blog", "url": url, "name": u["blog_name"], "description": desc,
            "inLanguage": hl, "publisher": {"@id": SITE + "/#org"}, "translationOfWork": {"@id": SITE + "/blog/#blog"}}
    if posts:
        blog["blogPost"] = posts
    crumbs = {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": 1, "name": "ToucHigh", "item": SITE + page_url("home", hl)},
        {"@type": "ListItem", "position": 2, "name": u["blog"], "item": url}]}
    head = re.sub(r'<script type="application/ld\+json">.*?</script>\s*', "", head, flags=re.S)
    fam = {"zh-Hant": "Noto+Sans+TC", "ja": "Noto+Sans+JP", "ko": "Noto+Sans+KR", "th": "Noto+Sans+Thai", "hi": "Noto+Sans+Devanagari", "ar": "Noto+Sans+Arabic"}.get(hl)
    if fam:
        head = head.replace("family=Inter:wght@400;500;600;700;800;900&display=swap", "family=Inter:wght@400;500;600;700;800;900&family=%s:wght@400;500;700;800&display=swap" % fam)
    head = head.replace("</head>", "")
    head += "\n".join('<script type="application/ld+json">%s</script>' % json.dumps(b, ensure_ascii=False, separators=(",", ":")) for b in (blog, crumbs))
    head += '\n<link rel="stylesheet" href="/assets/css/blog-extra.css">\n</head>\n'
    ogi = "/assets/blog/og/hub-%s.jpg" % code
    if os.path.exists(os.path.join(ROOT, ogi.lstrip("/"))):
        head = head.replace("https://touchigh.ai/assets/blog/og/hub-en.jpg", SITE + ogi)
    out = head + body
    vers = hub_versions()
    vers[hl] = path
    out = langmenu.apply(out, hl, vers)
    f = os.path.join(ROOT, "blog", code, "index.html")
    os.makedirs(os.path.dirname(f), exist_ok=True)
    open(f, "w", encoding="utf-8").write(out)
    print("hub", code, "cards:", total, "in language:", n_local)


if __name__ == "__main__":
    codes = sys.argv[1:] or [L[h]["code"] for h in NEW_LANGS]
    for c in codes:
        hl = CODE2HL[c]
        if coverage(c)[0] < MIN_COVERAGE or hl not in UI or "cats" not in UI[hl]:
            print("hub", c, "skipped (translations incomplete)")
            continue
        render(hl)
