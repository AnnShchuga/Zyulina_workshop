"""Сборка сайта в двух вариантах.

  docs/   — превью для GitHub Pages: целые страницы, относительные ссылки и картинки.
  tilda/  — по папке на страницу, внутри пронумерованные фрагменты для блоков T123
            («Другое» → T123 «HTML-код»). Вставлять строго по порядку номеров.

Запуск: python3 build.py
"""
import json
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
CFG = json.loads((ROOT / "site.config.json").read_text(encoding="utf-8"))
PAGES = json.loads((SRC / "pages.json").read_text(encoding="utf-8"))

TILDA_LIMIT = CFG["tilda_block_limit_bytes"]


def link(name, mode):
    if mode == "docs":
        return "index.html" if name == "index" else f"{name}.html"
    return "/" if name == "index" else f"/{name}"


def render(text, mode, params=None):
    assets = "assets" if mode == "docs" else CFG["tilda_asset_base"].rstrip("/")
    text = text.replace("{{A}}", assets)
    text = re.sub(r"\{\{L:([a-z-]+)\}\}", lambda m: link(m.group(1), mode), text)
    for k, v in (params or {}).items():
        text = text.replace("{{" + k + "}}", v)
    left = re.findall(r"\{\{[^}]+\}\}", text)
    if left:
        raise SystemExit(f"Не подставлены метки: {sorted(set(left))}")
    return text


def base_for(mode):
    css = (SRC / "base.html").read_text(encoding="utf-8")
    if mode == "tilda":
        # на живом сайте пунктир «заменить» не показываем, фон кладём на всю страницу Тильды
        css = css.replace(".zm-todo{outline:2px dashed var(--zm-red);outline-offset:4px}", ".zm-todo{}")
        css = css.replace("</style>", "body,.t-records{background:#F8F5F0 url('{{A}}/decor/seigaiha-bg.svg') repeat;background-size:120px 60px}\n</style>")
    return render(css, mode)


def sections(page):
    for item in page["sections"]:
        if isinstance(item, list):
            yield item[0], item[1]
        else:
            yield item, {}


def build():
    for d in ("docs", "tilda"):
        shutil.rmtree(ROOT / d, ignore_errors=True)
    (ROOT / "docs").mkdir()
    shutil.copytree(ROOT / "assets", ROOT / "docs" / "assets")
    (ROOT / "docs" / ".nojekyll").write_text("")

    report = []
    for name, page in PAGES["pages"].items():
        parts_docs = []
        tdir = ROOT / "tilda" / name
        tdir.mkdir(parents=True)
        tb = base_for("tilda")
        (tdir / "00-base.html").write_text(tb, encoding="utf-8")
        report.append((f"{name}/00-base.html", len(tb.encode())))
        for i, (sec, params) in enumerate(sections(page), start=1):
            raw = (SRC / "sections" / f"{sec}.html").read_text(encoding="utf-8")
            parts_docs.append(render(raw, "docs", params))
            t = render(raw, "tilda", params)
            fn = f"{i:02d}-{sec}.html"
            (tdir / fn).write_text(t, encoding="utf-8")
            report.append((f"{name}/{fn}", len(t.encode())))

        html = f"""<!doctype html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{page['title']}</title>
<meta name="description" content="{page['description']}">
<link rel="icon" href="assets/decor/logo.svg" type="image/svg+xml">
</head>
<body data-zm-page="{name}" style="margin:0">
<div class="zm zm-page">
{base_for('docs')}
{''.join(parts_docs)}
</div>
</body>
</html>
"""
        (ROOT / "docs" / link(name, "docs")).write_text(html, encoding="utf-8")

    (ROOT / "tilda" / "SIZES.txt").write_text(
        "\n".join(f"{b:>7} B  {'OK ' if b <= TILDA_LIMIT else 'ВЕЛИК'}  {f}" for f, b in report) + "\n",
        encoding="utf-8")
    big = [f for f, b in report if b > TILDA_LIMIT]
    print(f"Страниц: {len(PAGES['pages'])}, блоков для Тильды: {len(report)}, самый большой: {max(b for _, b in report)} B")
    if big:
        raise SystemExit(f"Блоки больше лимита {TILDA_LIMIT} B: {big}")


if __name__ == "__main__":
    build()
