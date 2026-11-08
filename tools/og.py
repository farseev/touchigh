#!/usr/bin/env python3
"""1200x630 Open Graph cards in the blog's existing style (text left, artwork right).

Needs Pillow (tooling only; the site and the page generator stay stdlib-only).
Fonts: Inter (Latin/Cyrillic/Vietnamese), Noto Sans CJK (zh/ja/ko). Thai, Devanagari and Arabic use
Noto Sans Thai / Devanagari / Arabic from FONT_DIR (env TOUCHIGH_FONTS, default /tmp/fonts).
"""
import os
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONT_DIR = os.environ.get("TOUCHIGH_FONTS", "/tmp/fonts")
INTER = "/usr/share/fonts/opentype/inter/Inter-%s.otf"
CJK = "/usr/share/fonts/opentype/noto/NotoSansCJK-%s.ttc"
CJK_INDEX = {"zh-Hans": 2, "zh-Hant": 3, "ja": 0, "ko": 1}   # SC, TC, JP, KR inside the .ttc
EXTRA = {"th": "NotoSansThai", "hi": "NotoSansDevanagari", "ar": "NotoSansArabic"}
ORANGE, INK, GREY = (255, 100, 45), (25, 27, 35), (108, 110, 121)


def font(lang, weight, size):
    if lang in CJK_INDEX:
        w = {"ExtraBold": "Black", "Bold": "Bold", "SemiBold": "Bold", "Medium": "Medium"}[weight]
        return ImageFont.truetype(CJK % w, size, index=CJK_INDEX[lang])
    if lang in EXTRA:
        w = {"ExtraBold": "Bold", "Bold": "Bold", "SemiBold": "SemiBold", "Medium": "Medium"}[weight]
        p = os.path.join(FONT_DIR, "%s-%s.ttf" % (EXTRA[lang], w))
        if not os.path.exists(p):
            p = os.path.join(FONT_DIR, "%s-Bold.ttf" % EXTRA[lang])
        return ImageFont.truetype(p, size, layout_engine=ImageFont.Layout.RAQM)
    return ImageFont.truetype(INTER % weight, size)


NO_START = set("，。：；、！？）」』”’,.:;!?)%")


def wrap(draw, text, f, width, cjk):
    import re as _re
    if cjk:
        words = _re.findall(r"[A-Za-z0-9\-\+\.&'/]+|\s|.", text)
    else:
        words = text.split(" ")
    lines, cur = [], ""
    for w in words:
        if cjk and w == " " and not cur:
            continue
        trial = (cur + w) if cjk else (cur + " " + w).strip()
        if draw.textlength(trial, font=f) <= width or not cur or (cjk and w in NO_START):
            cur = trial
        else:
            lines.append(cur.rstrip())
            cur = w.lstrip()
    if cur:
        lines.append(cur)
    return lines


def card(out, title, eyebrow, art, lang="en", footer="touchigh.ai/blog"):
    W, H = 1200, 630
    im = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(im)
    rtl = lang == "ar"
    cjk = lang in CJK_INDEX or lang == "th"
    # artwork, rounded, right side (left side for RTL)
    src = Image.open(art).convert("RGB")
    bw, bh = 520, 550
    r = max(bw / src.width, bh / src.height)
    src = src.resize((int(src.width * r) + 1, int(src.height * r) + 1), Image.LANCZOS)
    l, t = (src.width - bw) // 2, (src.height - bh) // 2
    src = src.crop((l, t, l + bw, t + bh))
    mask = Image.new("L", (bw, bh), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, bw, bh), 24, fill=255)
    ax = 40 if rtl else 640
    im.paste(src, (ax, 40), mask)
    x0 = 680 if rtl else 60
    tw = 480
    # logo
    spark = Image.open(os.path.join(ROOT, "touchigh_spark.png")).convert("RGBA").resize((40, 40), Image.LANCZOS)
    logo_f = ImageFont.truetype(INTER % "ExtraBold", 30)
    if rtl:
        lw = d.textlength("ToucHigh", font=logo_f)
        im.paste(spark, (x0 + tw - 40, 56), spark)
        d.text((x0 + tw - 52 - lw, 58), "ToucHigh", font=logo_f, fill=INK)
    else:
        im.paste(spark, (x0, 56), spark)
        d.text((x0 + 52, 58), "ToucHigh", font=logo_f, fill=INK)
    ef = font(lang, "SemiBold", 17)
    eb = eyebrow if (cjk or rtl or lang in EXTRA) else eyebrow.upper()
    ex = x0 + tw - d.textlength(eb, font=ef) if rtl else x0
    d.text((ex, 150), eb, font=ef, fill=ORANGE)
    size = 44
    while True:
        tf = font(lang, "ExtraBold", size)
        lines = wrap(d, title, tf, tw, cjk)
        lh = int(size * (1.32 if (cjk or lang in EXTRA) else 1.18))
        if (len(lines) <= 5 and len(lines) * lh <= 330) or size <= 28:
            break
        size -= 2
    y = 190
    for ln in lines[:6]:
        lx = x0 + tw - d.textlength(ln, font=tf) if rtl else x0
        d.text((lx, y), ln, font=tf, fill=INK)
        y += lh
    ff = ImageFont.truetype(INTER % "Medium", 19)
    if rtl:
        fw = d.textlength(footer, font=ff)
        d.ellipse((x0 + tw - 10, 567, x0 + tw, 577), fill=ORANGE)
        d.text((x0 + tw - 20 - fw, 559), footer, font=ff, fill=GREY)
    else:
        d.ellipse((x0, 567, x0 + 10, 577), fill=ORANGE)
        d.text((x0 + 20, 559), footer, font=ff, fill=GREY)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    im.save(out, "JPEG", quality=86, optimize=True, progressive=True)


def articles(force=False, only_langs=None):
    """OG cards for every article language file under i18n/articles/."""
    import json
    import sys
    sys.path.insert(0, os.path.dirname(__file__))
    from site_config import L
    from articles import parse, ART
    n = 0
    for slug in sorted(os.listdir(ART)):
        meta = json.load(open(os.path.join(ART, slug, "meta.json"), encoding="utf-8"))
        for f in sorted(os.listdir(os.path.join(ART, slug))):
            if not f.endswith(".txt"):
                continue
            hl = f[:-4]
            if only_langs and hl not in only_langs:
                continue
            if hl in meta.get("og_by_lang", {}):   # imported article: keeps the card it already had
                continue
            out = os.path.join(ROOT, "assets/blog/og/%s%s.jpg" % (meta["num"], "" if hl == "zh-Hans" else "-" + L[hl]["code"]))
            if os.path.exists(out) and not force:
                continue
            d = parse(os.path.join(ART, slug, f))
            try:
                card(out, d["title"], d["section"], os.path.join(ROOT, "assets/blog/hero/%s.jpg" % meta["hero"]), hl)
            except OSError as e:   # font for this script not installed: the page falls back to the English card
                print("og: skipped", slug, hl, "-", e)
                if os.path.exists(out):
                    os.remove(out)
                continue
            n += 1
    return n


if __name__ == "__main__":
    import sys as _s
    if len(_s.argv) > 1 and _s.argv[1] == "articles":
        print(articles("--force" in _s.argv, [a for a in _s.argv[2:] if not a.startswith("--")] or None), "article cards")
        raise SystemExit
    card(os.path.join(ROOT, "assets/og/supplier-ai-visibility.jpg"), "让AI把您的工厂列进供应商短名单",
         "中国工厂 · B2B供应商 · GEO", os.path.join(ROOT, "assets/blog/hero/t52.jpg"), "zh-Hans", "touchigh.ai")
    card(os.path.join(ROOT, "assets/og/supplier-ai-visibility-en.jpg"), "Buyers ask AI for a supplier shortlist. Make sure your factory is on it.",
         "Supplier visibility · GEO", os.path.join(ROOT, "assets/blog/hero/t52.jpg"), "en", "touchigh.ai")
    card(os.path.join(ROOT, "assets/og/amazon-ads-autopilot.jpg"), "亚马逊广告：先评分，再花钱",
         "亚马逊卖家 · 广告自动驾驶", os.path.join(ROOT, "media/ads.jpg"), "zh-Hans", "touchigh.ai")
    card(os.path.join(ROOT, "assets/og/amazon-ads-autopilot-en.jpg"), "Amazon ads without a full-time ads team: score first, then spend",
         "Amazon sellers · Ads Autopilot", os.path.join(ROOT, "media/ads.jpg"), "en", "touchigh.ai")
    print("ok")
