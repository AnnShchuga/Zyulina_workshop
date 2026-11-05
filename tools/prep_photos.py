"""Готовит обработанные фото для сайта: дополняет фон до нужных пропорций
цветом края снимка (без обрезки работы), уменьшает и сжимает в JPEG.
Запуск: python3 tools/prep_photos.py <папка с исходниками> <карта.json>
карта: {"имя-на-сайте": ["файл.jpg", "1:1"], ...}"""
import json, sys
from pathlib import Path
from PIL import Image, ImageStat

OUT = Path(__file__).resolve().parent.parent / "assets" / "img"

def edge_color(im):
    w, h = im.size; b = max(4, min(w, h) // 60)
    strips = [im.crop((0, 0, w, b)), im.crop((0, h - b, w, h)), im.crop((0, 0, b, h)), im.crop((w - b, 0, w, h))]
    px = []
    for s in strips: px += list(s.resize((40, 4)).get_flattened_data())
    return tuple(sorted(c[i] for c in px)[len(px) // 2] for i in range(3))

def pad(im, ratio):
    a, b = map(int, ratio.split(":")); w, h = im.size
    if w / h < a / b: nw, nh = round(h * a / b), h
    else: nw, nh = w, round(w * b / a)
    if (nw, nh) == (w, h): return im
    # продолжаем край снимка (каждая строка/столбец своим цветом), затем размываем только добавленные поля
    import numpy as np
    from PIL import ImageFilter
    a_ = np.asarray(im); l = (nw - w) // 2; t_ = (nh - h) // 2
    big = np.pad(a_, ((t_, nh - h - t_), (l, nw - w - l), (0, 0)), mode="edge")
    c = Image.fromarray(big).filter(ImageFilter.GaussianBlur(max(nw, nh) // 60))
    c.paste(im.crop((3, 3, w - 3, h - 3)), (l + 3, t_ + 3)); return c

src, m = Path(sys.argv[1]), json.load(open(sys.argv[2]))
for name, (f, ratio) in m.items():
    im = Image.open(src / f).convert("RGB")
    im = pad(im, ratio) if ratio != "orig" else im
    im.thumbnail((1200, 1200), Image.LANCZOS)
    out = OUT / f"{name}.jpg"; im.save(out, quality=82, optimize=True, progressive=True)
    print(f"{name}.jpg {im.size} {out.stat().st_size//1024} KB  <- {f}")
