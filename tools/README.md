# tools/ — site generators and checks

All generators are Python 3 standard library only, except `og.py` (Open Graph cards, needs Pillow).
Run everything from the repo root.

| Script | What it does |
| --- | --- |
| `site_config.py` | The 17 site languages (zh-Hans default + en + 15), hreflang codes, URL scheme. |
| `make_landings.py` | Builds the bilingual (zh-Hans / `?lang=en`) landing pages `/supplier-ai-visibility/` and `/amazon-ads-autopilot/` on the `/pro/` design system (CSS copied from `pro/index.html`). |
| `og.py` | 1200×630 OG cards (text left, artwork right). |
| `check_site.py` | JSON-LD parses, one `<h1>`, self-canonical, hreflang targets exist and are reciprocal, internal links/assets resolve, sitemaps/feeds are valid XML. Exit 1 on errors. |

GA4 (G-XCXZPEFP94) events used by the generated pages follow the existing pattern
(`try{gtag('event',…)}catch(e){}`): `book_call_click` (via `book(event,'<location>')`), `login_click`,
`blog_click`, `pro_click` (links to /pro/ from the landing pages and articles), `landing_click`
(article → landing page), `language_switch`.
