# ToucHigh PRO — files to add / replace in the repo

New page: **https://touchigh.ai/pro/** — "ToucHigh PRO · 外呼获客 / strategy-first outbound & lead generation".
Built to match the main site 1:1: same tokens, nav, `data-en`/`data-zh` language system (中文 default, `?lang=en`, shared `localStorage` key `tl`), same Calendly popup + `book()` GA events, same GA tag `G-XCXZPEFP94` (with `page_path:'/pro/'`).

## Added
- `pro/index.html` — the full bilingual PRO page. Sections: hero (with engine-written cold-email mock), channel band, delivery stats, 5-layer strategy engine, real output (Tonik/inDrive briefs reimagined as outreach), 21-day × 4-channel × 3-level cadence matrix, AI×human proof band (7,000+ variants · 100% human-reviewed · <5 min takeover · <60 s kill switch), sales clients (EcoFlow · 中国联通 · OrionStar · Ant International · Aurora · Tungee · MAXHUB), metrics + Mothercare quote, compliance checks, PRO FAQ, final CTA with contracting entities (SG SOMIN PTE. LTD. · HK SOMIN Limited · UK MARKETING AI LIMITED).
- SEO/AEO/GEO on the page itself: canonical + hreflang (`/pro/`, `/pro/?lang=en`), OG/Twitter, JSON-LD (`Service`, `HowTo`, `FAQPage`, `BreadcrumbList`, `WebPage` with speakable).

## Replaced (small, surgical edits)
- `index.html` — nav link + footer "Product" link to `/pro/` (bilingual, orange-highlighted in nav). Nothing else touched.
- `sitemap.xml` — added the `/pro/` URL entry with hreflang alternates.
- `llms.txt` — new "ToucHigh PRO (outbound & lead generation service)" section.
- `llms-full.txt` — full PRO brief section for AI answer engines.
- `feed.xml` — new PRO item; `lastBuildDate` bumped.
- `ai.txt` — `Pro-service:` pointer added.

## Notes
- Language selector: identical to the main site (the earlier standalone HTML block had no selector because it shipped without the site's i18n runtime — this page is wired into it).
- Naming: rendered as the "ToucHigh" wordmark + orange **PRO** badge in the nav/footer lockup, and "ToucHigh PRO" (your spelling) in copy, titles and structured data. Say the word if you want a single casing everywhere.
- `robots.txt`, icons, media: unchanged — the page reuses existing root assets via absolute paths.
