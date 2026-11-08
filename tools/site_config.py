"""Shared language + URL configuration for touchigh.ai (stdlib only).

URL scheme
  home        zh-Hans "/"            en "/?lang=en"            other "/<code>/"
  PRO         zh-Hans "/pro/"        en "/pro/?lang=en"        other "/<code>/pro/"
  landing X   zh-Hans "/X/"          en "/X/?lang=en"          other "/<code>/X/"
  blog hub    zh-Hans "/blog/"       en "/blog/en/"            other "/blog/<code>/"
  article     existing URLs kept (/blog/<slug>/, /blog/zh/<slug>/, /blog/en/<slug>/);
              new language versions at /blog/<code>/<slug>/
x-default is always the Simplified Chinese URL.
"""
SITE = "https://touchigh.ai"

# (hreflang, url code, native name, short label, og:locale, dir)
LANGS = [
    ("zh-Hans", "zh",      "简体中文",          "中文",   "zh_CN", "ltr"),
    ("en",      "en",      "English",           "EN",     "en_US", "ltr"),
    ("zh-Hant", "zh-hant", "繁體中文",          "繁中",   "zh_TW", "ltr"),
    ("ja",      "ja",      "日本語",            "日本語", "ja_JP", "ltr"),
    ("ko",      "ko",      "한국어",            "한국어", "ko_KR", "ltr"),
    ("th",      "th",      "ไทย",               "ไทย",    "th_TH", "ltr"),
    ("vi",      "vi",      "Tiếng Việt",        "VI",     "vi_VN", "ltr"),
    ("id",      "id",      "Bahasa Indonesia",  "ID",     "id_ID", "ltr"),
    ("ms",      "ms",      "Bahasa Melayu",     "MS",     "ms_MY", "ltr"),
    ("hi",      "hi",      "हिन्दी",              "हिन्दी",  "hi_IN", "ltr"),
    ("fil",     "fil",     "Filipino",          "FIL",    "tl_PH", "ltr"),
    ("es",      "es",      "Español",           "ES",     "es_ES", "ltr"),
    ("fr",      "fr",      "Français",          "FR",     "fr_FR", "ltr"),
    ("de",      "de",      "Deutsch",           "DE",     "de_DE", "ltr"),
    ("pt",      "pt",      "Português",         "PT",     "pt_BR", "ltr"),
    ("ar",      "ar",      "العربية",           "عربي",   "ar_AR", "rtl"),
    ("ru",      "ru",      "Русский",           "RU",     "ru_RU", "ltr"),
]
L = {l[0]: dict(hl=l[0], code=l[1], name=l[2], short=l[3], locale=l[4], dir=l[5]) for l in LANGS}
ORDER = [l[0] for l in LANGS]
NEW_LANGS = ORDER[2:]          # languages rendered as separate static pages
CODE2HL = {v["code"]: k for k, v in L.items()}

# Bilingual (client-side zh/en) pages and their path
STATIC_PAGES = {
    "home": "/",
    "pro": "/pro/",
    "supplier": "/supplier-ai-visibility/",
    "amazon": "/amazon-ads-autopilot/",
}


def page_url(page, hl):
    """Path for a static page (home/pro/landing) or blog hub in language hl."""
    if page == "hub":
        if hl == "zh-Hans":
            return "/blog/"
        return "/blog/%s/" % L[hl]["code"]
    base = STATIC_PAGES[page]
    if hl == "zh-Hans":
        return base
    if hl == "en":
        return base + "?lang=en"
    return "/" + L[hl]["code"] + base


def file_for(path):
    """Repo file that serves a path ('/x/?lang=en' -> 'x/index.html')."""
    p = path.split("?")[0].split("#")[0].strip("/")
    return (p + "/index.html") if p else "index.html"
