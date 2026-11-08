#!/usr/bin/env python3
"""One-off importer: turn the hand-built article pages (blog/<slug>/, blog/zh|en|…/<slug>/) into the
i18n/articles/<slug>/ source format (meta.json + <hl>.txt) that tools/articles.py renders.

  python3 tools/import_legacy.py            # import every article page that has no source folder yet
  python3 tools/import_legacy.py <slug> …   # (re)import specific slugs

Everything is read from the existing pages, nothing is rewritten: text fields are stored unescaped,
HTML fields (body, takeaways, prop box, FAQ answers) as they appear. Chrome wording that differs from
i18n/ui.json for that language is kept per article in meta.json "ui" so the page renders unchanged.
"""
import html
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(__file__))
from site_config import L, ORDER, SITE  # noqa: E402
from registry import registry  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ART = os.path.join(ROOT, "i18n", "articles")
UI = json.load(open(os.path.join(ROOT, "i18n", "ui.json"), encoding="utf-8"))
U = html.unescape


def g(rx, s, default=None, flags=re.S):
    m = re.search(rx, s, flags)
    return m.group(1) if m else default


def soft(htm):
    """HTML stored as written, but with quote/apostrophe entities turned back into characters."""
    return htm.replace("&#39;", "'").replace("&#x27;", "'").replace("&#34;", '"').replace("&quot;", '"').strip()


def lis(block):
    return [soft(x) for x in re.findall(r"<li>(.*?)</li>", block or "", re.S)]


def extract(s):
    d = {}
    d["title"] = U(g(r"<h1>(.*?)</h1>", s))
    d["seo_title"] = U(g(r"<title>(.*?)</title>", s))
    d["desc"] = U(g(r'<meta name="description" content="([^"]*)"', s))
    d["dek"] = U(g(r'<p class="dek">(.*?)</p>', s))
    d["section"] = U(g(r'<header class="a-head">\s*<div class="eyebrow">(.*?)</div>', s))
    d["tags"] = " | ".join(U(t) for t in re.findall(r'<meta property="article:tag" content="([^"]*)">', s))
    d["keywords"] = U(g(r'<meta name="keywords" content="([^"]*)"', s, ""))
    d["read"] = g(r'<div class="a-meta">.*?</time></span><span>[^<\d]*(\d+)', s)
    d["q"] = U(g(r'<p class="q">(.*?)</p>', s))
    d["a"] = U(g(r'<p class="ans"><b>.*?</b>(.*?)</p>', s))
    d["takeaways"] = lis(g(r'<section class="kt takeaways"><h2>.*?</h2><ul>(.*?)</ul></section>', s))
    d["alt"] = U(g(r'<figure class="hero-fig">.*?alt="([^"]*)"', s, ""))
    d["body"] = g(r'<div class="prose">(.*?)</div>\s*<aside class="insight"', s).strip()
    d["insight_quote"] = U(g(r'<aside class="insight"[^>]*>.*?<blockquote>(.*?)</blockquote>', s))
    d["insight"] = U(g(r'<aside class="insight"[^>]*>.*?</blockquote>\s*<p>(.*?)</p>', s))
    prop = g(r'(<section class="prop".*?</section>)', s)
    d["prop_eyebrow"] = U(g(r'<div class="ph"><div class="eyebrow">(.*?)</div>', prop))
    pb = g(r'<div class="pb prose">(.*?)</div>\s*<div class="pa">', prop)
    pb_wo_uc = re.sub(r'<p class="uc">.*?</p>', "", pb, flags=re.S).strip()
    m = re.fullmatch(r"<p>(.*?)</p>\s*<ul>(.*?)</ul>\s*<p>(.*?)</p>", pb_wo_uc, re.S)
    if not m:
        raise ValueError("unexpected prop box: " + pb_wo_uc[:200])
    d["prop_intro"], d["prop_items"], d["prop_outro"] = soft(m.group(1)), lis(m.group(2)), soft(m.group(3))
    landing = None
    if '<p class="uc">' in pb:
        landing = "supplier" if "supplier-ai-visibility" in pb else "amazon"
    faq = []
    for q, a in re.findall(r"<details(?: open)?><summary>(.*?)</summary><p>(.*?)</p></details>", g(r'(<section class="faq".*?</section>)', s), re.S):
        faq.append((U(q), soft(a)))
    d["faq"] = faq
    d["note"] = U(g(r'<p class="note"><b>.*?</b>(.*?)</p>', s))
    srcs = []
    for href, name, rest in re.findall(r'<li><a href="([^"]*)" rel="noopener" target="_blank">(.*?)</a> — (.*?)</li>', g(r'<section class="srcs">(.*?)</section>', s, "")):
        rest = U(rest)
        mm = re.match(r"(.*), (\d{4}-\d{2}(?:-\d{2})?)$", rest)
        src = {"name": U(name), "url": U(href), "publisher": mm.group(1) if mm else rest}
        if mm:
            src["date"] = mm.group(2)
        srcs.append(src)
    related = re.findall(r'<a class="card" href="([^"]+)">', g(r'<section class="related">(.*?)</section>', s, ""))
    ld = json.loads(g(r'<script type="application/ld\+json">(\{"@context":"https://schema.org","@type":"BlogPosting".*?)</script>', s))
    info = dict(num=g(r"return book\(event,'article_(T\d+)'\)", s).lower(), hero=g(r"/assets/blog/hero/(t\d+)\.jpg", s),
                published=ld["datePublished"], modified=ld.get("dateModified", ld["datePublished"]), landing=landing,
                sources=srcs, related=related, ld=ld)
    return d, info, chrome(s)


def chrome(s):
    """Chrome strings as they appear on the page (compared with ui.json later)."""
    c = {}
    c["skip"] = U(g(r'<a class="skip" href="#main">(.*?)</a>', s))
    nav = g(r'<nav class="nav-links"[^>]*>(.*?)</nav>', s)
    links = [U(x) for x in re.findall(r"<a [^>]*>(.*?)</a>", nav)]
    c["home"], c["products"], c["faq_nav"], c["blog"] = links[0], links[1], links[2], links[4]
    c["login"] = U(g(r"location:'blog_nav'\}\)\}catch\(e\)\{\}\">(.*?)</a>", s))
    c["book"] = U(g(r"return book\(event,'blog_nav'\)\">(.*?)</a>", s))
    c["author"] = U(g(r'<div class="a-meta"><b>(.*?)</b>', s))
    pub = g(r'<div class="a-meta"><b>.*?</b><span>(.*?)</span>', s)
    c["published"] = U(re.sub(r"<time.*?</time>", "{d}", pub))
    c["date_text"] = U(g(r'<div class="a-meta">.*?<time[^>]*>(.*?)</time>', s))
    rd = U(g(r'<div class="a-meta">.*?</time></span><span>(.*?)</span>', s))
    c["read"] = re.sub(r"\d+", "{n}", rd, count=1)
    c["also"] = U(g(r'<div class="a-langs">([^<]*)', s, ""))
    c["qeyebrow"] = U(g(r'<section class="answer-lead answer-box" aria-label="([^"]*)"', s))
    c["short"] = U(g(r'<p class="ans"><b>(.*?)</b>', s))
    c["takeaways"] = U(g(r'<section class="kt takeaways"><h2>(.*?)</h2>', s))
    c["insight"] = U(g(r'<aside class="insight" aria-label="([^"]*)"', s))
    c["help"] = U(g(r'<section class="prop" aria-label="([^"]*)"', s))
    c["help_h2"] = U(g(r'<div class="ph"><div class="eyebrow">.*?</div><h2>(.*?)</h2>', s))
    c["book30"] = U(g(r"return book\(event,'article_T\d+'\)\">(.*?)</a>", s))
    c["login_th"] = U(g(r'<div class="pa">.*?<a class="btn btn-ghost" href="https://pro.touchigh.ai"[^>]*>(.*?)</a>', s))
    c["faq"] = U(g(r'<section class="faq" aria-label="[^"]*"><h2>(.*?)</h2>', s))
    c["faq_aria"] = U(g(r'<section class="faq" aria-label="([^"]*)"', s))
    c["sources"] = U(g(r'<section class="srcs"><h2>(.*?)</h2>', s))
    c["why"] = U(g(r'<p class="note"><b>(.*?)</b>', s))
    c["toc"] = U(g(r'<nav class="toc" aria-label="[^"]*"><h4>(.*?)</h4>', s))
    c["side"] = U(g(r'<div class="side-cta"><h4>ToucHigh</h4><p>(.*?)</p>', s))
    c["related"] = U(g(r'<section class="related"><div class="wrap"><h2>(.*?)</h2>', s))
    c["back"] = U(g(r'<section class="related">.*?<a class="btn btn-ghost" href="[^"]*">(.*?)</a>', s))
    c["final_side"] = U(g(r'<section class="final"[^>]*>\s*<div class="eyebrow">ToucHigh</div>\s*<h2>(.*?)</h2>', s))
    c["final_p"] = U(g(r'<section class="final"[^>]*>.*?</h2>\s*<p>(.*?)</p>', s))
    c["tagline"] = U(g(r'<p style="margin-top:12px;max-width:38ch;font-size:14px">(.*?)</p>', s))
    c["blog_name"] = U(g(r'"isPartOf":\{"@type":"Blog","@id":"[^"]*","name":"([^"]*)"', s, ""))
    return c


def dump_txt(d):
    out = []
    for k in ("title", "seo_title", "desc", "dek", "section", "tags", "keywords", "read", "q", "a"):
        out += ["== %s ==" % k, d[k]]
    out += ["== takeaways =="] + ["- " + x for x in d["takeaways"]]
    if d.get("alt"):
        out += ["== alt ==", d["alt"]]
    out += ["== body ==", d["body"]]
    out += ["== insight_quote ==", d["insight_quote"], "== insight ==", d["insight"], "== prop_eyebrow ==", d["prop_eyebrow"],
            "== prop_intro ==", d["prop_intro"], "== prop_items =="] + ["- " + x for x in d["prop_items"]]
    out += ["== prop_outro ==", d["prop_outro"], "== faq =="]
    for q, a in d["faq"]:
        out += ["Q: " + q, "A: " + a]
    out += ["== note ==", d["note"]]
    for k, v in d.items():
        if isinstance(v, str) and "\n== " in "\n" + v:
            raise ValueError("section marker inside " + k)
    return "\n".join(out) + "\n"


def one_line(d):
    """Fields parsed line by line must not contain line breaks."""
    for k in ("title", "seo_title", "desc", "dek", "section", "tags", "keywords", "q", "a", "insight_quote", "insight", "note", "alt"):
        d[k] = re.sub(r"\s*\n\s*", " ", d.get(k) or "").strip()
    d["takeaways"] = [re.sub(r"\s*\n\s*", " ", x) for x in d["takeaways"]]
    d["prop_items"] = [re.sub(r"\s*\n\s*", " ", x) for x in d["prop_items"]]
    d["prop_intro"] = re.sub(r"\s*\n\s*", " ", d["prop_intro"])
    d["prop_outro"] = re.sub(r"\s*\n\s*", " ", d["prop_outro"])
    d["faq"] = [(re.sub(r"\s*\n\s*", " ", q), re.sub(r"\s*\n\s*", " ", a)) for q, a in d["faq"]]


def ui_diff(hl, c):
    """Chrome keys whose wording on this page differs from ui.json."""
    u = UI[hl]
    diff = {}
    for k in ("skip", "home", "products", "faq_nav", "blog", "login", "book", "author", "published", "read", "also", "qeyebrow", "short",
              "takeaways", "insight", "help", "book30", "login_th", "faq", "sources", "why", "toc", "side", "related", "back", "final_p",
              "tagline", "blog_name"):
        if c.get(k) is not None and c[k] != u.get(k):
            diff[k] = c[k]
    for k, uk in (("help_h2", "help"), ("faq_aria", "faq"), ("final_side", "side")):
        if c.get(k) is not None and c[k] != diff.get(uk, u.get(uk)):
            diff[k] = c[k]
    return diff


def main(slugs=None):
    reg = registry()
    done = set(os.listdir(ART))
    todo = slugs or sorted(s for s in reg if s not in done)
    for slug in todo:
        e = reg[slug]
        orig = next(h for h, p in e["versions"].items() if p == "/blog/%s/" % slug)
        meta, ui, alts = None, {}, {}
        os.makedirs(os.path.join(ART, slug), exist_ok=True)
        for hl, path in sorted(e["versions"].items(), key=lambda kv: kv[0] != orig):
            s = open(os.path.join(ROOT, path.strip("/"), "index.html"), encoding="utf-8").read()
            d, info, c = extract(s)
            one_line(d)
            rel = []
            for href in info["related"]:
                rs = href.rstrip("/").split("/")[-1]
                rel.append(rs)
            if meta is None:
                meta = {"num": info["num"], "original": orig, "cat": e["pages"][hl]["cat"], "hero": info["hero"],
                        "published": info["published"]}
                if info["modified"] != info["published"]:
                    meta["modified"] = info["modified"]
                if info["landing"]:
                    meta["landing"] = info["landing"]
                meta["related"] = rel
                meta["sources"] = info["sources"]
            else:
                for k in ("num", "hero", "published"):
                    if meta[k] != info[k]:
                        print("WARN", slug, hl, k, "differs:", meta[k], info[k])
                if rel != meta["related"]:
                    meta.setdefault("related_by_lang", {})[hl] = rel
                if info["sources"] != meta["sources"]:
                    meta.setdefault("sources_by_lang", {})[hl] = info["sources"]
                if info["modified"] != meta.get("modified", meta["published"]):
                    meta.setdefault("modified_by_lang", {})[hl] = info["modified"]
            og = g(r'<meta property="og:image" content="https://touchigh.ai([^"]+)"', s)
            meta.setdefault("og_by_lang", {})[hl] = og
            meta.setdefault("words_by_lang", {})[hl] = info["ld"].get("wordCount")
            diff = ui_diff(hl, c)
            if diff:
                ui[hl] = diff
            if c["date_text"]:
                from articles import fmt_date  # noqa: E402
                if fmt_date(info["published"], hl) != c["date_text"]:
                    ui.setdefault(hl, {})["date_text"] = c["date_text"]
            open(os.path.join(ART, slug, hl + ".txt"), "w", encoding="utf-8").write(dump_txt(d))
        if ui:
            meta["ui"] = ui
        meta["legacy"] = True
        open(os.path.join(ART, slug, "meta.json"), "w", encoding="utf-8").write(json.dumps(meta, ensure_ascii=False, indent=1) + "\n")
        print("imported", slug, sorted(e["versions"]), "ui overrides:", {h: sorted(v) for h, v in ui.items()})


if __name__ == "__main__":
    main(sys.argv[1:] or None)
