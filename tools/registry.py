"""Scan the existing blog article pages into a registry (stdlib only).

registry() -> {slug: {"versions": {hl: path}, "pages": {hl: info}}}
info = title, dek, eyebrow, hero (tNN), alt, read, date (ISO), path, cat (hub filter key)
"""
import glob
import html
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = "https://touchigh.ai"
HUBS = {"zh-Hans": "blog/index.html", "en": "blog/en/index.html"}


def _g(rx, s, default=""):
    m = re.search(rx, s, re.S)
    return html.unescape(m.group(1)).strip() if m else default


def _cats():
    """data-cat per article URL, read from the two hubs."""
    cats = {}
    for f in HUBS.values():
        p = os.path.join(ROOT, f)
        if not os.path.exists(p):
            continue
        s = open(p, encoding="utf-8").read()
        for m in re.finditer(r'<a class="(?:card|feat)[^"]*" href="([^"]+)" data-cat="([^"]+)"', s):
            cats[m.group(1)] = m.group(2)
    return cats


def page_info(path_file):
    s = open(path_file, encoding="utf-8").read()
    rel = "/" + os.path.relpath(path_file, ROOT).replace(os.sep, "/")[:-len("index.html")]
    canon = _g(r'<link rel="canonical" href="([^"]+)"', s).replace(SITE, "")
    slug = canon.rstrip("/").split("/")[-1]
    return dict(
        slug=slug, path=canon or rel, hl=_g(r'<html lang="([^"]+)"', s),
        title=_g(r"<h1>(.*?)</h1>", s), dek=_g(r'<p class="dek">(.*?)</p>', s),
        eyebrow=_g(r'<header class="a-head">\s*<div class="eyebrow">(.*?)</div>', s),
        hero=_g(r'/assets/blog/hero/(t\d+)\.jpg', s), alt=_g(r'<figure class="hero-fig">.*?alt="([^"]*)"', s),
        read=_g(r'<div class="a-meta">.*?<span>[^<]*<time[^>]*>[^<]*</time></span><span>([^<]*)</span>', s),
        date=_g(r'"datePublished":"([^"]+)"', s), modified=_g(r'"dateModified":"([^"]+)"', s),
        og=_g(r'<meta property="og:image" content="([^"]+)"', s),
        desc=_g(r'<meta name="description" content="([^"]*)"', s),
    )


def registry():
    cats = _cats()
    reg = {}
    files = glob.glob(os.path.join(ROOT, "blog", "*", "index.html")) + glob.glob(os.path.join(ROOT, "blog", "*", "*", "index.html"))
    for f in files:
        s = open(f, encoding="utf-8").read(4000)
        if 'property="og:type" content="article"' not in s and '"BlogPosting"' not in open(f, encoding="utf-8").read():
            continue
        if 'class="a-head"' not in open(f, encoding="utf-8").read():
            continue
        info = page_info(f)
        e = reg.setdefault(info["slug"], {"versions": {}, "pages": {}})
        e["versions"][info["hl"]] = info["path"]
        info["cat"] = cats.get(info["path"], "")
        e["pages"][info["hl"]] = info
    for slug, e in reg.items():
        cat = next((p["cat"] for p in e["pages"].values() if p["cat"]), "")
        for p in e["pages"].values():
            p["cat"] = p["cat"] or cat
    return reg


if __name__ == "__main__":
    r = registry()
    print(len(r), "articles,", sum(len(e["versions"]) for e in r.values()), "versions")
    for k in list(r)[:3]:
        print(k, r[k]["versions"], {h: (p["title"][:40], p["read"], p["cat"], p["hero"]) for h, p in r[k]["pages"].items()})
