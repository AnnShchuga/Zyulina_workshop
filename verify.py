"""Проверка сборки перед публикацией.  Запуск: python3 verify.py [--shots]

1. Каждый блок для Тильды не больше лимита T123.
2. Все стили изолированы: селекторы начинаются с .zm (чтобы не ломать стили Тильды).
3. Внутренние ссылки ведут на существующие страницы и якоря, картинки на месте.
4. В браузере (Chrome): нет ошибок JS, нет горизонтальной прокрутки на 1440 и 375 px,
   меню-бургер и фильтр каталога работают.  --shots сохраняет скриншоты в shots/.
"""
import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CFG = json.loads((ROOT / "site.config.json").read_text(encoding="utf-8"))
fails, notes = [], []


def check(ok, msg):
    (notes if ok else fails).append(("OK  " if ok else "FAIL") + "  " + msg)


# 1. размеры
blocks = sorted((ROOT / "tilda").glob("*/*.html"))
over = [b for b in blocks if b.stat().st_size > CFG["tilda_block_limit_bytes"]]
check(not over, f"блоки T123: {len(blocks)} шт., max {max(b.stat().st_size for b in blocks)} B, лимит {CFG['tilda_block_limit_bytes']} B")

# 2. изоляция стилей
bad = []
for b in blocks:
    for css in re.findall(r"<style>(.*?)</style>", b.read_text(encoding="utf-8"), re.S):
        css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
        css = re.sub(r"@media[^{]*\{", "", css)
        for sel in re.findall(r"([^{}]+)\{", css):
            for s in sel.split(","):
                s = s.strip()
                if s and not (s.startswith(".zm") or s.startswith("@font-face") or s in ("body", ".t-records") or s.startswith("from") or s.startswith("to")):
                    bad.append(f"{b.parent.name}/{b.name}: {s}")
check(not bad, "все CSS-селекторы с префиксом .zm" + ("" if not bad else ": " + "; ".join(bad[:5])))


# 3. ссылки, якоря, картинки
class P(HTMLParser):
    def __init__(self):
        super().__init__(); self.links, self.srcs, self.ids = [], [], set()
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if "id" in a: self.ids.add(a["id"])
        if tag == "a" and "href" in a: self.links.append(a["href"])
        if tag == "img" and "src" in a: self.srcs.append(a["src"])

docs = {p.name: p for p in (ROOT / "docs").glob("*.html")}
parsed = {}
for n, p in docs.items():
    pr = P(); pr.feed(p.read_text(encoding="utf-8")); parsed[n] = pr
broken = []
for n, pr in parsed.items():
    for h in pr.links:
        if h.startswith(("http", "mailto:", "tel:")):
            continue
        path, _, frag = h.partition("#")
        path = path.split("?")[0] or n
        if path not in docs:
            broken.append(f"{n} → {h}")
        elif frag and frag not in parsed[path].ids and frag not in ("online", "offline", "rec", "pdf"):
            broken.append(f"{n} → {h} (нет якоря)")
    for s in pr.srcs:
        if not (ROOT / "docs" / s).exists():
            broken.append(f"{n}: картинка {s}")
check(not broken, f"ссылки и картинки на {len(docs)} страницах" + ("" if not broken else ": " + "; ".join(broken[:8])))

todo = sum(p.read_text(encoding="utf-8").count("zm-todo") for p in docs.values())
notes.append(f"INFO  мест с пометкой «заменить» (zm-todo): {todo}")

# 4. браузер
from playwright.sync_api import sync_playwright
shots = "--shots" in sys.argv
(ROOT / "shots").mkdir(exist_ok=True)
with sync_playwright() as pw:
    br = pw.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--no-sandbox"])
    for w, h, tag in ((1440, 900, "desktop"), (375, 812, "mobile")):
        ctx = br.new_context(viewport={"width": w, "height": h})
        pg = ctx.new_page()
        errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)))
        for n in sorted(docs):
            pg.goto((ROOT / "docs" / n).as_uri())
            pg.evaluate("document.querySelectorAll('img[loading=lazy]').forEach(i=>i.loading='eager')")
            pg.wait_for_timeout(300)
            sw = pg.evaluate("document.documentElement.scrollWidth")
            check(sw <= w, f"{tag} {n}: нет горизонтальной прокрутки ({sw} ≤ {w})")
            if shots:
                pg.screenshot(path=str(ROOT / "shots" / f"{tag}-{n.replace('.html','')}.png"), full_page=True)
        check(not errs, f"{tag}: ошибок JS нет" + ("" if not errs else ": " + "; ".join(errs[:3])))
        if tag == "mobile":
            pg.goto((ROOT / "docs" / "index.html").as_uri())
            pg.click(".zm-hd__burger")
            check(pg.is_visible(".zm-hd__nav"), "mobile: бургер открывает меню")
        else:
            pg.goto((ROOT / "docs" / "workshops.html").as_uri() + "#pdf")
            vis = pg.evaluate("[...document.querySelectorAll('.zm-cat__card')].filter(c=>!c.hidden).length")
            check(vis == 2, f"каталог: фильтр по якорю #pdf показывает {vis} карточки (ожидаем 2)")
            pg.goto((ROOT / "docs" / "contacts.html").as_uri() + "?mk=origami")
            check("Оригами" in pg.inner_text(".zm-ct__topic"), "контакты: подставляется выбранный мастер-класс")
        ctx.close()
    br.close()

print("\n".join(notes + fails))
print(f"\nИТОГ: {len(notes) - 1} проверок пройдено, {len(fails)} провалено")
sys.exit(1 if fails else 0)
