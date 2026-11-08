#!/usr/bin/env python3
"""Per-language sitemaps (sitemap-<code>.xml) + sitemap index (/sitemap.xml). stdlib only.

Every URL carries its full hreflang cluster (+ x-default = Simplified Chinese). Home and PRO keep their
image and video entries. Articles carry their hero image.
"""
import html
import os
import re
import sys
from datetime import date

sys.path.insert(0, os.path.dirname(__file__))
from site_config import L, ORDER, SITE, STATIC_PAGES, page_url  # noqa: E402
from registry import registry  # noqa: E402
from localize import static_versions  # noqa: E402
from hub_i18n import hub_versions  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TODAY = date.today().isoformat()
E = lambda s: html.escape(s, quote=True)  # noqa: E731

HOME_MEDIA = """    <image:image><image:loc>https://touchigh.ai/og-cover.jpg</image:loc><image:title>ToucHigh — AI search visibility on autopilot</image:title></image:image>
    <image:image><image:loc>https://touchigh.ai/media/seo.jpg</image:loc><image:title>ToucHigh SEO, AEO and GEO dashboard</image:title></image:image>
    <image:image><image:loc>https://touchigh.ai/media/social-lib.jpg</image:loc><image:title>ToucHigh Social Autopilot content library</image:title></image:image>
    <video:video>
      <video:thumbnail_loc>https://touchigh.ai/media/audit.jpg</video:thumbnail_loc>
      <video:title>ToucHigh builds a US market-entry strategy in real time</video:title>
      <video:description>ToucHigh reads a store and its competitors' ads and organic content, then generates a US market-entry strategy on autopilot.</video:description>
      <video:content_loc>https://touchigh.ai/media/audit.mp4</video:content_loc>
      <video:live>no</video:live>
    </video:video>
    <video:video>
      <video:thumbnail_loc>https://touchigh.ai/media/article.jpg</video:thumbnail_loc>
      <video:title>ToucHigh generates a GEO / thought-leadership article</video:title>
      <video:description>One trending query turns into a full GEO article, angled to get the store cited in AI answers.</video:description>
      <video:content_loc>https://touchigh.ai/media/article.mp4</video:content_loc>
      <video:live>no</video:live>
    </video:video>
"""
PRO_MEDIA = """    <image:image><image:loc>https://touchigh.ai/og-cover.jpg</image:loc><image:title>ToucHigh PRO — strategy-first outbound and lead generation</image:title></image:image>
"""


def lastmod_of(path, default=TODAY):
    f = os.path.join(ROOT, path.split("?")[0].strip("/"), "index.html")
    if os.path.exists(f):
        s = open(f, encoding="utf-8").read(200000)
        m = re.search(r'"dateModified":"(\d{4}-\d{2}-\d{2})', s)
        if m:
            return m.group(1)
    return default


def url_entry(loc, versions, prio, extra="", lastmod=TODAY, freq="weekly"):
    alts = "".join('    <xhtml:link rel="alternate" hreflang="%s" href="%s%s"/>\n' % (h, SITE, E(versions[h])) for h in ORDER if h in versions)
    xd = versions.get("zh-Hans") or versions.get("en")
    alts += '    <xhtml:link rel="alternate" hreflang="x-default" href="%s%s"/>\n' % (SITE, E(xd))
    return "  <url>\n    <loc>%s%s</loc>\n    <lastmod>%s</lastmod>\n    <changefreq>%s</changefreq>\n    <priority>%s</priority>\n%s%s  </url>\n" % (
        SITE, E(loc), lastmod, freq, prio, alts, extra)


def main():
    per = {hl: [] for hl in ORDER}
    for page in STATIC_PAGES:
        vers = static_versions(page)
        for hl, p in vers.items():
            extra = HOME_MEDIA if page == "home" else (PRO_MEDIA if page == "pro" else "")
            per[hl].append(url_entry(p, vers, "1.0" if page == "home" else "0.9", extra))
    hv = hub_versions()
    for hl, p in hv.items():
        per[hl].append(url_entry(p, hv, "0.9"))
    for slug, e in registry().items():
        for hl, p in e["versions"].items():
            info = e["pages"][hl]
            img = '    <image:image><image:loc>%s/assets/blog/hero/%s.jpg</image:loc><image:title>%s</image:title></image:image>\n' % (SITE, info["hero"], E(info["title"])) if info["hero"] else ""
            per[hl].append(url_entry(p, e["versions"], "0.8", img, (info.get("modified") or info.get("date") or TODAY)[:10], "monthly"))
    head = ('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"\n'
            '        xmlns:xhtml="http://www.w3.org/1999/xhtml"\n        xmlns:image="http://www.google.com/schemas/sitemap-image/1.1"\n'
            '        xmlns:video="http://www.google.com/schemas/sitemap-video/1.1">\n')
    written = []
    for f in os.listdir(ROOT):
        if re.fullmatch(r"sitemap-[a-z-]+\.xml", f):
            os.remove(os.path.join(ROOT, f))
    for hl in ORDER:
        if not per[hl]:
            continue
        name = "sitemap-%s.xml" % hl.lower()
        open(os.path.join(ROOT, name), "w", encoding="utf-8").write(head + "".join(per[hl]) + "</urlset>\n")
        written.append((name, len(per[hl])))
    idx = '<?xml version="1.0" encoding="UTF-8"?>\n<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    idx += "".join("  <sitemap>\n    <loc>%s/%s</loc>\n    <lastmod>%s</lastmod>\n  </sitemap>\n" % (SITE, n, TODAY) for n, _ in written)
    idx += "</sitemapindex>\n"
    open(os.path.join(ROOT, "sitemap.xml"), "w", encoding="utf-8").write(idx)
    rb = open(os.path.join(ROOT, "robots.txt"), encoding="utf-8").read()
    rb = re.sub(r"\n# Sitemaps.*\Z|\nSitemap: .*\Z", "", rb, flags=re.S).rstrip("\n")
    rb += "\n\n# Sitemaps: index plus one sitemap per language (hreflang clusters inside)\nSitemap: https://touchigh.ai/sitemap.xml\n"
    rb += "".join("Sitemap: %s/%s\n" % (SITE, n) for n, _ in written)
    open(os.path.join(ROOT, "robots.txt"), "w", encoding="utf-8").write(rb)
    for n, c in written:
        print(n, c)


if __name__ == "__main__":
    main()
