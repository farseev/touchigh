#!/usr/bin/env python3
"""One command to rebuild every generated language artefact:
static language pages, language hubs, articles, language menus + hreflang on every page, sitemaps.
  python3 tools/build_i18n.py            # all languages with >= 97% coverage
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(__file__))
from site_config import L, NEW_LANGS, STATIC_PAGES  # noqa: E402
import localize  # noqa: E402
import hub_i18n  # noqa: E402
import articles  # noqa: E402
import langmenu  # noqa: E402
import sitemaps  # noqa: E402
from registry import registry  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def menus():
    # bilingual root pages: zh-Hans default + ?lang=en, switching in place
    for page, path in STATIC_PAGES.items():
        f = os.path.join(ROOT, path.strip("/"), "index.html")
        s = open(f, encoding="utf-8").read()
        s = langmenu.apply(s, "zh-Hans", localize.static_versions(page), setlang=True)
        open(f, "w", encoding="utf-8").write(s)
    hv = hub_i18n.hub_versions()
    for hl, f in (("zh-Hans", "blog/index.html"), ("en", "blog/en/index.html")):
        p = os.path.join(ROOT, f)
        s = open(p, encoding="utf-8").read()
        open(p, "w", encoding="utf-8").write(langmenu.apply(s, hl, hv))
    for slug, e in registry().items():
        for hl, path in e["versions"].items():
            p = os.path.join(ROOT, path.strip("/"), "index.html")
            s = open(p, encoding="utf-8").read()
            open(p, "w", encoding="utf-8").write(langmenu.apply(s, hl, e["versions"]))


def main():
    codes = sys.argv[1:] or [L[h]["code"] for h in NEW_LANGS]
    localize.build(codes)
    for c in codes:
        hl = localize.CODE2HL[c]
        if localize.coverage(c)[0] >= localize.MIN_COVERAGE and "cats" in hub_i18n.UI.get(hl, {}):
            hub_i18n.render(hl)
    articles.build_all()
    menus()
    # second pass so every page sees the full set of language versions
    localize.build(codes)
    for c in codes:
        hl = localize.CODE2HL[c]
        if localize.coverage(c)[0] >= localize.MIN_COVERAGE and "cats" in hub_i18n.UI.get(hl, {}):
            hub_i18n.render(hl)
    sitemaps.main()


if __name__ == "__main__":
    main()
