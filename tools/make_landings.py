#!/usr/bin/env python3
"""Build the two bilingual (zh-Hans default / ?lang=en) landing pages from the /pro/ design system.

  /supplier-ai-visibility/  supplier visibility in ChatGPT / AI search for Chinese factories and B2B suppliers
  /amazon-ads-autopilot/    Amazon seller ads / AI ad agent use case

Copy only restates capabilities the site already states (index.html, /pro/, llms.txt).
The CSS is copied from pro/index.html so the design system stays identical.
Run from the repo root:  python3 tools/make_landings.py
"""
import html
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(__file__))
from site_config import SITE  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CAL = "https://calendly.com/a-touchigh/30min"
E = html.escape


def a(s):
    return E(s, quote=True)


def t(tag, en, zh, attrs="", raw=False):
    """Bilingual element in the site's data-en/data-zh system (Chinese rendered by default)."""
    body = zh if raw else E(zh, quote=False)
    kind = "-html" if raw else ""
    return '<%s%s data-en%s="%s" data-zh%s="%s">%s</%s>' % (tag, (" " + attrs) if attrs else "", kind, a(en), kind, a(zh), body, tag)


def book(loc, en, zh, cls="btn btn-primary", style=""):
    st = (' style="%s"' % style) if style else ""
    return ('<a class="%s"%s href="%s" target="_blank" rel="noopener" onclick="return book(event,\'%s\')">%s →</a>'
            % (cls, st, CAL, loc, t("span", en, zh)))


def pro_link(loc, en, zh, cls="btn btn-ghost"):
    return ('<a class="%s" href="/pro/" onclick="try{gtag(\'event\',\'pro_click\',{location:\'%s\'})}catch(e){}" '
            'data-en="%s" data-zh="%s">%s</a>' % (cls, loc, a(en), a(zh), E(zh)))


EXTRA_CSS = """
.frame video{width:100%;display:block}
.steps .card .k{color:var(--o)}
.tw{overflow-x:auto;border:1px solid var(--g100);border-radius:var(--r-m);background:#fff}
.tw table{width:100%;border-collapse:collapse;font-size:15px;min-width:640px}
.tw th,.tw td{padding:14px 16px;text-align:left;vertical-align:top;border-bottom:1px solid var(--g100)}
.tw th{background:var(--g50);font-weight:700;font-size:13px;letter-spacing:.04em;text-transform:uppercase;color:var(--g600)}
.tw tr:last-child td{border-bottom:none}
.reads{display:grid;grid-template-columns:repeat(3,1fr);gap:18px}
.reads a{display:block;border:1px solid var(--g100);border-radius:var(--r-m);padding:20px;background:#fff;color:var(--ink);transition:.15s}
.reads a:hover{border-color:var(--o);box-shadow:var(--sh)}
.reads a b{display:block;font-size:17px;line-height:1.35;margin-bottom:6px}
.reads a span{font-size:14px;color:var(--g500)}
.pro-band{background:var(--ink);color:#fff;border-radius:var(--r-l);padding:40px;display:grid;grid-template-columns:1.2fr 1fr;gap:36px;align-items:center}
.pro-band h2{color:#fff}.pro-band p{color:var(--g200)}
.pro-band .checks li{color:#fff}
.pro-band .btn-ghost{color:#fff;border-color:rgba(255,255,255,.3)}
@media(max-width:960px){.reads{grid-template-columns:1fr}.pro-band{grid-template-columns:1fr;padding:28px}}
"""

SCRIPT = """<script>
(function(){
  var CAL='%s';
  window.setLang=function(l){
    document.documentElement.lang=(l==='zh'?'zh-Hans':'en');
    document.querySelectorAll('[data-en]').forEach(function(el){var t=el.getAttribute('data-'+l); if(t!==null) el.textContent=t;});
    document.querySelectorAll('[data-en-html]').forEach(function(el){var t=el.getAttribute('data-'+l+'-html'); if(t!==null) el.innerHTML=t;});
    document.querySelectorAll('[data-href-en]').forEach(function(x){var h=x.getAttribute(l==='en'?'data-href-en':'data-href-zh'); if(h) x.setAttribute('href',h);});
    try{ localStorage.setItem('tl',l); }catch(e){}
    try{ gtag('event','language_switch',{language:l, page:'%s'}); }catch(e){}
  };
  window.book=function(e,loc){
    try{ gtag('event','book_call_click',{location:loc}); }catch(_){}
    if(window.Calendly && Calendly.initPopupWidget){ if(e&&e.preventDefault) e.preventDefault(); Calendly.initPopupWidget({url:CAL}); return false; }
    return true;
  };
  var p=new URLSearchParams(location.search).get('lang');
  var saved=null; try{ saved=localStorage.getItem('tl'); }catch(e){}
  if(p==='en'||p==='zh') setLang(p); else if(saved==='en') setLang('en'); else setLang('zh');
  document.querySelectorAll('.nav-links a').forEach(function(x){x.addEventListener('click',function(){
    var n=document.querySelector('.nav-links'); if(n) n.classList.remove('open');
    var mb=document.querySelector('.menu-btn'); if(mb) mb.setAttribute('aria-expanded','false');});});
})();
</script>"""


def faq_html(items):
    out = []
    for i, (qen, qzh, aen, azh) in enumerate(items):
        out.append('<details%s>%s%s</details>' % (" open" if i == 0 else "", t("summary", qen, qzh), t("p", aen, azh)))
    return '<div class="faq">' + "".join(out) + "</div>"


def jsonld(objs):
    return "\n".join('<script type="application/ld+json">%s</script>' % json.dumps(o, ensure_ascii=False) for o in objs)


def build(P):
    pro_html = open(os.path.join(ROOT, "pro/index.html"), encoding="utf-8").read()
    css = re.search(r"<style>.*?</style>", pro_html, re.S).group(0).replace("</style>", EXTRA_CSS + "</style>")
    url = SITE + P["path"]
    faq_ld = {"@context": "https://schema.org", "@type": "FAQPage", "@id": url + "#faq", "inLanguage": "zh-Hans",
              "mainEntity": [{"@type": "Question", "name": q[1], "acceptedAnswer": {"@type": "Answer", "text": q[3]}} for q in P["faq"]]}
    faq_ld_en = {"@context": "https://schema.org", "@type": "FAQPage", "@id": url + "?lang=en#faq", "inLanguage": "en",
                 "mainEntity": [{"@type": "Question", "name": q[0], "acceptedAnswer": {"@type": "Answer", "text": q[2]}} for q in P["faq"]]}
    lds = [
        {"@context": "https://schema.org", "@type": "Service", "@id": url + "#service", "name": P["service_name"],
         "serviceType": P["service_type"], "provider": {"@id": SITE + "/#org"}, "areaServed": P["area"],
         "audience": {"@type": "BusinessAudience", "name": P["audience"]}, "description": P["service_desc"],
         "url": url, "offers": P.get("offers")},
        faq_ld, faq_ld_en,
        {"@context": "https://schema.org", "@type": "BreadcrumbList", "@id": url + "#breadcrumb", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "ToucHigh", "item": SITE + "/"},
            {"@type": "ListItem", "position": 2, "name": P["crumb"], "item": url}]},
        {"@context": "https://schema.org", "@type": "WebPage", "@id": url + "#webpage", "url": url, "name": P["title_en"],
         "description": P["desc_en"], "isPartOf": {"@id": SITE + "/#website"}, "about": {"@id": url + "#service"},
         "inLanguage": "zh-Hans", "breadcrumb": {"@id": url + "#breadcrumb"},
         "speakable": {"@type": "SpeakableSpecification", "cssSelector": [".hero h1", ".hero .lead"]},
         "primaryImageOfPage": SITE + P["og"]},
    ]
    if not lds[0]["offers"]:
        del lds[0]["offers"]
    head = """<!DOCTYPE html>
<html lang="zh-Hans">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="{desc}">
<meta name="keywords" content="{kw}">
<link rel="canonical" href="{url}">
<meta name="robots" content="index, follow, max-image-preview:large, max-snippet:-1, max-video-preview:-1">
<meta name="author" content="ToucHigh">
<meta name="theme-color" content="#FF642D">
<meta name="format-detection" content="telephone=no">

<!-- hreflang -->
<link rel="alternate" hreflang="zh-Hans" href="{url}">
<link rel="alternate" hreflang="en" href="{url}?lang=en">
<link rel="alternate" hreflang="x-default" href="{url}">

<!-- Open Graph -->
<meta property="og:type" content="website">
<meta property="og:site_name" content="ToucHigh">
<meta property="og:url" content="{url}">
<meta property="og:title" content="{ogt}">
<meta property="og:description" content="{desc}">
<meta property="og:image" content="{site}{og}">
<meta property="og:image:type" content="image/jpeg">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="{ogt}">
<meta property="og:locale" content="zh_CN">
<meta property="og:locale:alternate" content="en_US">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{ogt}">
<meta name="twitter:description" content="{desc}">
<meta name="twitter:image" content="{site}{og}">
<meta name="twitter:image:alt" content="{ogt}">

<link rel="icon" href="/favicon.ico" sizes="any">
<link rel="icon" type="image/png" sizes="32x32" href="/favicon-32.png">
<link rel="icon" type="image/png" sizes="16x16" href="/favicon-16.png">
<link rel="icon" type="image/svg+xml" href="/touchigh_spark.svg">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
<link rel="manifest" href="/site.webmanifest">
<link rel="alternate" type="application/rss+xml" title="ToucHigh" href="/feed.xml">
<link rel="sitemap" type="application/xml" title="Sitemap" href="/sitemap.xml">
<link rel="alternate" type="text/plain" title="LLM index" href="/llms.txt">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&family=Noto+Sans+SC:wght@400;500;700;800;900&display=swap" rel="stylesheet">
<link href="https://assets.calendly.com/assets/external/widget.css" rel="stylesheet">
<script src="https://assets.calendly.com/assets/external/widget.js" async></script>
<!-- Google tag (gtag.js) -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-XCXZPEFP94"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){{dataLayer.push(arguments);}}
  gtag('js', new Date());
  gtag('config', 'G-XCXZPEFP94', {{page_title:'{gat}', page_path:'{path}'}});
</script>
{ld}
{css}
</head>""".format(title=E(P["title_zh"]), desc=a(P["desc_zh"]), kw=a(P["keywords"]), url=url, ogt=a(P["og_title_zh"]),
                   site=SITE, og=P["og"], gat=P["ga_title"], path=P["path"], ld=jsonld(lds), css=css)
    nav = """<body id="top">
<a class="skip" href="#main" data-en="Skip to content" data-zh="跳到正文">跳到正文</a>
<header class="nav">
  <div class="wrap nav-in">
    <a class="brand" href="/" aria-label="ToucHigh"><img src="/touchigh_spark.svg" alt="ToucHigh" width="25" height="25"><span>ToucHigh</span></a>
    <nav class="nav-links" aria-label="Primary">
      %s
      <a href="/pro/" data-href-zh="/pro/" data-href-en="/pro/?lang=en" onclick="try{gtag('event','pro_click',{location:'%s_nav'})}catch(e){}" data-en="ToucHigh PRO" data-zh="ToucHigh PRO">ToucHigh PRO</a>
      <a href="/blog/" data-href-zh="/blog/" data-href-en="/blog/en/" style="color:var(--o);font-weight:600" onclick="try{gtag('event','blog_click',{location:'%s_nav'})}catch(e){}" data-en="Blog" data-zh="博客">博客</a>
    </nav>
    <div class="nav-right">
      <div class="lang" role="group" aria-label="Language"><button data-lang="zh" class="active" onclick="setLang('zh')">中文</button><button data-lang="en" onclick="setLang('en')">EN</button></div>
      <a class="btn btn-ghost nav-login" href="https://pro.touchigh.ai" rel="noopener" onclick="try{gtag('event','login_click',{location:'%s_nav'})}catch(e){}" data-en="Log in" data-zh="登录">登录</a>
      <a class="btn btn-primary nav-cta" href="%s" target="_blank" rel="noopener" onclick="return book(event,'%s_nav')" data-en="Book a call" data-zh="预约沟通">预约沟通</a>
      <button class="menu-btn" aria-label="Menu" aria-expanded="false" onclick="var n=document.querySelector('.nav-links');var o=n.classList.toggle('open');this.setAttribute('aria-expanded',o?'true':'false')">☰</button>
    </div>
  </div>
</header>
<main id="main">
""" % ("\n      ".join(t("a", en, zh, 'href="#%s"' % hid) for hid, en, zh in P["nav"]), P["key"], P["key"], P["key"], CAL, P["key"])
    foot = """</main>
<footer>
  <div class="wrap">
    <div class="foot-grid">
      <div>
        <a class="brand" href="/"><img src="/touchigh_spark.svg" alt="" width="24" height="24"><span>ToucHigh</span></a>
        %s
      </div>
      <div>
        <h4 style="text-transform:none;letter-spacing:0">ToucHigh</h4>
        <a href="/" data-href-zh="/" data-href-en="/?lang=en" data-en="Home" data-zh="主页">主页</a>
        <a href="/#geo" data-en="GEO Autopilot" data-zh="GEO自动执行">GEO自动执行</a>
        <a href="/#social" data-en="Social Autopilot" data-zh="社媒自动化">社媒自动化</a>
        <a href="/pro/" data-href-zh="/pro/" data-href-en="/pro/?lang=en" onclick="try{gtag('event','pro_click',{location:'%s_footer'})}catch(e){}" data-en="ToucHigh PRO — outbound &amp; lead gen" data-zh="ToucHigh PRO——外拓与获客">ToucHigh PRO——外拓与获客</a>
      </div>
      <div>
        <h4 data-en="Use cases" data-zh="应用场景">应用场景</h4>
        <a href="/supplier-ai-visibility/" data-href-zh="/supplier-ai-visibility/" data-href-en="/supplier-ai-visibility/?lang=en" data-en="Supplier visibility in AI search" data-zh="供应商AI搜索可见度">供应商AI搜索可见度</a>
        <a href="/amazon-ads-autopilot/" data-href-zh="/amazon-ads-autopilot/" data-href-en="/amazon-ads-autopilot/?lang=en" data-en="Amazon ads for sellers" data-zh="亚马逊卖家广告">亚马逊卖家广告</a>
        <a href="/blog/" data-href-zh="/blog/" data-href-en="/blog/en/" data-en="Blog" data-zh="博客">博客</a>
      </div>
      <div>
        <h4 data-en="Get started" data-zh="开始">开始</h4>
        <a href="%s" target="_blank" rel="noopener" onclick="return book(event,'%s_footer')" data-en="30-min strategy call" data-zh="30分钟策略沟通">30分钟策略沟通</a>
        <a href="https://pro.touchigh.ai" rel="noopener" data-en="Log in" data-zh="登录">登录</a>
        <a href="/llms.txt" data-en="For AI engines (llms.txt)" data-zh="面向AI引擎（llms.txt）">面向AI引擎（llms.txt）</a>
      </div>
    </div>
    <div class="foot-bot">
      <span data-en="© 2026 ToucHigh · Measured with the ToucHigh engine" data-zh="© 2026 ToucHigh · 数据由ToucHigh引擎测得">© 2026 ToucHigh · 数据由ToucHigh引擎测得</span>
      <span data-en="Get found in US AI search. Run US social on autopilot." data-zh="被美国AI搜索发现，让美国社媒自动运转。">被美国AI搜索发现，让美国社媒自动运转。</span>
    </div>
  </div>
</footer>
%s
</body>
</html>
""" % (t("p", P["foot_en"], P["foot_zh"], 'style="margin-top:12px;max-width:38ch;font-size:14px"'), P["key"], CAL, P["key"], SCRIPT % (CAL, P["key"]))
    out = head + "\n" + nav + P["body"]() + foot
    path = os.path.join(ROOT, P["path"].strip("/"), "index.html")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, "w", encoding="utf-8").write(out)
    print("wrote", path)


def section(sid, label, inner, style=""):
    return '<section id="%s" aria-label="%s"%s>\n  <div class="wrap">\n%s\n  </div>\n</section>\n' % (
        sid, a(label), (' style="%s"' % style) if style else "", inner)


def sec_head(eb_en, eb_zh, h_en, h_zh, l_en=None, l_zh=None):
    s = '<div class="sec-head">' + t("div", eb_en, eb_zh, 'class="eyebrow"') + t("h2", h_en, h_zh)
    if l_en:
        s += t("p", l_en, l_zh, 'class="lead"')
    return s + "</div>"


def cards(items, cls="grid g3"):
    out = ['<div class="%s">' % cls]
    for k, hen, hzh, pen, pzh in items:
        out.append('<div class="card"><div class="k">%s</div>%s%s</div>' % (k, t("h3", hen, hzh), t("p", pen, pzh)))
    out.append("</div>")
    return "".join(out)


def checks(items):
    return '<ul class="checks">' + "".join('<li><span class="chk">✓</span>%s</li>' % t("span", en, zh) for en, zh in items) + "</ul>"


def reads(items):
    out = ['<div class="reads">']
    for zh_href, en_href, ten, tzh, sen, szh in items:
        if not os.path.exists(os.path.join(ROOT, zh_href.strip("/"), "index.html")):
            continue  # article not published yet
        out.append('<a href="%s" data-href-zh="%s" data-href-en="%s" onclick="try{gtag(\'event\',\'blog_click\',{location:\'landing_reads\'})}catch(e){}">%s%s</a>'
                   % (zh_href, zh_href, en_href, t("b", ten, tzh), t("span", sen, szh)))
    out.append("</div>")
    return "".join(out)


def video_frame(name, url, cap_en, cap_zh, aria):
    return ('<div class="frame"><div class="frame-bar"><span class="d"></span><span class="d"></span><span class="d"></span>'
            '<span class="url">%s</span></div><video poster="/media/%s.jpg" autoplay muted loop playsinline preload="metadata" aria-label="%s">'
            '<source src="/media/%s.webm" type="video/webm"><source src="/media/%s.mp4" type="video/mp4"></video></div>'
            '<p class="fine" style="margin-top:10px">%s</p>' % (url, name, a(aria), name, name, t("span", cap_en, cap_zh)))


# --------------------------------------------------------------------------------------------
# A. Supplier visibility in ChatGPT / AI search
# --------------------------------------------------------------------------------------------
SUP_FAQ = [
    ("What is supplier visibility in AI search?",
     "什么是“供应商的AI搜索可见度”？",
     "It is whether your factory is named, and described correctly, when a buyer asks ChatGPT, Perplexity, Gemini, Copilot or Google's AI Overviews and AI Mode to find or compare suppliers. It is the GEO (Generative Engine Optimization) side of a B2B website: being cited in the answer, not only ranking as a blue link.",
     "指的是：当采购商让ChatGPT、Perplexity、Gemini、Copilot或Google的AI概览、AI模式帮忙找供应商、比较供应商时，答案里有没有您的工厂，描述是否准确。这就是B2B官网的GEO（生成式引擎优化）：不只是排进蓝色链接，而是被写进AI的答案里。"),
    ("Can ToucHigh guarantee that ChatGPT will recommend our factory?",
     "ToucHigh能保证ChatGPT一定推荐我们的工厂吗？",
     "No one can guarantee what an AI assistant says. What ToucHigh does is measurable: it audits where you are invisible across ChatGPT, Perplexity, Google AI and Gemini, writes and ships the fixes (pages, answers, entity data) and GEO articles, and tracks your AI-citation share over time so you can see whether it moves. Predicted scores are a pre-launch proxy, not a guarantee.",
     "没有人能保证AI助手会说什么。ToucHigh做的是可衡量的事：审计您在ChatGPT、Perplexity、Google AI和Gemini中的曝光盲区，撰写并上线修复内容（页面、问答、实体数据）和GEO文章，并持续追踪AI引用份额，让您看清它有没有提升。预测评分是上线前的参考指标，不是保证。"),
    ("We already sell on Alibaba.com. Do we still need this?",
     "我们已经在阿里国际站开店了，还需要做这个吗？",
     "Usually yes. A marketplace store is an important inquiry channel, but the platform controls its format. Your own English website is the primary source you fully control, and AI answers often lean on it to check capacity, certifications and contact details. Keeping the two consistent works best.",
     "通常需要。平台店铺是重要的询盘渠道，但页面格式由平台决定。自己的英文官网是您完全掌控的一手信息源，AI在核实产能、认证和联系方式时常常会参考它。两者保持一致效果最好。"),
    ("Which AI engines does it cover?",
     "覆盖哪些AI引擎？",
     "GEO Autopilot covers the major AI answer engines, including ChatGPT, Perplexity, Google AI Overviews, Gemini and Copilot.",
     "GEO自动执行覆盖主流AI答案引擎，包括ChatGPT、Perplexity、Google AI概览、Gemini和Copilot。"),
    ("How do we start, and what does it cost?",
     "怎么开始？费用是多少？",
     "Book a 30-minute strategy call; it includes a live AI-visibility read. ToucHigh starts under USD 500 a month for the GEO plus Social bundle. ToucHigh PRO, the managed outbound service, is scoped on the call.",
     "预约一次30分钟策略沟通，其中包括一次在线AI可见度检测。ToucHigh的GEO+社媒套餐每月不到500美元起；托管式外拓服务ToucHigh PRO会在沟通中按需求定制方案。"),
]


def supplier_body():
    s = []
    s.append("""<!-- HERO -->
<section class="hero" aria-label="Intro">
  <div class="wrap">
    <div class="hero-grid">
      <div>
        %s
        <h1>%s %s</h1>
        %s
        <div class="hero-cta">%s %s</div>
        <div class="trust">%s<span class="sep">·</span>%s<span class="sep">·</span><a href="https://dl.acm.org/doi/10.1145/3805712.3808371" target="_blank" rel="noopener" style="color:var(--o-d);font-weight:600" data-en="Peer-reviewed at ACM SIGIR ↗" data-zh="经ACM SIGIR同行评审 ↗">经ACM SIGIR同行评审 ↗</a></div>
      </div>
      <div>%s</div>
    </div>
  </div>
</section>
""" % (t("div", "For Chinese factories & B2B suppliers · GEO Autopilot + ToucHigh PRO", "专为中国工厂与B2B供应商 · GEO自动执行 + ToucHigh PRO", 'class="eyebrow"'),
       t("span", "Buyers now ask AI for a supplier shortlist.", "海外采购商开始让AI列供应商短名单"),
       t("span", "Make sure your factory is on it.", "让您的工厂出现在名单上", 'class="accent"'),
       t("p", "Overseas buyers increasingly start sourcing by asking ChatGPT, Perplexity and Google's AI answers which factories to contact. ToucHigh shows where your factory is missing from those answers, writes and ships the citable pages that fix it, and tracks your AI-citation share. ToucHigh PRO can then turn that visibility into qualified conversations.",
         "越来越多海外买家寻源的第一步，是问ChatGPT、Perplexity和Google的AI答案该联系哪些工厂。ToucHigh帮您查清工厂在这些答案里缺席的地方，撰写并上线可被引用的页面来补上，并持续追踪AI引用份额；再由ToucHigh PRO把曝光转化为有效的商务沟通。", 'class="lead"'),
       book("supplier_hero", "Get your AI-visibility audit", "预约AI可见度诊断"),
       pro_link("supplier_hero", "See ToucHigh PRO", "了解ToucHigh PRO"),
       t("b", "Measured with the ToucHigh engine", "经ToucHigh引擎实测验证"),
       t("span", "GEO + Social from under $500 a month", "GEO+社媒套餐每月不到$500"),
       video_frame("article", "cloud.touchigh.ai/seo", "Recorded from the live product: one trending query turned into a full GEO article.",
                   "录制自真实产品：一个热门搜索问题被写成一篇完整的GEO文章。",
                   "ToucHigh turning a trending query into a GEO article, recorded from the live product.")))
    s.append("""<div class="band" aria-label="AI engines">
  <div class="wrap band-in">
    %s
    <span class="chip"><span class="dot"></span>ChatGPT</span><span class="chip"><span class="dot"></span>Perplexity</span><span class="chip"><span class="dot"></span>Google AI Overviews</span><span class="chip"><span class="dot"></span>Gemini</span><span class="chip"><span class="dot"></span>Copilot</span>
  </div>
</div>
""" % t("strong", "Where buyers now build supplier shortlists:", "采购商如今在这些地方筛选供应商："))
    s.append(section("problem", "The problem", sec_head(
        "The problem", "问题在哪", "A brochure website gives AI nothing to cite.", "只有公司简介的官网，AI无从引用。",
        "AI answers lean on information they can verify. Most factory sites state “advanced equipment and a professional team” while buyers ask about capacity, certificates, MOQ and lead times.",
        "AI答案倾向于引用可以核实的信息。很多工厂官网写的是“设备先进、团队专业”，而买家问的是产能、认证、起订量和交期。") +
        cards([
            ("01", "Proof locked away", "证据锁在内部", "Capacity, certificate numbers, materials and lead times sit in quotes, sales chats and Chinese-language PDFs, where AI cannot read them.",
             "产能、认证编号、材料工艺和交期散落在报价单、销售聊天记录和中文PDF里，AI读不到。"),
            ("02", "Inconsistent entity data", "实体信息不一致", "Your English name, address and main categories differ across the website, marketplace stores, LinkedIn and trade-show material, so AI cannot tell it is one company.",
             "公司英文名、地址和主营品类在官网、平台店铺、LinkedIn和展会资料里各不相同，AI难以判断这是同一家公司。"),
            ("03", "No view of the shortlist", "看不到短名单", "You don't know which buyer questions name a competitor instead of you, or whether AI describes your factory correctly.",
             "您不知道哪些买家问题的答案里出现的是竞争对手而不是您，也不知道AI对您工厂的描述是否准确。"),
        ])))
    s.append(section("how", "How ToucHigh helps", sec_head(
        "How ToucHigh helps", "ToucHigh怎么帮您", "Audit, then autopilot, then proof.", "先诊断，再自动执行，最后用数据证明。",
        "The main platform's workflow, pointed at the questions buyers ask when they look for a supplier.",
        "沿用ToucHigh主平台的工作流程，对准买家寻找供应商时提出的问题。") +
        '<div class="steps">' + cards([
            ("01", "Audit", "诊断", "See where your factory is invisible across ChatGPT, Perplexity, Google AI and Gemini. ToucHigh also reads competitors' ads and organic content to show the gap.",
             "查清您的工厂在ChatGPT、Perplexity、Google AI和Gemini中的曝光盲区；ToucHigh还会分析竞争对手的广告和自然内容，标出差距。"),
            ("02", "Fix and publish", "修复并发布", "ToucHigh writes and ships the fixes: pages, answers and entity data, plus programmatic GEO articles built around sourcing questions as they trend.",
             "ToucHigh撰写并上线修复内容：页面、问答和实体数据，并围绕正在升温的采购问题批量生成GEO文章。"),
            ("03", "Score before it ships", "发布前先评分", "Every concept is scored for predicted clickability before it goes live, so weak pages and posts don't go out.",
             "每条内容上线前都先做点击率预测评分，表现弱的页面和帖子不会发出去。"),
            ("04", "Prove the lift", "证明效果", "Your AI-citation share is tracked continuously, so you can see which pages start getting cited instead of guessing.",
             "持续追踪AI引用份额，看清哪些页面开始被引用，而不是靠猜。"),
        ], "grid g4") + "</div>" +
        '<div class="two-col" style="margin-top:34px"><div>' +
        t("h3", "Plus native US-English social for your founder and brand", "再加上地道美式英语的创始人与品牌社媒") +
        t("p", "Social Media Manager Autopilot writes, schedules and publishes native US-English posts and thought-leadership content, each scored for predicted engagement before it is scheduled.",
          "社媒自动驾驶模块撰写、排期并发布地道美式英语的帖子和行业洞见内容，每条在排期前都会做互动率预评分。", 'style="color:var(--g500);margin-top:10px"') +
        "</div><div>" + checks([
            ("Native US-English posts, articles and creatives, on brand", "地道美式英语的帖子、文章和创意，符合品牌调性"),
            ("Thought-leadership and organic content, written to sound like a person", "行业洞见与自然内容，读起来像真人所写"),
            ("Approve each one, or let it publish on autopilot", "可以逐条审批，也可以交给自动发布"),
        ]) + "</div></div>", "padding-top:30px"))
    s.append(section("citable", "What citable looks like", sec_head(
        "What “citable” looks like", "什么叫“可被引用”", "The pages AI can quote for a factory", "AI能为工厂引用的页面",
        "A practical checklist from our research on factory websites. ToucHigh writes and ships these pages; you supply the facts only your factory has.",
        "来自我们对工厂官网研究的实用清单。ToucHigh负责撰写并上线这些页面，您只需提供只有您的工厂才有的事实。") +
        '<div class="tw"><table><thead><tr>%s%s%s</tr></thead><tbody>%s</tbody></table></div>' % (
            t("th", "Page", "页面"), t("th", "What the buyer is asking", "买家在问什么"), t("th", "What to state", "要写清什么"),
            "".join("<tr>%s%s%s</tr>" % (t("td", r[0], r[1]), t("td", r[2], r[3]), t("td", r[4], r[5])) for r in [
                ("Capacity & equipment", "产能与设备", "Can you handle my volume?", "你们能接住我的量吗？", "Lines, main equipment, monthly capacity, real factory photos", "产线数量、主要设备、月产能、真实工厂照片"),
                ("Certifications & testing", "认证与检测", "Do you hold the certificates I need?", "你们有我需要的认证吗？", "Certificate names, numbers, issuing bodies and expiry dates", "证书名称、编号、发证机构和有效期"),
                ("Materials & process", "材料与工艺", "Why is your price different?", "为什么你们的价格不一样？", "Material grades and process differences, with data rather than adjectives", "材料等级和工艺差异，用数据而不是形容词"),
                ("MOQ, sampling & lead times", "起订量、打样与交期", "What's the minimum? How fast?", "最少订多少？多快交货？", "Ranges and the factors behind them", "给出范围以及影响因素"),
                ("FAQ", "常见问题", "Direct answers to specific questions", "具体问题的直接答案", "One question, one answer; the first sentence gives the conclusion", "一问一答，第一句就给结论"),
                ("Company entity data", "公司实体信息", "Is this supplier real and reliable?", "这家供应商真实可靠吗？", "English name, address, founding year and categories, identical everywhere", "英文名、地址、成立年份和主营品类，各平台完全一致"),
            ])), "padding-top:30px"))
    s.append(section("pro", "ToucHigh PRO", '<div class="pro-band"><div>' +
        t("div", "ToucHigh PRO · outbound & lead generation", "ToucHigh PRO · 外拓获客", 'class="eyebrow"') +
        t("h2", "Turn AI visibility into a pipeline.", "把AI曝光变成商机管道。") +
        t("p", "Being cited gets you on the shortlist. ToucHigh PRO, the managed outbound service, then runs email, cold calls, LinkedIn and business messengers on a strategy the engine computes first from your brand and competitor handles.",
          "被引用让您进入短名单。接下来，托管式外拓服务ToucHigh PRO会先由引擎根据您的品牌和竞品账号算出策略，再在邮件、冷呼叫、LinkedIn和商务即时通讯上执行。") +
        '<div class="hero-cta" style="margin-top:22px">' + pro_link("supplier_pro_band", "Explore ToucHigh PRO →", "了解ToucHigh PRO →", "btn btn-ghost") + "</div></div><div>" +
        checks([
            ("A standard cadence: 21 days, about 14 touches, 4 channels, 3 organisational levels", "标准节奏：21天、约14次触达、4个渠道、3个组织层级"),
            ("AI drafts 7,000+ strategy variants per setup; humans approve 100% of sends", "每次搭建由AI起草7,000+份策略变体；100%的发送经人工审核"),
            ("Humans take over any reply in under 5 minutes; a kill switch pauses everything in under 60 seconds", "任何回复5分钟内转人工接管；60秒内可一键暂停全部渠道"),
            ("PDPA, GDPR and CAN-SPAM compliance across all four channels", "四个渠道均遵循PDPA、GDPR和CAN-SPAM合规要求"),
        ]) + "</div></div>", "padding-top:30px"))
    s.append(section("reading", "Further reading", sec_head("From the blog", "延伸阅读", "Playbooks for factory GEO", "工厂GEO实操指南") + reads([
        ("/blog/factory-website-geo-chatgpt-supplier/", "/blog/en/factory-website-geo-chatgpt-supplier/", "Get ChatGPT to recommend your factory: a GEO primer", "让ChatGPT推荐你的工厂：工厂官网GEO入门", "Citable pages and first steps", "可被引用的页面清单与起步步骤"),
        ("/blog/chatgpt-supplier-shortlist-audit/", "/blog/en/chatgpt-supplier-shortlist-audit/", "Is your factory on ChatGPT's supplier shortlist? A 30-prompt audit", "ChatGPT的供应商短名单里有你吗？30个问题的自查法", "Measure before you fix", "先测量，再修复"),
        ("/blog/ai-crawlers-robots-txt-b2b-website/", "/blog/en/ai-crawlers-robots-txt-b2b-website/", "Is your website blocking ChatGPT? robots.txt for AI crawlers", "你的官网屏蔽了ChatGPT吗？AI爬虫的robots.txt设置", "Technical access comes first", "技术访问是第一步"),
    ]), "padding-top:30px"))
    s.append(section("faq", "FAQ", sec_head("Supplier visibility · FAQ", "供应商AI可见度 · 常见问题", "Questions we get asked", "大家的常见问题") + faq_html(SUP_FAQ), "padding-top:20px"))
    s.append("""<section class="final" aria-label="Get started">
  <div class="wrap">
    %s
    %s
    %s
    <div class="hero-cta" style="justify-content:center">%s %s</div>
  </div>
</section>
""" % (t("div", "Ready when you are", "准备好就开始吧", 'class="eyebrow" style="text-align:center"'),
       t("h2", "See whether AI puts your factory on the shortlist.", "看看AI会不会把您的工厂放进短名单。"),
       t("p", "Book a free 30-minute call. Bring your English website and a few core categories; we'll run a live AI-visibility read and show you which page to fix first.",
         "预约一次30分钟免费沟通。带上您的英文官网和几个核心品类，我们在线做一次AI可见度检测，告诉您先改哪一页。", 'class="lead"'),
       book("supplier_final", "Book your strategy call", "预约策略沟通", style="font-size:18px;padding:17px 34px"),
       pro_link("supplier_final", "ToucHigh PRO", "ToucHigh PRO", "btn btn-ghost on-dark")))
    return "".join(s)


SUPPLIER = dict(
    key="supplier", path="/supplier-ai-visibility/", ga_title="Supplier AI visibility",
    title_zh="供应商AI搜索可见度：让ChatGPT把您的工厂列进短名单 | ToucHigh",
    title_en="Supplier Visibility in ChatGPT & AI Search for Chinese Factories | ToucHigh",
    desc_zh="海外采购商开始用ChatGPT、Perplexity和Google AI找供应商。ToucHigh诊断工厂在AI答案中的曝光盲区，撰写并上线可被引用的页面，追踪AI引用份额，再由ToucHigh PRO把曝光变成商机。",
    desc_en="Buyers now ask ChatGPT, Perplexity and Google AI for supplier shortlists. ToucHigh audits where your factory is missing, ships citable pages and tracks your AI-citation share.",
    og_title_zh="让AI把您的工厂列进供应商短名单",
    keywords="供应商AI可见度, 工厂GEO, ChatGPT 推荐供应商, B2B GEO, AI搜索优化, 外贸独立站, supplier visibility ChatGPT, GEO for manufacturers, AI supplier search, B2B generative engine optimization",
    og="/assets/og/supplier-ai-visibility.jpg", crumb="Supplier visibility in AI search",
    service_name="ToucHigh supplier visibility in AI search",
    service_type="Generative Engine Optimization (GEO) for factories and B2B suppliers",
    area=["US", "CN"], audience="Chinese factories and B2B suppliers selling to overseas buyers",
    service_desc="ToucHigh's GEO Autopilot audits where a factory is invisible across ChatGPT, Perplexity, Google AI Overviews, Gemini and Copilot, writes and ships the fixes (pages, answers, entity data) and programmatic GEO articles, scores every concept for predicted clickability before publishing and tracks AI-citation share. ToucHigh PRO, the managed outbound service, can turn that visibility into qualified conversations.",
    offers={"@type": "Offer", "price": "500", "priceCurrency": "USD", "description": "GEO + Social bundle from under USD 500 / month"},
    nav=[("problem", "The problem", "问题"), ("how", "How it works", "运行机制"), ("faq", "FAQ", "常见问题")],
    foot_en="AI search visibility for Chinese factories and B2B suppliers selling overseas.",
    foot_zh="为出海的中国工厂与B2B供应商提升AI搜索可见度。",
    faq=SUP_FAQ, body=supplier_body,
)

# --------------------------------------------------------------------------------------------
# B. Amazon seller ads
# --------------------------------------------------------------------------------------------
AMZ_FAQ = [
    ("What does ToucHigh's Ads Autopilot do for Amazon sellers?",
     "ToucHigh的广告自动驾驶能为亚马逊卖家做什么？",
     "Ads Autopilot runs your ad spend across Amazon, Meta and Google, auto-adjusted to ROAS, and makes the creative-fatigue and budget calls for you. Creative concepts are scored for predicted performance before they go live.",
     "广告自动驾驶在Amazon、Meta和Google之间运行您的广告预算，以ROAS为目标自动调整，并替您处理素材疲劳和预算决策。创意概念在上线前都会做效果预测评分。"),
    ("Does it replace Amazon's own ad tools?",
     "它会取代亚马逊自己的广告工具吗？",
     "No. Amazon's tools, including its AI ad agent, optimise inside Amazon. ToucHigh works from one strategy across Amazon, Meta and Google, reads competitors' ads and organic content first, and scores creatives before spend. Bring your account setup to the call and we'll show how it fits.",
     "不会。亚马逊自己的工具（包括其AI广告智能体）是在亚马逊站内优化。ToucHigh基于同一套策略覆盖Amazon、Meta和Google，先分析竞争对手的广告和自然内容，并在花钱前给创意评分。沟通时带上您的账户情况，我们会说明它如何配合使用。"),
    ("Is a ROAS or ACoS result guaranteed?",
     "能保证ROAS或ACoS结果吗？",
     "No. Predicted-performance scores are a pre-launch corpus-pattern proxy, not a guarantee. The point is evidence before you spend: weak concepts are filtered out before budget goes behind them, and results are tracked so you can see the lift.",
     "不能。预测评分是基于语料规律的上线前参考，不是保证。它的意义在于花钱之前先有依据：表现弱的创意在投钱前就被筛掉，结果持续追踪，让您看清提升。"),
    ("Who is it built for?",
     "适合哪些卖家？",
     "Chinese cross-border sellers selling into the US who have the product and the price but no full-time US ads and content team. The same platform also covers GEO (getting your store cited in AI answers) and US social.",
     "面向进入美国市场、有产品有价格、但没有专职美国广告与内容团队的中国跨境卖家。同一平台还覆盖GEO（让店铺被AI答案引用）和美国社媒。"),
    ("How do I start?",
     "怎么开始？",
     "Book a 30-minute strategy call. Bring your store URL and one or two competitors; ToucHigh reads their ads and organic content and we walk you through a plan matched to your catalog.",
     "预约一次30分钟策略沟通。带上您的店铺网址和一两个竞争对手，ToucHigh会分析它们的广告和自然内容，我们再按您的产品线给出方案。"),
]


def amazon_body():
    s = []
    s.append("""<!-- HERO -->
<section class="hero" aria-label="Intro">
  <div class="wrap">
    <div class="hero-grid">
      <div>
        %s
        <h1>%s %s</h1>
        %s
        <div class="hero-cta">%s %s</div>
        <div class="trust">%s<span class="sep">·</span>%s<span class="sep">·</span>%s</div>
      </div>
      <div>%s</div>
    </div>
  </div>
</section>
""" % (t("div", "For Amazon sellers · Ads Autopilot", "专为亚马逊卖家 · 广告自动驾驶", 'class="eyebrow"'),
       t("span", "Amazon ads without a full-time ads team.", "没有专职广告团队，也能把亚马逊广告跑起来"),
       t("span", "Score first, then spend.", "先评分，再花钱", 'class="accent"'),
       t("p", "Amazon is moving ad buying to AI agents, and the platform's tools optimise inside Amazon. ToucHigh's Ads Autopilot runs your spend across Amazon, Meta and Google from one strategy, auto-adjusted to ROAS, with creative-fatigue and budget calls handled for you, and every concept scored before it goes live.",
         "亚马逊正把广告投放交给AI智能体，而平台工具只在亚马逊站内优化。ToucHigh的广告自动驾驶基于同一套策略，在Amazon、Meta和Google之间运行您的预算，以ROAS为目标自动调整，替您处理素材疲劳和预算决策，每个创意上线前都先评分。", 'class="lead"'),
       book("amazon_hero", "Book a 30-min strategy call", "预约30分钟策略沟通"),
       pro_link("amazon_hero", "See ToucHigh PRO", "了解ToucHigh PRO"),
       t("b", "Measured with the ToucHigh engine", "经ToucHigh引擎实测验证"),
       t("span", "Amazon · Meta · Google", "Amazon · Meta · Google"),
       t("span", "Recorded from the live product", "录制自真实产品"),
       video_frame("ads", "cloud.touchigh.ai/ads", "Recorded from the live product: spend across Amazon, Meta and Google, auto-adjusted to ROAS.",
                   "录制自真实产品：在Amazon、Meta和Google之间分配预算，以ROAS为目标自动调整。",
                   "ToucHigh Ads Autopilot adjusting spend across Amazon, Meta and Google, recorded from the live product.")))
    s.append("""<div class="band" aria-label="Channels">
  <div class="wrap band-in">
    %s
    <span class="chip"><span class="dot"></span>Amazon</span><span class="chip"><span class="dot"></span>Meta</span><span class="chip"><span class="dot"></span>Google</span>
    %s
  </div>
</div>
""" % (t("strong", "One strategy, three ad channels:", "一套策略，三个广告渠道："), t("span", "creatives scored before spend", "创意先评分再投放")))
    s.append(section("problem", "The problem", sec_head(
        "The problem", "问题在哪", "Handing ads to AI is easy. Knowing what to hand over is not.", "把广告交给AI不难，难的是知道该交什么。",
        "Amazon's AI ad agent and automatic targeting make it simple to launch. Without a strategy and guardrails, it is just as simple to spend past your margin.",
        "亚马逊的AI广告智能体和自动投放让开广告变得很简单；但没有策略和护栏，花超利润也同样简单。") +
        cards([
            ("01", "ACoS above margin is a loss", "ACoS高于利润率就是亏损", "Amazon's own guidance: to stay profitable, ACoS has to sit below your profit margin. Platform reports show attributed sales, not take-home profit.",
             "亚马逊官方说明：要保持盈利，ACoS必须低于利润率。平台报表显示的是归因销售额，不是到手利润。"),
            ("02", "One marketplace, one point of failure", "只靠一个平台，风险集中", "When all demand comes from Amazon ads, every cost increase lands on your margin. Meta, Google and AI search spread the risk.",
             "当所有需求都来自亚马逊广告时，每一次成本上涨都直接压在利润上。Meta、Google和AI搜索可以分散风险。"),
            ("03", "Creative fatigue goes unnoticed", "素材疲劳没人盯", "Without a full-time ads person, tired creatives and drifting budgets keep running until the numbers are already bad.",
             "没有专职广告人员时，疲劳的素材和跑偏的预算会一直跑下去，等发现时数据已经很难看。"),
        ])))
    s.append(section("how", "How ToucHigh helps", sec_head(
        "How ToucHigh helps", "ToucHigh怎么帮您", "Read the market, score the creative, run the spend.", "读懂市场，给创意打分，再跑预算。") +
        '<div class="steps">' + cards([
            ("01", "Read the market", "读懂市场", "Paste a URL. ToucHigh studies your rivals' ads and organic content and writes a US market-entry strategy.",
             "粘贴一个网址，ToucHigh研究竞争对手的广告和自然内容，输出一份进入美国市场的策略。"),
            ("02", "Score before spend", "花钱前先评分", "Every creative concept gets a predicted-performance score before it goes live, so budget goes behind the strongest ones.",
             "每个创意概念上线前都有效果预测评分，预算优先投给最强的创意。"),
            ("03", "Run spend to ROAS", "以ROAS为目标投放", "Spend across Amazon, Meta and Google, auto-adjusted, with creative-fatigue and budget calls made for you.",
             "在Amazon、Meta和Google之间自动调配预算，替您处理素材疲劳和预算决策。"),
            ("04", "Get found beyond ads", "广告之外也被找到", "GEO Autopilot gets your store cited in AI answers, and Social Autopilot runs native US-English social, so demand doesn't depend on ads alone.",
             "GEO自动执行让您的店铺被AI答案引用，社媒自动驾驶运营地道美式英语社媒，需求不再只靠广告。"),
        ], "grid g4") + "</div>", "padding-top:30px"))
    s.append(section("guardrails", "Guardrails", sec_head(
        "Guardrails", "护栏", "What to automate, what to keep", "哪些交给自动化，哪些自己把关",
        "A practical split from our research on AI ad agents for sellers. ACoS is ad spend divided by the sales those ads drove.",
        "来自我们对卖家使用AI广告智能体的研究的实用分工。ACoS即广告花费除以广告带来的销售额。") +
        '<div class="tw"><table><thead><tr>%s%s%s</tr></thead><tbody>%s</tbody></table></div>' % (
            t("th", "Task", "任务"), t("th", "Automate", "交给自动化"), t("th", "Keep control of", "自己把关"),
            "".join("<tr>%s%s%s</tr>" % (t("td", r[0], r[1]), t("td", r[2], r[3]), t("td", r[4], r[5])) for r in [
                ("Bids & daily adjustments", "出价与日常调整", "Continuous adjustment toward the goal", "朝目标持续调整", "Bid limits and your ACoS ceiling", "出价上限和ACoS上限"),
                ("Budget allocation", "预算分配", "Shifting spend between campaigns and channels", "在广告活动和渠道之间调配预算", "Total monthly budget and daily cap", "月度总预算和每日上限"),
                ("Creatives", "创意素材", "Variants, fatigue checks and pre-launch scoring", "变体生成、疲劳检测和上线前评分", "Brand claims and what you won't say", "品牌主张和不能说的话"),
                ("Campaign goal", "投放目标", "Planning the mix around the goal", "围绕目标规划投放组合", "Push sales, win new customers or clear stock", "冲销量、拉新客还是清库存"),
                ("Reporting", "报告", "Compiling data and explaining trends", "汇总数据、解释趋势", "Whether conclusions match real profit", "结论是否符合真实利润"),
            ])), "padding-top:30px"))
    s.append(section("pro", "ToucHigh PRO", '<div class="pro-band"><div>' +
        t("div", "Selling B2B or wholesale too?", "也做B2B或批发？", 'class="eyebrow"') +
        t("h2", "ToucHigh PRO builds the pipeline ads can't.", "ToucHigh PRO补上广告给不了的商机。") +
        t("p", "For distributor, retail-buyer or wholesale deals, ToucHigh PRO runs strategy-first outbound: AI agents plus human experts across email, cold calls, LinkedIn and business messengers.",
          "面向分销商、零售采购和批发客户，ToucHigh PRO提供策略先行的外拓：AI智能体+真人专家，覆盖邮件、冷呼叫、LinkedIn和商务即时通讯。") +
        '<div class="hero-cta" style="margin-top:22px">' + pro_link("amazon_pro_band", "Explore ToucHigh PRO →", "了解ToucHigh PRO →") + "</div></div><div>" +
        checks([
            ("Strategy computed first from your brand and competitor handles", "先根据您的品牌和竞品账号计算策略"),
            ("21-day cadence across 4 channels and 3 organisational levels", "21天节奏，覆盖4个渠道、3个组织层级"),
            ("Humans approve 100% of sends and make every call", "100%的发送由人工审核，每通电话都由真人拨打"),
            ("KPI baselines written into the contract", "KPI基准写进合同"),
        ]) + "</div></div>", "padding-top:30px"))
    s.append(section("reading", "Further reading", sec_head("From the blog", "延伸阅读", "Playbooks for Amazon ads", "亚马逊广告实操指南") + reads([
        ("/blog/amazon-ads-agent-sellers/", "/blog/en/amazon-ads-agent-sellers/", "Amazon's AI ad agent is here: what to hand over", "亚马逊AI广告智能体来了：该交出去什么", "A four-week controlled test", "四周对照测试"),
        ("/blog/amazon-break-even-acos-tacos/", "/blog/en/amazon-break-even-acos-tacos/", "Break-even ACoS, TACoS and ROAS explained", "盈亏平衡ACoS、TACoS和ROAS怎么算", "The math behind the guardrails", "护栏背后的算术"),
        ("/blog/amazon-search-term-report-negative-keywords/", "/blog/en/amazon-search-term-report-negative-keywords/", "Search term report: negatives and harvesting", "搜索词报告：否定词与关键词收割", "A weekly 30-minute routine", "每周30分钟的例行优化"),
    ]), "padding-top:30px"))
    s.append(section("faq", "FAQ", sec_head("Amazon ads · FAQ", "亚马逊广告 · 常见问题", "Questions we get asked", "大家的常见问题") + faq_html(AMZ_FAQ), "padding-top:20px"))
    s.append("""<section class="final" aria-label="Get started">
  <div class="wrap">
    %s
    %s
    %s
    <div class="hero-cta" style="justify-content:center">%s %s</div>
  </div>
</section>
""" % (t("div", "Ready when you are", "准备好就开始吧", 'class="eyebrow" style="text-align:center"'),
       t("h2", "Know what to hand to automation before you spend.", "花钱之前，先想清楚交给自动化的是什么。"),
       t("p", "Book a free 30-minute call. Bring your store URL and one competitor; ToucHigh reads their ads and organic content and we walk you through a plan.",
         "预约一次30分钟免费沟通。带上您的店铺网址和一个竞争对手，ToucHigh会分析它们的广告和自然内容，我们再和您一起过一遍方案。", 'class="lead"'),
       book("amazon_final", "Book your strategy call", "预约策略沟通", style="font-size:18px;padding:17px 34px"),
       pro_link("amazon_final", "ToucHigh PRO", "ToucHigh PRO", "btn btn-ghost on-dark")))
    return "".join(s)


AMAZON = dict(
    key="amazon", path="/amazon-ads-autopilot/", ga_title="Amazon ads autopilot",
    title_zh="亚马逊广告自动驾驶：没有广告团队也能先评分再投放 | ToucHigh",
    title_en="Amazon Ads Autopilot for Sellers: Score First, Then Spend | ToucHigh",
    desc_zh="亚马逊正把广告投放交给AI智能体。ToucHigh广告自动驾驶基于同一套策略在Amazon、Meta和Google运行预算，以ROAS为目标自动调整，处理素材疲劳和预算决策，每个创意上线前先评分。",
    desc_en="Amazon is moving ad buying to AI agents. ToucHigh's Ads Autopilot runs spend across Amazon, Meta and Google to ROAS, and scores every creative before it goes live.",
    og_title_zh="亚马逊广告：先评分，再花钱",
    keywords="亚马逊广告, Amazon Ads Agent, 亚马逊广告代运营替代, ACoS, ROAS, 跨境卖家广告, Amazon ads autopilot, Amazon PPC for sellers, AI ad agent Amazon, ROAS optimization",
    og="/assets/og/amazon-ads-autopilot.jpg", crumb="Amazon ads autopilot",
    service_name="ToucHigh Ads Autopilot for Amazon sellers", service_type="Advertising automation across Amazon, Meta and Google",
    area=["US"], audience="Chinese cross-border sellers on Amazon selling into the US",
    service_desc="ToucHigh's Ads Autopilot runs ad spend across Amazon, Meta and Google from one strategy, auto-adjusted to ROAS, with creative-fatigue and budget calls handled for the seller. Creative concepts are scored for predicted performance before they go live; predicted scores are a pre-launch proxy, not a guarantee.",
    offers=None,
    nav=[("problem", "The problem", "问题"), ("how", "How it works", "运行机制"), ("faq", "FAQ", "常见问题")],
    foot_en="Ads, AI search visibility and social on autopilot for cross-border sellers entering the US.",
    foot_zh="为进入美国市场的跨境卖家提供广告、AI搜索曝光和社媒自动化。",
    faq=AMZ_FAQ, body=amazon_body,
)

if __name__ == "__main__":
    for P in (SUPPLIER, AMAZON):
        build(P)
