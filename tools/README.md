# tools/ — site generators and checks

All generators are Python 3 standard library only, except `og.py` (Open Graph cards, needs Pillow).
Run everything from the repo root.

| Script | What it does |
| --- | --- |
| `site_config.py` | The 17 site languages (zh-Hans default + en + 15), hreflang codes, URL scheme. |
| `make_landings.py` | Builds the bilingual (zh-Hans / `?lang=en`) landing pages `/supplier-ai-visibility/` and `/amazon-ads-autopilot/` on the `/pro/` design system (CSS copied from `pro/index.html`). |
| `registry.py` | Scans existing article pages (title, dek, hero, versions per language). |
| `articles.py` | Renders articles from `i18n/articles/<slug>/meta.json` + `<hl>.txt` (one text file per language) with the existing article template, BlogPosting (workTranslation/translationOfWork), FAQPage, BreadcrumbList. |
| `hubs.py` | Adds rendered articles to the zh/en hubs (cards, Blog JSON-LD, count) and RSS feeds. |
| `traction_links.py` | Adds the use-case line (landing page + ToucHigh PRO) to the six traction articles. |
| `localize.py` | Renders home, /pro/ and both landing pages into the 15 further languages from `i18n/<code>.json` (segments = the page's `data-en` values, alt/aria-label, demo captions, head metadata from `i18n/pages.json`). `todo <code>` lists untranslated segments, `merge <code> file.tsv` imports `id<TAB>translation` lines. Pages are only built at ≥ 97 % coverage. |
| `hub_i18n.py` | Renders `/blog/<code>/` from the English hub; cards use the article in that language when it exists, otherwise the English version. |
| `langmenu.py` | The shared accessible language menu (`assets/css/lang-menu.css`, `assets/js/lang-menu.js`) and the hreflang cluster. |
| `sitemaps.py` | `sitemap-<hl>.xml` per language + the index at `/sitemap.xml`; updates robots.txt. |
| `build_i18n.py` | Runs everything above in order (static pages, hubs, articles, menus on every page, sitemaps). |
| `og.py` | 1200×630 OG cards (text left, artwork right). |
| `check_site.py` | JSON-LD parses, one `<h1>`, self-canonical, hreflang targets exist and are reciprocal, internal links/assets resolve, sitemaps/feeds are valid XML. Exit 1 on errors. |

GA4 (G-XCXZPEFP94) events used by the generated pages follow the existing pattern
(`try{gtag('event',…)}catch(e){}`): `book_call_click` (via `book(event,'<location>')`), `login_click`,
`blog_click`, `pro_click` (links to /pro/ from the landing pages and articles), `landing_click`
(article → landing page), `language_switch`.

Typical article workflow: write `i18n/articles/<slug>/zh-Hans.txt` and `en.txt` (+ `meta.json`), then
`python3 tools/articles.py && python3 tools/og.py articles && python3 tools/hubs.py && python3 tools/check_site.py`.

## Language URL scheme

| Page | zh-Hans (x-default) | English | Other languages (`<code>` = zh-hant, ja, ko, th, vi, id, ms, hi, fil, es, fr, de, pt, ar, ru) |
| --- | --- | --- | --- |
| Home | `/` | `/?lang=en` | `/<code>/` |
| ToucHigh PRO | `/pro/` | `/pro/?lang=en` | `/<code>/pro/` |
| Landing pages | `/supplier-ai-visibility/`, `/amazon-ads-autopilot/` | `…/?lang=en` | `/<code>/supplier-ai-visibility/`, `/<code>/amazon-ads-autopilot/` |
| Blog hub | `/blog/` | `/blog/en/` | `/blog/<code>/` |
| Article | existing URLs unchanged (`/blog/<slug>/`, `/blog/zh/<slug>/`, `/blog/en/<slug>/`) | | `/blog/<code>/<slug>/` |

Every page carries the full hreflang cluster of the versions that exist (x-default = Simplified Chinese) and the
same language menu. Adding a language to an article = add `i18n/articles/<slug>/<hl>.txt`, then run `build_i18n.py`.
