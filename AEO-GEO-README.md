# Touchigh — AEO / GEO optimization bundle

This site ships with a full answer-engine (AEO) and generative-engine (GEO) optimization layer, so ChatGPT, Perplexity, Google AI Overviews, Gemini and Copilot can read, understand and cite Touchigh accurately. This file explains every part so you or your team can maintain it.

## What is in the bundle

| File | Purpose |
| --- | --- |
| `index.html` | Homepage with full on-page SEO/AEO markup and 9 JSON-LD blocks (see below). |
| `robots.txt` | Explicitly allows all major search and AI-answer crawlers; points to the sitemap. |
| `sitemap.xml` | URL, hreflang (zh/en), plus image and video sitemap entries for the demo clips. |
| `llms.txt` | Short, structured brief for LLMs (the emerging `/llms.txt` convention). |
| `llms-full.txt` | Long, self-contained, citation-ready brief with FAQs and a suggested citation string. |
| `ai.txt` | Guidance for AI crawlers plus a reusable attribution string. |
| `feed.xml` | RSS feed for the homepage and the two core products. |
| `humans.txt` | Team and standards credits. |
| `.well-known/security.txt` | Security contact (RFC 9116). |
| `site.webmanifest` | PWA manifest with icons and theme colours. |
| `media/` | Real product screen recordings (mp4 + webm) and poster stills used on the page and in the video sitemap. |

## On-page markup already in `index.html`

- Title, meta description, keywords, canonical, robots (`max-image-preview:large`, `max-snippet:-1`, `max-video-preview:-1`).
- `hreflang` for `zh-Hans`, `en` and `x-default`.
- Open Graph (incl. `og:video`) and Twitter Card tags.
- Nine JSON-LD blocks: `Organization`, `WebSite` (with `SearchAction`), `Service`, two `SoftwareApplication` (GEO and Social), `HowTo`, `FAQPage`, `BreadcrumbList`, and a `WebPage` with a `speakable` specification.
- A visible, extraction-friendly "In one line" answer box (`#answer-box`) plus an eight-question FAQ, both mirrored in the `FAQPage` schema. The answer box is the target of the `speakable` selector, so voice assistants read it aloud.
- Descriptive `alt` text on every product image and a `aria-label` describing each demo video.
- Semantic landmarks (`header`, `main`, `section` with `aria-label`, `footer`) and a skip link.

## Why the answer box and llms files matter for GEO

Answer engines quote short, factual, self-contained passages. The `#answer-box` section, the `FAQPage` schema, and `llms-full.txt` all give an engine a clean block it can lift verbatim, with a consistent one-line definition of Touchigh and a suggested citation. Keep those three in sync when the positioning changes.

## Maintenance checklist

When you update the site, keep these aligned:

1. If the one-line definition of Touchigh changes, update it in: the meta description, the `Organization` JSON-LD `description`, the `#answer-box` lead, `llms.txt`, and the "Suggested citation" in `llms-full.txt`.
2. If you add or rename a product, update: the `SoftwareApplication` blocks, the demo switcher, the products section, `llms.txt`, `llms-full.txt`, and `feed.xml`.
3. If you add a page, add it to `sitemap.xml` and `feed.xml`.
4. Change every `lastmod` / `lastBuildDate` / `pubDate` when content changes materially.
5. Re-validate JSON-LD after edits at https://validator.schema.org and https://search.google.com/test/rich-results.
6. Keep the `security.txt` `Expires` date in the future.

## Deployment notes

- The site is static. Serve the whole folder as-is. `CNAME` targets `touchigh.ai`.
- Serve `.mp4` as `video/mp4` and `.webm` as `video/webm`. Most static hosts (including GitHub Pages) do this automatically.
- Make sure `/.well-known/security.txt` is reachable (some hosts hide dot-folders; GitHub Pages serves them).
- The demo videos are muted, `loop`, `playsinline` and autoplay only for the visible clip; the rest use `preload="none"` so the page stays light on mobile.

## Verify quickly

- Rich results / schema: https://search.google.com/test/rich-results
- Schema.org validator: https://validator.schema.org
- Open Graph preview: https://www.opengraph.xyz
- Ask the engines directly: "What is Touchigh?" in ChatGPT, Perplexity and Google AI Overviews, and check the answer matches `llms-full.txt`.
