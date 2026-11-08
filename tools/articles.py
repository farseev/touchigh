#!/usr/bin/env python3
"""Render blog articles from i18n/articles/<slug>/ (stdlib only).

  meta.json   shared data: num, cat, hero, published, sources, related, landing, original language
  <hl>.txt    one file per language, sections separated by lines "== name ==":
              title, seo_title, desc, dek, section, tags (a | b), keywords, q, a, read, note,
              insight_quote, insight, prop_eyebrow, prop_intro, prop_items (- lines), prop_outro,
              takeaways (- lines), faq (Q:/A: lines), alt (optional hero alt), body (HTML)

URLs: original language at /blog/<slug>/, the other of zh-Hans/en at /blog/zh|en/<slug>/,
every further language at /blog/<code>/<slug>/.
The HTML reproduces the existing article template (assets/css/touchigh-blog.css).
"""
import html
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(__file__))
from site_config import L, ORDER, SITE  # noqa: E402
import langmenu  # noqa: E402
from registry import registry  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ART = os.path.join(ROOT, "i18n", "articles")
CAL = "https://calendly.com/a-touchigh/30min"
E = html.escape
UI = json.load(open(os.path.join(ROOT, "i18n", "ui.json"), encoding="utf-8"))
CJK = ("zh-Hans", "zh-Hant", "ja")
LANDING = {"supplier": "/supplier-ai-visibility/", "amazon": "/amazon-ads-autopilot/"}


def a(s):
    return E(s, quote=True)


def parse(path):
    d, cur, buf = {}, None, []
    for line in open(path, encoding="utf-8").read().split("\n"):
        m = re.match(r"^== (\w+) ==\s*$", line)
        if m:
            if cur:
                d[cur] = "\n".join(buf).strip()
            cur, buf = m.group(1), []
        else:
            buf.append(line)
    if cur:
        d[cur] = "\n".join(buf).strip()
    for k in ("takeaways", "prop_items"):
        if k in d:
            d[k] = [x[2:].strip() for x in d[k].split("\n") if x.startswith("- ")]
    if "faq" in d:
        qa, q = [], None
        for x in d["faq"].split("\n"):
            if x.startswith("Q: "):
                q = x[3:].strip()
            elif x.startswith("A: ") and q:
                qa.append((q, x[3:].strip()))
                q = None
        d["faq"] = qa
    d["tags"] = [t.strip() for t in d.get("tags", "").split("|") if t.strip()]
    return d


def article_langs(slug):
    return [hl for hl in ORDER if os.path.exists(os.path.join(ART, slug, hl + ".txt"))]


def url_for(slug, hl, meta):
    if hl == meta["original"]:
        return "/blog/%s/" % slug
    if hl in ("zh-Hans", "en"):
        return "/blog/%s/%s/" % ("zh" if hl == "zh-Hans" else "en", slug)
    return "/blog/%s/%s/" % (L[hl]["code"], slug)


def fmt_date(iso, hl):
    y, m, d = int(iso[:4]), int(iso[5:7]), int(iso[8:10])
    u = UI[hl]
    months = u.get("months")
    return u["date"].format(y=y, m=m, d=d, M=(months[m - 1] if months else m))


def home_url(hl):
    return "/" if hl == "zh-Hans" else ("/?lang=en" if hl == "en" else "/%s/" % L[hl]["code"])


def pro_url(hl):
    return "/pro/" if hl == "zh-Hans" else ("/pro/?lang=en" if hl == "en" else "/%s/pro/" % L[hl]["code"])


def hub_url(hl):
    return "/blog/" if hl == "zh-Hans" else "/blog/%s/" % L[hl]["code"]


def landing_url(key, hl):
    base = LANDING[key]
    return base if hl == "zh-Hans" else (base + "?lang=en" if hl == "en" else "/%s%s" % (L[hl]["code"], base))


def text_len(htm, hl):
    t = html.unescape(re.sub(r"<[^>]+>", " ", htm))
    if hl in ("zh-Hans", "zh-Hant", "ja"):
        return len(re.findall(r"[\u3040-\u30ff\u3400-\u9fff]", t)) + len(re.findall(r"[A-Za-z0-9]+", t))
    if hl == "th":
        return len(t.replace(" ", "")) // 6
    return len(t.split())


def number_h2(body):
    """Give every <h2> an id s1..sN; return body and TOC entries."""
    toc, n = [], [0]

    def rep(m):
        n[0] += 1
        toc.append(("s%d" % n[0], re.sub(r"<[^>]+>", "", m.group(2))))
        return '<h2 id="s%d"%s>%s</h2>' % (n[0], m.group(1), m.group(2))
    body = re.sub(r"<h2(?: id=\"[^\"]*\")?([^>]*)>(.*?)</h2>", rep, body)
    return body, toc


def uc_line(tmpl, href, loc, kind):
    ev = "landing_click" if kind == "landing" else "pro_click"
    return tmpl.replace("<a>", '<a href="%s" onclick="try{gtag(\'event\',\'%s\',{location:\'%s\'})}catch(e){}">' % (href, ev, loc))


def _exists_or(path, fallback):
    f = os.path.join(ROOT, path.split("?")[0].strip("/"), "index.html")
    return path if os.path.exists(f) else fallback


def usecase_html(landing, hl, loc):
    u = UI[hl]
    fb = "zh-Hans" if hl == "zh-Hant" else "en"
    lu = _exists_or(landing_url(landing, hl), landing_url(landing, fb))
    pu = _exists_or(pro_url(hl), pro_url(fb))
    return ('<p class="uc">%s %s</p>' % (uc_line(u["uc_" + landing], lu, loc, "landing"), uc_line(u["uc_pro"], pu, loc, "pro")))


def card_html(info, hl_page, cat_label=None):
    """Related-article card in the existing template."""
    lang = info["hl"]
    badge = L[lang]["name"]
    return ('<a class="card" href="%s"><div class="im"><picture><source type="image/webp" srcset="/assets/blog/hero/%s-768.webp">'
            '<img src="/assets/blog/hero/%s.jpg" alt="%s" width="1536" height="1024" loading="lazy"></picture></div>'
            '<div class="tx" lang="%s"%s><div class="eyebrow">%s</div><h3>%s</h3><p>%s</p><div class="meta"><span class="lg">%s</span><span>%s</span></div></div></a>'
            % (info["path"], info["hero"], info["hero"], a(info["alt"]), lang, ' dir="rtl"' if L[lang]["dir"] == "rtl" else "",
               E(cat_label or info["eyebrow"]), E(info["title"]), E(info["dek"]), badge, E(info["read"])))


def related_pick(rel_slugs, hl, reg):
    out = []
    for s in rel_slugs:
        e = reg.get(s)
        if not e:
            continue
        pg = e["pages"].get(hl) or e["pages"].get("en") or e["pages"].get("zh-Hans")
        if pg:
            out.append(pg)
    return out[:3]


def hero_alt(hero, hl, reg):
    """Alt text of the existing article that owns this hero image, in hl (fallback en)."""
    for want in (hl, "en"):
        for e in reg.values():
            p = e["pages"].get(want)
            if p and p["hero"] == hero and p["alt"]:
                return p["alt"]
    return ""


def render(slug, hl, meta, reg, versions):
    d = parse(os.path.join(ART, slug, hl + ".txt"))
    u = UI[hl]
    dr = L[hl]["dir"]
    path = versions[hl]
    url = SITE + path
    num = meta["num"].upper()
    og = "/assets/blog/og/%s%s.jpg" % (meta["num"], "" if hl == "zh-Hans" else "-" + L[hl]["code"])
    if not os.path.exists(os.path.join(ROOT, og.lstrip("/"))):
        og = "/assets/blog/og/%s-en.jpg" % meta["num"]
    pub = meta["published"]
    mod = meta.get("modified", pub)
    hero = meta["hero"]
    alt = d.get("alt") or meta.get("alt", {}).get(hl, "") or hero_alt(hero, hl, reg)
    body, toc = number_h2(d["body"])
    words = text_len(" ".join([body, d["a"], d["insight"], " ".join(d["takeaways"]), " ".join(q + " " + x for q, x in d["faq"])]), hl)
    tags = d["tags"]
    srcs = meta.get("sources", [])
    orig = meta["original"]
    trans = {"@type": "BlogPosting", "@id": SITE + versions[orig] + "#article", "inLanguage": orig}
    posting = {"@context": "https://schema.org", "@type": "BlogPosting", "@id": url + "#article", "url": url, "mainEntityOfPage": url,
               "headline": d["title"], "alternativeHeadline": d["seo_title"].replace(" | ToucHigh", ""), "description": d["desc"], "abstract": d["a"],
               "image": [SITE + og, SITE + "/assets/blog/hero/%s.jpg" % hero], "datePublished": pub, "dateModified": mod, "inLanguage": hl,
               "author": {"@type": "Organization", "name": u["author"], "url": SITE + hub_url(hl)},
               "publisher": {"@type": "Organization", "@id": SITE + "/#org", "name": "ToucHigh", "url": SITE + "/",
                             "logo": {"@type": "ImageObject", "url": SITE + "/apple-touch-icon.png", "width": 180, "height": 180}},
               "articleSection": d["section"], "keywords": d["keywords"], "wordCount": words, "timeRequired": "PT%sM" % d["read"],
               "isPartOf": {"@type": "Blog", "@id": SITE + hub_url(hl) + "#blog", "name": u["blog_name"]},
               "about": [{"@type": "Thing", "name": t} for t in tags],
               "citation": [{"@type": "CreativeWork", "name": s["name"], "url": s["url"], **({"datePublished": s["date"]} if s.get("date") else {}),
                             "publisher": {"@type": "Organization", "name": s["publisher"]}} for s in srcs],
               "speakable": {"@type": "SpeakableSpecification", "cssSelector": [".answer-box", ".takeaways"]}}
    if hl == orig:
        posting["workTranslation"] = [{"@type": "BlogPosting", "@id": SITE + versions[h] + "#article", "inLanguage": h} for h in ORDER if h in versions and h != orig]
    else:
        posting["translationOfWork"] = trans
    faq = {"@context": "https://schema.org", "@type": "FAQPage", "inLanguage": hl,
           "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": re.sub(r"<[^>]+>", "", aa)}} for q, aa in d["faq"]]}
    crumbs = {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": 1, "name": "ToucHigh", "item": SITE + home_url(hl)},
        {"@type": "ListItem", "position": 2, "name": u["blog"], "item": SITE + hub_url(hl)},
        {"@type": "ListItem", "position": 3, "name": d["title"], "item": url}]}
    J = lambda o: json.dumps(o, ensure_ascii=False, separators=(",", ":"))  # noqa: E731
    font_link = "https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap"
    if hl in ("zh-Hans",):
        font_link = "https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&family=Noto+Sans+SC:wght@400;500;700;800&display=swap"
    elif hl == "zh-Hant":
        font_link = "https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&family=Noto+Sans+TC:wght@400;500;700;800&display=swap"
    elif hl in ("ja", "ko", "th", "hi", "ar"):
        fam = {"ja": "Noto+Sans+JP", "ko": "Noto+Sans+KR", "th": "Noto+Sans+Thai", "hi": "Noto+Sans+Devanagari", "ar": "Noto+Sans+Arabic"}[hl]
        font_link = "https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&family=%s:wght@400;500;700;800&display=swap" % fam
    rss = "/blog/feed.xml" if hl == "zh-Hans" else ("/blog/en/feed.xml" if hl == "en" else None)
    head = ['<!DOCTYPE html>', '<html lang="%s"%s>' % (hl, ' dir="rtl"' if dr == "rtl" else ""), "<head>", '<meta charset="utf-8">', "",
            '<meta name="viewport" content="width=device-width, initial-scale=1">',
            "<title>%s</title>" % E(d["seo_title"]),
            '<meta name="description" content="%s">' % a(d["desc"]),
            '<link rel="canonical" href="%s">' % url,
            '<meta name="robots" content="index, follow, max-image-preview:large, max-snippet:-1, max-video-preview:-1">',
            '<meta name="author" content="ToucHigh">', '<meta name="theme-color" content="#FF642D">', '<meta name="format-detection" content="telephone=no">',
            '<meta name="keywords" content="%s">' % a(d["keywords"]),
            langmenu.hreflang_html(versions), "",
            '<meta property="og:type" content="article">', '<meta property="og:site_name" content="ToucHigh">',
            '<meta property="og:url" content="%s">' % url, '<meta property="og:title" content="%s">' % a(d["title"]),
            '<meta property="og:description" content="%s">' % a(d["desc"]), '<meta property="og:image" content="%s%s">' % (SITE, og),
            '<meta property="og:image:type" content="image/jpeg">', '<meta property="og:image:width" content="1200">', '<meta property="og:image:height" content="630">',
            '<meta property="og:image:alt" content="%s">' % a(d["title"]), '<meta property="og:locale" content="%s">' % L[hl]["locale"]]
    head += ['<meta property="og:locale:alternate" content="%s">' % L[h]["locale"] for h in ORDER if h in versions and h != hl]
    head += ['<meta property="article:published_time" content="%s">' % pub, '<meta property="article:modified_time" content="%s">' % mod,
             '<meta property="article:section" content="%s">' % a(d["section"])]
    head += ['<meta property="article:tag" content="%s">' % a(t) for t in tags]
    head += ['<meta name="twitter:card" content="summary_large_image">', '<meta name="twitter:title" content="%s">' % a(d["title"]),
             '<meta name="twitter:description" content="%s">' % a(d["desc"]), '<meta name="twitter:image" content="%s%s">' % (SITE, og),
             '<meta name="twitter:image:alt" content="%s">' % a(d["title"]),
             '<link rel="icon" href="/favicon.ico" sizes="any">', '<link rel="icon" type="image/png" sizes="32x32" href="/favicon-32.png">',
             '<link rel="icon" type="image/png" sizes="16x16" href="/favicon-16.png">', '<link rel="icon" type="image/svg+xml" href="/touchigh_spark.svg">',
             '<link rel="apple-touch-icon" href="/apple-touch-icon.png">', '<link rel="manifest" href="/site.webmanifest">']
    if rss:
        head.append('<link rel="alternate" type="application/rss+xml" title="%s" href="%s">' % (a(u["blog_name"]), rss))
    head += ['<link rel="alternate" type="text/plain" title="LLM index" href="/llms.txt">',
             '<link rel="preconnect" href="https://fonts.googleapis.com">', '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>',
             '<link href="%s" rel="stylesheet">' % font_link, '<link rel="stylesheet" href="/assets/css/touchigh-blog.css">',
             '<link href="https://assets.calendly.com/assets/external/widget.css" rel="stylesheet">',
             '<script src="https://assets.calendly.com/assets/external/widget.js" async></script>',
             "<!-- Google tag (gtag.js) -->", '<script async src="https://www.googletagmanager.com/gtag/js?id=G-XCXZPEFP94"></script>',
             "<script>\n  window.dataLayer = window.dataLayer || [];\n  function gtag(){dataLayer.push(arguments);}\n  gtag('js', new Date());\n  gtag('config', 'G-XCXZPEFP94');\n</script>",
             '<script type="application/ld+json">%s</script>' % J(posting), '<script type="application/ld+json">%s</script>' % J(faq),
             '<script type="application/ld+json">%s</script>' % J(crumbs), "", langmenu.ASSETS[0], langmenu.ASSETS[1],
             '<link rel="stylesheet" href="/assets/css/blog-extra.css">', "</head>"]
    menu = langmenu.menu_html(hl, versions)
    others = "".join('<a href="%s" hreflang="%s" lang="%s"%s onclick="try{localStorage.setItem(\'tl\',\'%s\')}catch(e){}">%s</a>'
                     % (versions[h], h, h, ' dir="rtl"' if L[h]["dir"] == "rtl" else "", "zh" if h == "zh-Hans" else h.lower(), L[h]["name"])
                     for h in ORDER if h in versions and h != hl)
    loc = "article_" + num
    tk = "".join("<li>%s</li>" % x for x in d["takeaways"])
    pi = "".join("<li>%s</li>" % x for x in d["prop_items"])
    faqh = "".join('<details%s><summary>%s</summary><p>%s</p></details>' % (" open" if i == 0 else "", E(q, quote=False), aa) for i, (q, aa) in enumerate(d["faq"]))
    srch = "".join('<li><a href="%s" rel="noopener" target="_blank">%s</a> — %s%s</li>' % (a(s["url"]), E(s["name"]), E(s["publisher"]), (", " + s["date"]) if s.get("date") else "") for s in srcs)
    toch = "".join('<a href="#%s">%s</a>' % (i, E(t, quote=False)) for i, t in toc)
    rel = related_pick(meta.get("related", []), hl, reg)
    relh = "".join(card_html(r, hl) for r in rel)
    bodyh = """<body>
<a class="skip" href="#main">{skip}</a>
<header class="nav">
  <div class="wrap nav-in">
    <a class="brand" href="/" aria-label="ToucHigh"><img src="/touchigh_spark.svg" alt="ToucHigh" width="25" height="25"><span>ToucHigh</span></a>
    <nav class="nav-links" aria-label="Primary">
      <a href="{home}">{t_home}</a>
      <a href="{homeh}#products">{products}</a>
      <a href="{homeh}#faq">{faq_nav}</a>
      <a href="{pro}">ToucHigh PRO</a>
      <a href="{hub}" class="on">{blog}</a>
    </nav>
    <div class="nav-right">
      {menu}
      <a class="btn btn-ghost" href="https://pro.touchigh.ai" rel="noopener" onclick="try{{gtag('event','login_click',{{location:'blog_nav'}})}}catch(e){{}}">{login}</a>
      <a class="btn btn-primary" href="{cal}" target="_blank" rel="noopener" onclick="return book(event,'blog_nav')">{book}</a>
      <button class="menu-btn" aria-label="Menu" aria-expanded="false" onclick="var n=document.querySelector('.nav-links');var o=n.classList.toggle('open');this.setAttribute('aria-expanded',o?'true':'false')">☰</button>
    </div>
  </div>
</header>
<main id="main">
<article class="wrap">
  <nav class="crumbs" aria-label="Breadcrumb"><a href="{home}">{t_home}</a><span>/</span><a href="{hub}">{blog}</a><span>/</span><span>{section}</span></nav>
  <header class="a-head">
    <div class="eyebrow">{section}</div>
    <h1>{title}</h1>
    <p class="dek">{dek}</p>
    <div class="a-meta"><b>{author}</b><span>{published}</span><span>{read}</span><span class="lang-badge">{lname}</span></div>
    <div class="a-langs">{also}{others}</div>
  </header>
  <figure class="hero-fig"><picture><source type="image/webp" srcset="/assets/blog/hero/{hero}-768.webp 768w, /assets/blog/hero/{hero}-1536.webp 1536w" sizes="(max-width:1250px) 100vw, 1152px"><img src="/assets/blog/hero/{hero}.jpg" alt="{alt}" width="1536" height="1024" fetchpriority="high"></picture></figure>
  <div class="layout">
    <div class="col">
      <section class="answer-lead answer-box" aria-label="{qeyebrow}"><span class="qm">“</span><div><div class="eyebrow">{qeyebrow}</div><p class="q">{q}</p><p class="ans"><b>{short}</b>{ans}</p></div></section>
      <section class="kt takeaways"><h2>{t_takeaways}</h2><ul>{tk}</ul></section>
      <div class="prose">{body}</div>
      <aside class="insight" aria-label="{t_insight}"><div class="eyebrow">{t_insight}</div><blockquote>{iq}</blockquote><p>{ins}</p></aside>
      <section class="prop" aria-label="{help}">
        <div class="ph"><div class="eyebrow">{peb}</div><h2>{help}</h2></div>
        <div class="pb prose"><p>{pintro}</p><ul>{pi}</ul><p>{pout}</p>{uc}</div>
        <div class="pa"><a class="btn btn-primary" href="{cal}" target="_blank" rel="noopener" onclick="return book(event,'{loc}')">{book30}</a><a class="btn btn-ghost" href="https://pro.touchigh.ai" rel="noopener" onclick="try{{gtag('event','login_click',{{location:'{loc}'}})}}catch(e){{}}">{login_th}</a></div>
      </section>
      <section class="faq" aria-label="{t_faq}"><h2>{t_faq}</h2>{faqh}</section>
      <section class="srcs"><h2>{t_sources}</h2><ol>{srch}</ol></section>
      <p class="note"><b>{why}</b>{note}</p>
    </div>
    <aside class="side"><div class="side-in">
      <nav class="toc" aria-label="{t_toc}"><h4>{t_toc}</h4>{toch}</nav>
      <div class="side-cta"><h4>ToucHigh</h4><p>{side}</p><a class="btn btn-primary" href="{cal}" target="_blank" rel="noopener" onclick="return book(event,'article_side')">{book}</a><a class="btn btn-ghost on-dark" href="https://pro.touchigh.ai" rel="noopener">{login}</a></div>
    </div></aside>
  </div>
</article>
<section class="related"><div class="wrap"><h2>{t_related}</h2>
  <div class="grid">{relh}</div>
  <a class="btn btn-ghost" href="{hub}">{back}</a><div style="height:50px"></div>
</div></section>
</main>
<section class="final" aria-label="Get started">
  <div class="eyebrow">ToucHigh</div>
  <h2>{side}</h2>
  <p>{final_p}</p>
  <div class="row"><a class="btn btn-primary" href="{cal}" target="_blank" rel="noopener" onclick="return book(event,'blog_final')">{book30}</a><a class="btn btn-ghost" href="https://pro.touchigh.ai" rel="noopener" onclick="try{{gtag('event','login_click',{{location:'blog_final'}})}}catch(e){{}}">{login_th}</a></div>
</section>
<footer>
  <div class="wrap">
    <div class="foot-grid">
      <div><a class="brand" href="/"><img src="/touchigh_spark.svg" alt="" width="24" height="24"><span>ToucHigh</span></a><p style="margin-top:12px;max-width:38ch;font-size:14px">{tagline}</p></div>
      <div><h4>ToucHigh</h4><a href="{home}">{t_home}</a><a href="{homeh}#geo">GEO Autopilot</a><a href="{homeh}#social">Social Autopilot</a><a href="{pro}">ToucHigh PRO</a></div>
      <div><h4>{blog}</h4><a href="{hub}">{blog}</a>{rssl}<a href="/llms.txt">llms.txt</a><a href="https://dl.acm.org/doi/10.1145/3805712.3808371" target="_blank" rel="noopener">ACM SIGIR ↗</a></div>
      <div><h4>{login}</h4><a href="https://pro.touchigh.ai" rel="noopener">pro.touchigh.ai</a><a href="{cal}" target="_blank" rel="noopener" onclick="return book(event,'blog_footer')">{book}</a></div>
    </div>
    <div class="foot-bot"><span>© 2026 ToucHigh</span><span>touchigh.ai</span></div>
  </div>
</footer>
<script>
window.book=function(e,loc){{try{{gtag('event','book_call_click',{{location:loc}})}}catch(_){{}}if(window.Calendly&&Calendly.initPopupWidget){{if(e&&e.preventDefault)e.preventDefault();Calendly.initPopupWidget({{url:'{cal}'}});return false;}}return true;}};
</script>
</body>
</html>
""".format(skip=u["skip"], home=home_url(hl), homeh=home_url(hl).replace("?lang=en", "?lang=en"), t_home=u["home"], products=u["products"],
           faq_nav=u["faq_nav"], pro=pro_url(hl), hub=hub_url(hl), blog=u["blog"], menu=menu, login=u["login"], cal=CAL, book=u["book"],
           section=E(d["section"]), title=E(d["title"]), dek=E(d["dek"]), author=u["author"],
           published=u["published"].format(d='<time datetime="%s">%s</time>' % (pub, fmt_date(pub, hl))),
           read=u["read"].format(n=d["read"]), lname=L[hl]["name"], also=u["also"] if others else "", others=others,
           hero=hero, alt=a(alt), qeyebrow=u["qeyebrow"], q=E(d["q"]), short=u["short"], ans=E(d["a"]), t_takeaways=u["takeaways"], tk=tk,
           body=body, t_insight=u["insight"], iq=E(d["insight_quote"]), ins=E(d["insight"]), help=u["help"], peb=E(d.get("prop_eyebrow", "GEO Autopilot · Social Autopilot · Ads")),
           pintro=d["prop_intro"], pi=pi, pout=d["prop_outro"], uc=usecase_html(meta["landing"], hl, loc), loc=loc, book30=u["book30"],
           login_th=u["login_th"], t_faq=u["faq"], faqh=faqh, t_sources=u["sources"], srch=srch, why=u["why"], note=E(d["note"]), t_toc=u["toc"],
           toch=toch, side=E(u["side"]), t_related=u["related"], relh=relh, back=u["back"], final_p=E(u["final_p"]), tagline=E(u["tagline"]),
           rssl=('<a href="%s">RSS</a>' % rss) if rss else "")
    homeq = home_url(hl)
    if "?lang=en" in homeq:
        bodyh = bodyh.replace('href="/?lang=en#', 'href="/?lang=en#')
    return "\n".join(head) + "\n" + bodyh, d, words


def build_all(slugs=None, langs=None):
    reg = registry()
    out = {}
    for slug in sorted(os.listdir(ART)):
        if slugs and slug not in slugs:
            continue
        meta = json.load(open(os.path.join(ART, slug, "meta.json"), encoding="utf-8"))
        hls = article_langs(slug)
        versions = {h: url_for(slug, h, meta) for h in hls}
        for h in hls:
            if langs and h not in langs:
                continue
            page, d, words = render(slug, h, meta, reg, versions)
            f = os.path.join(ROOT, versions[h].strip("/"), "index.html")
            os.makedirs(os.path.dirname(f), exist_ok=True)
            open(f, "w", encoding="utf-8").write(page)
            out[(slug, h)] = (versions[h], d, words)
    return out


if __name__ == "__main__":
    res = build_all(sys.argv[1:] or None)
    for (slug, h), (p, d, w) in sorted(res.items()):
        print("%-48s %-8s %5d  %s" % (slug, h, w, p))
