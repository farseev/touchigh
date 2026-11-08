#!/usr/bin/env python3
"""Site checker (stdlib only). Run from anywhere:  python3 tools/check_site.py

Checks every HTML page for: JSON-LD that parses, exactly one <h1>, a canonical whose target exists and
points back at the page's own file (self-canonical), hreflang targets that exist (and a reciprocal
cluster), lang/dir attributes, and internal links / assets that resolve to files. Also validates every
sitemap*.xml as XML and checks that each <loc> resolves. Exit code 1 on any error.
"""
import glob
import json
import os
import re
import sys
import xml.etree.ElementTree as ET
from html.parser import HTMLParser

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = "https://touchigh.ai"
sys.path.insert(0, os.path.dirname(__file__))
from site_config import L  # noqa: E402

errors, warns = [], []


def target_file(path):
    p = path.split("#")[0].split("?")[0]
    if not p.startswith("/"):
        return None
    p = p.lstrip("/")
    full = os.path.join(ROOT, p)
    if p == "" or p.endswith("/"):
        return os.path.join(full, "index.html")
    return full


class P(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.h1 = 0
        self.links = []
        self.canon = None
        self.alts = []
        self.html_attrs = {}
        self.ids = set()
        self.frags = []

    def handle_starttag(self, tag, attrs):
        d = dict(attrs)
        if "id" in d:
            self.ids.add(d["id"])
        if tag == "html":
            self.html_attrs = d
        if tag == "h1":
            self.h1 += 1
        if tag == "link" and d.get("rel") == "canonical":
            self.canon = d.get("href")
        if tag == "link" and d.get("rel") == "alternate" and d.get("hreflang"):
            self.alts.append((d["hreflang"], d.get("href")))
        for k in ("href", "src", "poster"):
            v = d.get(k)
            if v and tag != "link" or (tag == "link" and k == "href" and d.get("rel") in ("stylesheet", "icon", "apple-touch-icon", "manifest")):
                if v:
                    self.links.append(v)
        if tag in ("source", "img") and d.get("srcset"):
            for part in d["srcset"].split(","):
                u = part.strip().split(" ")[0]
                if u:
                    self.links.append(u)


def page_url_of(f):
    rel = os.path.relpath(f, ROOT).replace(os.sep, "/")
    return "/" + (rel[:-len("index.html")] if rel.endswith("index.html") else rel)


def check_page(f, hreflang_map):
    s = open(f, encoding="utf-8").read()
    rel = os.path.relpath(f, ROOT)
    if rel.startswith("login/"):
        return
    p = P()
    p.feed(s)
    for m in re.finditer(r'<script type="application/ld\+json">(.*?)</script>', s, re.S):
        try:
            json.loads(m.group(1))
        except Exception as e:  # noqa: BLE001
            errors.append("%s: JSON-LD does not parse (%s)" % (rel, e))
    if p.h1 != 1:
        errors.append("%s: %d <h1> elements" % (rel, p.h1))
    lang = p.html_attrs.get("lang")
    if not lang:
        errors.append("%s: missing <html lang>" % rel)
    elif lang in L and L[lang]["dir"] == "rtl" and p.html_attrs.get("dir") != "rtl":
        errors.append("%s: rtl language without dir=rtl" % rel)
    me = page_url_of(f)
    if not p.canon:
        errors.append("%s: no canonical" % rel)
    else:
        c = p.canon.replace(SITE, "")
        tf = target_file(c)
        if not tf or os.path.normpath(tf) != os.path.normpath(f):
            errors.append("%s: canonical %s is not self" % (rel, p.canon))
    hl = {}
    for code, href in p.alts:
        u = href.replace(SITE, "")
        tf = target_file(u)
        if not tf or not os.path.exists(tf):
            errors.append("%s: hreflang %s -> %s missing" % (rel, code, href))
        hl[code] = u
    if p.alts and "x-default" not in hl:
        errors.append("%s: hreflang without x-default" % rel)
    if p.canon:
        hreflang_map[p.canon.replace(SITE, "")] = (rel, hl)
    for u in p.links:
        if u.startswith("//") or u.startswith("http") or u.startswith("mailto:") or u.startswith("tel:") or u.startswith("data:") or u.startswith("javascript:"):
            continue
        if u.startswith("#"):
            if len(u) > 1 and u[1:] not in p.ids:
                warns.append("%s: fragment %s not found" % (rel, u))
            continue
        if not u.startswith("/"):
            u = me + u if me.endswith("/") else os.path.dirname(me) + "/" + u
        tf = target_file(u)
        if tf and not os.path.exists(tf):
            errors.append("%s: broken internal link %s" % (rel, u))


def check_clusters(hmap):
    """Every page listed in a cluster must list the same cluster back (reciprocity)."""
    for url, (rel, hl) in hmap.items():
        for code, u in hl.items():
            if code == "x-default":
                continue
            other = hmap.get(u)
            if other is None:
                continue
            if url not in other[1].values():
                errors.append("%s: hreflang %s -> %s is not reciprocal" % (rel, code, u))


def check_sitemaps():
    for f in sorted(glob.glob(os.path.join(ROOT, "sitemap*.xml"))):
        rel = os.path.relpath(f, ROOT)
        try:
            tree = ET.parse(f)
        except ET.ParseError as e:
            errors.append("%s: invalid XML (%s)" % (rel, e))
            continue
        for loc in tree.iter():
            if loc.tag.endswith("}loc") and loc.text and loc.text.startswith(SITE):
                u = loc.text.replace(SITE, "")
                tf = target_file(u)
                if tf and not os.path.exists(tf):
                    errors.append("%s: <loc> %s missing" % (rel, loc.text))


def main():
    hmap = {}
    files = [f for f in glob.glob(os.path.join(ROOT, "**", "*.html"), recursive=True) if "/.git/" not in f and "/tools/" not in f]
    for f in sorted(files):
        check_page(f, hmap)
    check_clusters(hmap)
    check_sitemaps()
    for xf in glob.glob(os.path.join(ROOT, "**", "feed.xml"), recursive=True):
        try:
            ET.parse(xf)
        except ET.ParseError as e:
            errors.append("%s: invalid XML (%s)" % (os.path.relpath(xf, ROOT), e))
    for w in warns[:30]:
        print("warn:", w)
    for e in errors:
        print("ERROR:", e)
    print("%d pages checked, %d errors, %d warnings" % (len(files), len(errors), len(warns)))
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
