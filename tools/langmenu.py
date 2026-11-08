"""Language menu + hreflang cluster helpers (stdlib only)."""
import re
from site_config import L, ORDER, SITE

GLOBE = ('<svg viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="1.8">'
         '<circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3c2.5 2.6 3.8 5.6 3.8 9s-1.3 6.4-3.8 9c-2.5-2.6-3.8-5.6-3.8-9S9.5 5.6 12 3z"/></svg>')
LABEL = {"zh-Hans": "语言", "en": "Language", "zh-Hant": "語言", "ja": "言語", "ko": "언어", "th": "ภาษา",
         "vi": "Ngôn ngữ", "id": "Bahasa", "ms": "Bahasa", "hi": "भाषा", "fil": "Wika", "es": "Idioma",
         "fr": "Langue", "de": "Sprache", "pt": "Idioma", "ar": "اللغة", "ru": "Язык"}
START, END = "<!--lmenu-->", "<!--/lmenu-->"
HSTART, HEND = "<!--hreflang-->", "<!--/hreflang-->"
ASSETS = ('<link rel="stylesheet" href="/assets/css/lang-menu.css">', '<script src="/assets/js/lang-menu.js" defer></script>')


def menu_html(cur, versions, setlang=False):
    """versions: {hl: path}. Languages without a version are left out of the list."""
    items = []
    for hl in ORDER:
        if hl not in versions:
            continue
        d = L[hl]
        attrs = ' hreflang="%s" lang="%s" data-short="%s"' % (hl, hl, d["short"])
        if d["dir"] == "rtl":
            attrs += ' dir="rtl"'
        if setlang and hl in ("zh-Hans", "en"):
            attrs += ' data-setlang="%s"' % ("zh" if hl == "zh-Hans" else "en")
        if hl == cur:
            attrs += ' aria-current="page"'
        items.append('<li><a href="%s"%s>%s</a></li>' % (versions[hl], attrs, d["name"]))
    lab = LABEL[cur]
    return ('%s<div class="lmenu" data-lmenu><button type="button" class="lm-btn" aria-haspopup="true" aria-expanded="false" '
            'aria-label="%s: %s">%s<span class="lm-txt">%s</span><span class="lm-car" aria-hidden="true">▾</span></button>'
            '<ul class="lm-list" role="list" aria-label="%s" hidden>%s</ul></div>%s') % (
        START, lab, L[cur]["name"], GLOBE, L[cur]["short"], lab, "".join(items), END)


def hreflang_html(versions):
    out = [HSTART]
    for hl in ORDER:
        if hl in versions:
            out.append('<link rel="alternate" hreflang="%s" href="%s%s">' % (hl, SITE, versions[hl]))
    xd = versions.get("zh-Hans") or versions.get("en") or list(versions.values())[0]
    out.append('<link rel="alternate" hreflang="x-default" href="%s%s">' % (SITE, xd))
    out.append(HEND)
    return "\n".join(out)


_LANG_DIV = re.compile(r'<div class="lang" role="group"[^>]*>.*?</div>', re.S)
_MENU = re.compile(re.escape(START) + r'.*?' + re.escape(END), re.S)
_HL_BLOCK = re.compile(re.escape(HSTART) + r'.*?' + re.escape(HEND), re.S)
_HL_LINE = re.compile(r'[ \t]*<link rel="alternate" hreflang="[^"]*" href="[^"]*">\n?')


def apply(html, cur, versions, setlang=False):
    """Insert/refresh the language menu, the hreflang cluster and the shared assets."""
    m = menu_html(cur, versions, setlang)
    if _MENU.search(html):
        html = _MENU.sub(lambda _: m, html, count=1)
    else:
        html, n = _LANG_DIV.subn(lambda _: m, html, count=1)
        if not n:
            raise ValueError("no language switch found")
    h = hreflang_html(versions)
    if _HL_BLOCK.search(html):
        html = _HL_BLOCK.sub(lambda _: h, html, count=1)
    else:
        first = _HL_LINE.search(html)
        if not first:
            raise ValueError("no hreflang found")
        pos = first.start()
        html = _HL_LINE.sub("", html)
        html = html[:pos] + h + "\n" + html[pos:]
    for a in ASSETS:
        if a not in html:
            html = html.replace("</head>", a + "\n</head>", 1)
    return html
