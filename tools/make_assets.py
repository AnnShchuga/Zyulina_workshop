"""Генерирует декор и временные картинки-заглушки в assets/.
Заглушки нужны только до прихода реальных фото: каждая подписана, чтобы не перепутать.
Запуск: python3 tools/make_assets.py
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DECOR = ROOT / "assets" / "decor"
IMG = ROOT / "assets" / "img"
DECOR.mkdir(parents=True, exist_ok=True)
IMG.mkdir(parents=True, exist_ok=True)

INK, RED = "#435A67", "#E8523F"


def seigaiha(stroke, fill, w=120, h=60, sw=2.2):
    """Японский узор «волны»: ряды вложенных полуокружностей."""
    def scale(cx, cy):
        out = [f'<circle cx="{cx}" cy="{cy}" r="{w/2}" fill="{fill}"/>']
        for r in (w / 2, w / 2 * 0.75, w / 2 * 0.5, w / 2 * 0.25):
            out.append(f'<circle cx="{cx}" cy="{cy}" r="{r - sw/2:.2f}" fill="none" stroke="{stroke}" stroke-width="{sw}"/>')
        return "".join(out)
    parts = []
    # порядок отрисовки важен: нижние ряды поверх верхних
    for cy, xs in ((0, (0, w)), (h / 2, (w / 2,)), (h, (0, w))):
        for cx in xs:
            parts.append(scale(cx, cy))
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">{"".join(parts)}</svg>'


(DECOR / "seigaiha-bg.svg").write_text(seigaiha("#EFEAE2", "#F8F5F0", sw=2.6), encoding="utf-8")
(DECOR / "seigaiha-dark.svg").write_text(seigaiha("#1E1E1E", "#FFFFFF", w=56, h=28, sw=2.4), encoding="utf-8")

logo = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200" role="img" aria-label="Творческая мастерская Людмилы Зюлиной">
<defs><path id="c" d="M100,100 m-72,0 a72,72 0 1,1 144,0 a72,72 0 1,1 -144,0"/></defs>
<text font-family="Yanone Kaffeesatz, Arial Narrow, sans-serif" font-weight="700" font-size="24" fill="{INK}">
<textPath href="#c" startOffset="0" textLength="430" lengthAdjust="spacingAndGlyphs">ТВОРЧЕСКАЯ МАСТЕРСКАЯ ЛЮДМИЛЫ ЗЮЛИНОЙ</textPath></text>
<path d="M150 46 l6 16 17 1 -13 10 5 17 -15 -9 -14 9 4 -17 -13 -10 17 -1z" fill="{RED}"/>
<circle cx="100" cy="100" r="34" fill="none" stroke="#1E1E1E" stroke-width="1.6"/>
<circle cx="124" cy="112" r="24" fill="none" stroke="#1E1E1E" stroke-width="1.6"/>
</svg>'''
(DECOR / "logo.svg").write_text(logo, encoding="utf-8")

PLACEHOLDERS = {
    "hero": ("#F6C9A3", "Фото мастерской: кисти, краски, рабочий стол", 1600, 700),
    "portrait": ("#E8523F", "Портрет Людмилы", 600, 600),
    "mk-decoupage": ("#F6C9A3", "Декупаж ложек: обложка видео", 800, 500),
    "mk-cardmaking": ("#F2A7A2", "Кардмейкинг: обложка видео", 800, 500),
    "mk-dandelion": ("#3AA0B8", "«Одуванчик»: обложка видео", 800, 500),
    "work-newyear": ("#F6C9A3", "Новогодний венок", 800, 640),
    "work-cards": ("#F2A7A2", "Открытки", 800, 640),
    "work-wedding": ("#C9B6E8", "Свадебный декор", 800, 640),
    "work-dolls": ("#3AA0B8", "Куклы", 800, 640),
    "blog-1": ("#4A4A4A", "Фото с урока памяти", 800, 600),
    "blog-2": ("#4A4A4A", "Фото встречи со школьниками", 800, 600),
    "blog-3": ("#4A4A4A", "Фото программы о Гаршине", 800, 600),
}
for name, (bg, label, w, h) in PLACEHOLDERS.items():
    fg = "#FFFFFF" if bg in ("#4A4A4A", "#3AA0B8", "#E8523F") else INK
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">
<rect width="{w}" height="{h}" fill="{bg}"/>
<circle cx="{w*0.82:.0f}" cy="{h*0.22:.0f}" r="{min(w,h)*0.14:.0f}" fill="#FFFFFF" opacity=".25"/>
<path d="M{w*0.15:.0f} {h*0.85:.0f} L{w*0.38:.0f} {h*0.5:.0f} L{w*0.55:.0f} {h*0.7:.0f} L{w*0.7:.0f} {h*0.56:.0f} L{w*0.88:.0f} {h*0.85:.0f}Z" fill="#FFFFFF" opacity=".28"/>
<text x="50%" y="46%" text-anchor="middle" font-family="PT Sans, Arial, sans-serif" font-size="{max(22, w//28)}" font-weight="700" fill="{fg}">ЗАГЛУШКА</text>
<text x="50%" y="56%" text-anchor="middle" font-family="PT Sans, Arial, sans-serif" font-size="{max(18, w//40)}" fill="{fg}">{label}</text>
</svg>'''
    (IMG / f"{name}.svg").write_text(svg, encoding="utf-8")

print(f"decor: {len(list(DECOR.iterdir()))} файлов, img: {len(list(IMG.iterdir()))} файлов")
