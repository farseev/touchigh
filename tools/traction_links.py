#!/usr/bin/env python3
"""Add the use-case line (matching landing page + ToucHigh PRO) to existing articles' "How ToucHigh helps" box.
Idempotent (skips pages that already have <p class="uc">)."""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(__file__))
from articles import usecase_html  # noqa: E402
from registry import registry  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TRACTION = {
    "factory-website-geo-chatgpt-supplier": "supplier",
    "instagram-algorithm-posting-consistency": "amazon",
    "amazon-ads-agent-sellers": "amazon",
    "chatgpt-utm-ai-referral-measurement": "supplier",
    "content-marketing-trends-2026-primary-sources": "supplier",
    "factory-to-brand-seo-aeo-geo-us": "supplier",
}


def main():
    reg = registry()
    for slug, landing in TRACTION.items():
        for hl, info in reg[slug]["pages"].items():
            f = os.path.join(ROOT, info["path"].strip("/"), "index.html")
            s = open(f, encoding="utf-8").read()
            s = re.sub(r'<p class="uc">.*?</p>', "", s, flags=re.S)
            m = re.search(r"onclick=\"return book\(event,'(article_T\d+)'\)", s)
            loc = m.group(1) if m else "article"
            uc = usecase_html(landing, hl, loc)
            s, n = re.subn(r'(<section class="prop".*?<div class="pb prose">.*?)(</div>\s*<div class="pa">)', lambda mm: mm.group(1) + uc + mm.group(2), s, count=1, flags=re.S)
            if not n:
                print("no prop box:", f)
                continue
            if "/assets/css/blog-extra.css" not in s:
                s = s.replace('<link rel="stylesheet" href="/assets/css/touchigh-blog.css">', '<link rel="stylesheet" href="/assets/css/touchigh-blog.css">\n<link rel="stylesheet" href="/assets/css/blog-extra.css">', 1)
            open(f, "w", encoding="utf-8").write(s)
            print("updated", info["path"])


if __name__ == "__main__":
    main()
