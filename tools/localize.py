#!/usr/bin/env python3
"""Render the bilingual pages (home, /pro/, the two landing pages) into every other site language.

Source of truth = the zh-Hans/English page itself: every element with data-en / data-en-html is one
segment (its English value), plus img alt / aria-label / the demo captions, plus the head metadata in
i18n/pages.json. Translations live in i18n/<code>.json keyed by segment id (sha1 of the English text).
Output: /<code>/, /<code>/pro/, /<code>/supplier-ai-visibility/, /<code>/amazon-ads-autopilot/.

  python3 tools/localize.py todo <code>      # print "id<TAB>English" for untranslated segments
  python3 tools/localize.py merge <code> f   # merge a "id<TAB>translation" file into i18n/<code>.json
  python3 tools/localize.py build [codes]    # render pages (only languages at >= MIN_COVERAGE)
"""
import hashlib
import html
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(__file__))
from site_config import L, ORDER, NEW_LANGS, SITE, STATIC_PAGES, page_url, CODE2HL  # noqa: E402
import langmenu  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
I18N = os.path.join(ROOT, "i18n")
MIN_COVERAGE = 0.97
PAGES = json.load(open(os.path.join(I18N, "pages.json"), encoding="utf-8"))
SRC_FILE = {"home": "index.html", "pro": "pro/index.html", "supplier": "supplier-ai-visibility/index.html", "amazon": "amazon-ads-autopilot/index.html"}
FONTS = {"zh-Hant": "Noto+Sans+TC", "ja": "Noto+Sans+JP", "ko": "Noto+Sans+KR", "th": "Noto+Sans+Thai", "hi": "Noto+Sans+Devanagari", "ar": "Noto+Sans+Arabic"}
FONT_CSS = {"zh-Hant": "'Noto Sans TC'", "ja": "'Noto Sans JP'", "ko": "'Noto Sans KR'", "th": "'Noto Sans Thai'", "hi": "'Noto Sans Devanagari'", "ar": "'Noto Sans Arabic'"}


def sid(text):
    return hashlib.sha1(text.encode("utf-8")).hexdigest()[:10]


def load_tm(code):
    p = os.path.join(I18N, code + ".json")
    return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else {}


# ------------------------------------------------------------------ segment extraction
_START = re.compile(r"<([a-zA-Z][a-zA-Z0-9]*)(\s[^<>]*?)?(/?)>")
_ATTR = re.compile(r'([a-zA-Z_:][-a-zA-Z0-9_:.]*)\s*=\s*"([^"]*)"')


def attrs_of(s):
    return {k: html.unescape(v) for k, v in _ATTR.findall(s or "")}


def find_close(src, tag, pos):
    """Index of the matching </tag> for an element whose content starts at pos."""
    depth, i = 1, pos
    rx = re.compile(r"<(/?)%s\b[^>]*>" % tag, re.I)
    while True:
        m = rx.search(src, i)
        if not m:
            return -1, -1
        if m.group(1):
            depth -= 1
            if depth == 0:
                return m.start(), m.end()
        elif not m.group(0).endswith("/>"):
            depth += 1
        i = m.end()


def body_segments(src):
    segs = []
    for m in _START.finditer(src):
        a = attrs_of(m.group(2))
        for k in ("data-en", "data-en-html"):
            if k in a and a[k].strip():
                segs.append(a[k])
        for k in ("alt", "aria-label", "title"):
            if k in a and a[k].strip() and re.search(r"[A-Za-z]{3}", a[k]) and m.group(1).lower() not in ("link", "meta", "html"):
                if a[k] not in ("ToucHigh", "Menu", "Primary", "Language"):
                    segs.append(a[k])
    return segs


def demo_segments(src):
    return [html.unescape(x) for x in re.findall(r"\ben:'((?:[^'\\]|\\.)*)'", src)]


def page_segments(page):
    src = open(os.path.join(ROOT, SRC_FILE[page]), encoding="utf-8").read()
    body = src[src.find("<body"):]
    segs = list(PAGES[page].values()) + body_segments(body) + demo_segments(body)
    seen, out = set(), []
    for s in segs:
        if s not in seen and re.search(r"[A-Za-z]", s):
            seen.add(s)
            out.append(s)
    return out


def all_segments():
    out, seen = [], set()
    for page in SRC_FILE:
        for s in page_segments(page):
            if s not in seen:
                seen.add(s)
                out.append((page, s))
    for s in PAGES.get("hub", {}).values():
        if s not in seen:
            seen.add(s)
            out.append(("hub", s))
    return out


# ------------------------------------------------------------------ URL mapping
def blog_versions():
    from registry import registry
    reg = registry()
    out = {}
    for slug, e in reg.items():
        for hl, p in e["versions"].items():
            out[p] = (slug, e["versions"])
    return out


_BV = None


def map_path(path, hl):
    """Map a zh-Hans/English site path to the equivalent path in language hl (falls back to English)."""
    global _BV
    if not path.startswith("/") or path.startswith("//"):
        return path
    base, frag = (path.split("#", 1) + [""])[:2]
    frag = ("#" + frag) if frag else ""
    base = base.split("?")[0]
    for page, p in STATIC_PAGES.items():
        if base == p:
            return page_url(page, hl) + frag
    if base in ("/blog/", "/blog/en/"):
        return page_url("hub", hl) + frag
    if base.startswith("/blog/"):
        if _BV is None:
            _BV = blog_versions()
        if base in _BV:
            slug, vers = _BV[base]
            return (vers.get(hl) or vers.get("en") or base) + frag
    return path


def static_versions(page):
    return {hl: page_url(page, hl) for hl in ORDER if hl in ("zh-Hans", "en") or os.path.exists(os.path.join(ROOT, L[hl]["code"], STATIC_PAGES[page].strip("/"), "index.html"))}


# ------------------------------------------------------------------ rendering
def tr(tm, text):
    return tm.get(sid(text))


def localize_body(body, hl, tm, missing):
    out, i = [], 0
    for m in _START.finditer(body):
        if m.start() < i:
            continue
        tag, raw = m.group(1), m.group(2) or ""
        a = attrs_of(raw)
        newraw = raw
        # attributes
        for k in ("alt", "aria-label", "title"):
            if k in a and a[k] in seg_set:
                t = tr(tm, a[k])
                if t is None:
                    missing.add(a[k])
                else:
                    newraw = re.sub(r'(\s%s=")[^"]*(")' % k, lambda mm: mm.group(1) + html.escape(t, quote=True) + mm.group(2), newraw, count=1)
        for k in ("href", "data-href-zh"):
            if k in a and a[k].startswith("/"):
                pass
        if "data-href-zh" in a:
            target = map_path(a["data-href-zh"], hl)
            newraw = re.sub(r'\shref="[^"]*"', ' href="%s"' % target, newraw, count=1)
            newraw = re.sub(r'\sdata-href-(zh|en)="[^"]*"', "", newraw)
        elif "href" in a and a["href"].startswith("/") and tag.lower() == "a":
            newraw = re.sub(r'\shref="[^"]*"', ' href="%s"' % map_path(a["href"], hl), newraw, count=1)
        content_key = "data-en-html" if "data-en-html" in a else ("data-en" if "data-en" in a else None)
        if content_key:
            en = a[content_key]
            t = tr(tm, en)
            if t is None:
                missing.add(en)
                t = en
                if content_key == "data-en":
                    t = html.escape(t, quote=False)
            elif content_key == "data-en":
                t = html.escape(t, quote=False)
            newraw = re.sub(r'\sdata-(en|zh)(-html)?="[^"]*"', "", newraw)
            cs, ce = find_close(body, tag, m.end())
            out.append(body[i:m.start()])
            out.append("<%s%s%s>%s" % (tag, newraw, m.group(3), t))
            out.append(body[cs:ce])
            i = ce
            continue
        out.append(body[i:m.start()])
        out.append("<%s%s%s>" % (tag, newraw, m.group(3)))
        i = m.end()
    out.append(body[i:])
    return "".join(out)


seg_set = set()


def jsonld_for(page, hl, tm, url, src):
    """Translated JSON-LD built from the localized visible content (FAQ, steps) + page metadata."""
    P = {k: (tr(tm, v) or v) for k, v in PAGES[page].items()}
    blocks = []
    blocks.append({"@context": "https://schema.org", "@type": "WebPage", "@id": url + "#webpage", "url": url, "name": P["title"],
                   "description": P["description"], "inLanguage": hl, "isPartOf": {"@id": SITE + "/#website"},
                   "about": {"@id": SITE + "/#org"}, "primaryImageOfPage": SITE + "/og-cover-en.jpg",
                   "speakable": {"@type": "SpeakableSpecification", "cssSelector": [".hero h1", ".hero .lead"]}})
    faq = re.findall(r"<details[^>]*>\s*<summary[^>]*>(.*?)</summary>\s*<p[^>]*>(.*?)</p>\s*</details>", src, re.S)
    if faq:
        blocks.append({"@context": "https://schema.org", "@type": "FAQPage", "@id": url + "#faq", "inLanguage": hl, "mainEntity": [
            {"@type": "Question", "name": html.unescape(re.sub(r"<[^>]+>", "", q)).strip(),
             "acceptedAnswer": {"@type": "Answer", "text": html.unescape(re.sub(r"<[^>]+>", "", a_)).strip()}} for q, a_ in faq]})
    crumbs = [{"@type": "ListItem", "position": 1, "name": "ToucHigh", "item": SITE + page_url("home", hl)}]
    if page != "home":
        crumbs.append({"@type": "ListItem", "position": 2, "name": P.get("crumb", P["title"]), "item": url})
    else:
        crumbs.append({"@type": "ListItem", "position": 2, "name": P.get("crumb_blog", "Blog"), "item": SITE + page_url("hub", hl)})
    blocks.append({"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": crumbs})
    if "service" in P:
        blocks.append({"@context": "https://schema.org", "@type": "Service", "@id": url + "#service", "name": P.get("service_name", "ToucHigh"),
                       "description": P["service"], "provider": {"@id": SITE + "/#org"}, "url": url})
    if "howto_name" in P:
        steps = re.findall(r'<div class="step[^"]*"[^>]*>.*?<h3[^>]*>(.*?)</h3>\s*<p[^>]*>(.*?)</p>', src, re.S)
        if steps:
            blocks.append({"@context": "https://schema.org", "@type": "HowTo", "name": P["howto_name"], "inLanguage": hl, "step": [
                {"@type": "HowToStep", "position": i + 1, "name": html.unescape(re.sub(r"<[^>]+>", "", n)).strip(),
                 "text": html.unescape(re.sub(r"<[^>]+>", "", t)).strip()} for i, (n, t) in enumerate(steps)]})
    return "\n".join('<script type="application/ld+json">%s</script>' % json.dumps(b, ensure_ascii=False, separators=(",", ":")) for b in blocks)


EXTRA_CSS = """<style id="i18n-css">
body{font-family:'Inter',%s,system-ui,-apple-system,sans-serif}
html[lang="zh-Hant"] body,html[lang="ja"] body,html[lang="ko"] body,html[lang="th"] body,html[lang="hi"] body,html[lang="ar"] body{line-height:1.72}
html[lang="zh-Hant"] h1,html[lang="zh-Hant"] h2,html[lang="zh-Hant"] h3,html[lang="ja"] h1,html[lang="ja"] h2,html[lang="ja"] h3,html[lang="ko"] h1,html[lang="ko"] h2,html[lang="ko"] h3,html[lang="th"] h1,html[lang="th"] h2,html[lang="th"] h3,html[lang="hi"] h1,html[lang="hi"] h2,html[lang="hi"] h3,html[lang="ar"] h1,html[lang="ar"] h2,html[lang="ar"] h3{letter-spacing:0;line-height:1.3}
html[lang="zh-Hant"] .hero h1,html[lang="ja"] .hero h1,html[lang="ko"] .hero h1{font-size:clamp(30px,4.6vw,52px);letter-spacing:-.01em}
html[lang="de"] .hero h1,html[lang="fr"] .hero h1,html[lang="ru"] .hero h1,html[lang="es"] .hero h1,html[lang="pt"] .hero h1,html[lang="id"] .hero h1,html[lang="ms"] .hero h1,html[lang="fil"] .hero h1,html[lang="vi"] .hero h1,html[lang="hi"] .hero h1,html[lang="th"] .hero h1,html[lang="ar"] .hero h1{font-size:clamp(30px,4.3vw,50px)}
h1,h2,h3{overflow-wrap:break-word;hyphens:auto}
html[dir="rtl"] .nav-links{margin-left:0;margin-right:26px}html[dir="rtl"] .nav-right{margin-left:0;margin-right:auto}
html[dir="rtl"] .eyebrow,html[dir="rtl"] .eyebrow *{letter-spacing:0}
html[dir="rtl"] .checks li{text-align:right}
html[dir="rtl"] .faq summary::after{left:0;right:auto}
html[dir="rtl"] .tw th,html[dir="rtl"] .tw td{text-align:right}
html[dir="rtl"] .skip{left:auto;right:-999px}html[dir="rtl"] .skip:focus{right:0}
</style>"""


def render(page, hl, tm):
    code = L[hl]["code"]
    src = open(os.path.join(ROOT, SRC_FILE[page]), encoding="utf-8").read()
    missing = set()
    path = page_url(page, hl)
    url = SITE + path
    P = {}
    for k, v in PAGES[page].items():
        t = tr(tm, v)
        if t is None:
            missing.add(v)
        P[k] = t or v
    head, body = src[:src.find("</head>")], src[src.find("</head>"):]
    # --- head
    head = re.sub(r'<html lang="[^"]*"[^>]*>', '<html lang="%s"%s>' % (hl, ' dir="rtl"' if L[hl]["dir"] == "rtl" else ""), head, count=1)
    head = re.sub(r"<title>.*?</title>", "<title>%s</title>" % html.escape(P["title"], quote=False), head, count=1, flags=re.S)

    def meta(attr, name, val, h):
        return re.sub(r'(<meta %s="%s" content=")[^"]*(")' % (attr, re.escape(name)), lambda m: m.group(1) + html.escape(val, quote=True) + m.group(2), h, count=1)
    head = meta("name", "description", P["description"], head)
    head = meta("name", "keywords", P.get("keywords", ""), head)
    head = re.sub(r'<link rel="canonical" href="[^"]*">', '<link rel="canonical" href="%s">' % url, head, count=1)
    ogimg = "/assets/og/%s-%s.jpg" % (page, code)
    if not os.path.exists(os.path.join(ROOT, ogimg.lstrip("/"))):
        ogimg = "/og-cover-en.jpg"
    for k, v in (("og:url", url), ("og:title", P.get("og_title", P["title"])), ("og:description", P.get("og_description", P["description"])),
                 ("og:image", SITE + ogimg), ("og:image:alt", P.get("og_title", P["title"])), ("og:locale", L[hl]["locale"])):
        head = meta("property", k, v, head)
    head = re.sub(r'\s*<meta property="og:locale:alternate" content="[^"]*">', "", head)
    head = head.replace('<meta property="og:locale" content="%s">' % L[hl]["locale"],
                        '<meta property="og:locale" content="%s">\n' % L[hl]["locale"] + "\n".join('<meta property="og:locale:alternate" content="%s">' % L[h]["locale"] for h in ORDER if h != hl), 1)
    head = re.sub(r'\s*<meta property="og:video" content="[^"]*">', "", head)
    for k, v in (("twitter:title", P.get("og_title", P["title"])), ("twitter:description", P.get("og_description", P["description"])),
                 ("twitter:image", SITE + ogimg), ("twitter:image:alt", P.get("og_title", P["title"]))):
        head = meta("name", k, v, head)
    head = re.sub(r'<script type="application/ld\+json">.*?</script>\s*', "", head, flags=re.S)
    head = head.replace("<!-- ===================== END STRUCTURED DATA ===================== -->", "")
    head = re.sub(r"page_path:'[^']*'", "page_path:'%s'" % path, head)
    if hl in FONTS:
        head = head.replace("family=Noto+Sans+SC:wght@400;500;700;800;900", "family=%s:wght@400;500;700;800;900" % FONTS[hl])
    else:
        head = head.replace("&family=Noto+Sans+SC:wght@400;500;700;800;900", "")
    head = head.replace('<link rel="alternate" type="application/rss+xml" title="ToucHigh 博客" href="/blog/feed.xml">\n', "")
    # --- body
    global seg_set
    seg_set = set(page_segments(page))
    body = localize_body(body, hl, tm, missing)
    # Chinese-only names
    body = body.replace(">赵奎<", ">%s<" % ("趙奎" if hl == "zh-Hant" else ("趙奎" if hl == "ja" else "Zhao Kui")))
    # demo captions: use the translated caption for this language
    def demo(m):
        en = html.unescape(m.group(1))
        t = tr(tm, en)
        if t is None:
            missing.add(en)
            t = en
        return "en:'%s', loc:'%s'" % (m.group(1), t.replace("\\", "\\\\").replace("'", "\\'"))
    body = re.sub(r"\ben:'((?:[^'\\]|\\.)*)'", demo, body)
    body = body.replace("n.textContent=d[document.documentElement.lang==='en'?'en':'zh'];", "n.textContent=d.loc||d.en;")
    body = body.replace("n.setAttribute('data-en',d.en); n.setAttribute('data-zh',d.zh); ", "")
    # no client-side language switching on static language pages
    body = re.sub(r"if\(p==='en'\|\|p==='zh'\) setLang\(p\);\s*else if\(saved==='en'\) setLang\('en'\);\s*else setLang\('zh'\);",
                  "/* static %s page: no client-side language switch */" % hl, body)
    body = body.replace("var f=window.setLang;if(typeof f==='function'){window.setLang=function(l){f(l);sync();};}\n  sync();", "")
    # the source page sits at the site root: make relative asset paths absolute
    body = re.sub(r'(\s(?:src|poster|href)=")(?!/|#|https?:|mailto:|tel:|data:|javascript:)([^"]+)"', r'\1/\2"', body)
    # localized JSON-LD + CSS
    ld = jsonld_for(page, hl, tm, url, body)
    fam = FONT_CSS.get(hl, "'Noto Sans SC'")
    out = head + ld + "\n" + EXTRA_CSS % fam + "\n" + body
    versions = static_versions(page)
    versions[hl] = path
    out = langmenu.apply(out, hl, versions)
    return out, missing


def coverage(code):
    tm = load_tm(code)
    segs = all_segments()
    have = sum(1 for _, s in segs if sid(s) in tm)
    return have / max(1, len(segs)), len(segs) - have


def build(codes):
    for code in codes:
        hl = CODE2HL[code]
        cov, miss = coverage(code)
        if cov < MIN_COVERAGE:
            print("%s: coverage %.0f%% (%d missing) — skipped" % (code, cov * 100, miss))
            continue
        tm = load_tm(code)
        for page in SRC_FILE:
            out, missing = render(page, hl, tm)
            f = os.path.join(ROOT, code, STATIC_PAGES[page].strip("/"), "index.html")
            os.makedirs(os.path.dirname(f), exist_ok=True)
            open(f, "w", encoding="utf-8").write(out)
            print("%-8s %-9s %s%s" % (code, page, page_url(page, hl), ("  (%d untranslated)" % len(missing)) if missing else ""))


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "build"
    if cmd == "todo":
        tm = load_tm(sys.argv[2])
        for page, s in all_segments():
            if sid(s) not in tm:
                print("%s\t%s" % (sid(s), s.replace("\n", " ")))
    elif cmd == "merge":
        code, f = sys.argv[2], sys.argv[3]
        tm = load_tm(code)
        n = 0
        for line in open(f, encoding="utf-8"):
            line = line.rstrip("\n")
            if "\t" in line:
                k, v = line.split("\t", 1)
                if re.fullmatch(r"[0-9a-f]{10}", k.strip()) and v.strip():
                    tm[k.strip()] = v.strip()
                    n += 1
        json.dump(tm, open(os.path.join(I18N, code + ".json"), "w", encoding="utf-8"), ensure_ascii=False, indent=0, sort_keys=True)
        print("merged", n, "->", code, "coverage %.1f%%" % (coverage(code)[0] * 100))
    elif cmd == "source":
        json.dump({sid(s): s for _, s in all_segments()}, open(os.path.join(I18N, "source.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=0)
        print(len(all_segments()), "segments")
    else:
        build(sys.argv[2:] or [L[h]["code"] for h in NEW_LANGS])


if __name__ == "__main__":
    main()
