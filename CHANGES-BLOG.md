# ToucHigh — blog, login and SEO upgrade (16 Oct 2026)

## Structure
- **Main · Blog · Log in.** The main nav is now 平台实景 · 产品 · 常见问题 · ToucHigh PRO · **博客/Blog**, with a **登录/Log in** button (→ https://pro.touchigh.ai) next to 预约沟通. The same change is on `/pro/`. `/login/` redirects to pro.touchigh.ai.
- **Blog:** `/blog/` hub (zh/en toggle like the main site) with language filters (简体中文 30 · English 20 · 繁體中文 5 · Español 5) and topic filters. There are 60 articles at `/blog/<slug>/`. T51–T60 form a series on SEO/AEO/GEO and social thought leadership for Chinese factories and e-commerce companies going overseas.
- Home page: new "博客精选 / From the blog" section (3 Chinese + 3 English articles).
- **Kirill Lepikhin:** upgraded bilingual bio and role, using only verified facts: six peer-reviewed ACM papers (TOIS 2025, SIGIR 2026, WWW 2025, WSDM 2021/2023, ACM MM 2018), co-founder and CTO of SOMIN since 2017 (2020 Gartner Cool Vendor, platforms used by McDonald's, P&G and Puma). It links to his Semantic Scholar profile and is mirrored in JSON-LD, the FAQ, llms files and humans.txt. A new "peer-reviewed research" list under the founders panel has the six papers and their DOI links. Kirill's personal "over a decade" line was dropped because his documented record covers about nine years. The team-level "more than a decade" lead paragraph is your original copy and was left as is.

## SEO / AEO / GEO
- Every article has: title, description, canonical, Open Graph and Twitter cards with a 1200×630 brand preview, BlogPosting JSON-LD (with citations and speakable), FAQPage and BreadcrumbList. The hub has Blog JSON-LD.
- The site-level social preview `og-cover.jpg` was redesigned (the old one showed a placeholder mock-up). An English version is at `og-cover-en.jpg`. 192/512 app icons were added to the manifest.
- `sitemap.xml` keeps the original home and PRO entries (with the video sitemap) and adds the blog hub and all 60 articles with image entries. `/blog/feed.xml` is new and `/feed.xml` has a blog item. `llms.txt`, `llms-full.txt` and `ai.txt` now include the blog and research.
- GA G-XCXZPEFP94 is on every new page, with `book_call_click`, `login_click`, `blog_click` and `blog_filter` events.
