"""Добавить пост ВКонтакте в блог сайта.

Примеры:
  python3 tools/add_vk_post.py "https://vk.com/wall598297974_272" --title "Детский сад готовится к празднику" --text "..." --kind "Декор"
  python3 tools/add_vk_post.py '<код экспорта из ВК, где есть VK.Widgets.Post(...)>'

По ссылке пост добавится карточкой со ссылкой. Из кода экспорта берётся ещё и hash,
тогда на сайте вместо карточки покажется сам пост ВК с фото.
Если пост уже есть в списке, команда обновит его (например, допишет hash).
После добавления: python3 build.py && python3 verify.py
"""
import argparse
import json
import re
import sys
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "src" / "vk-posts.json"


def parse(src):
    m = re.search(r"VK\.Widgets\.Post\(\s*['\"][^'\"]*['\"]\s*,\s*(-?\d+)\s*,\s*(\d+)\s*,\s*['\"]([^'\"]+)['\"]", src)
    if m:
        return int(m.group(1)), int(m.group(2)), m.group(3)
    m = re.search(r"wall(-?\d+)_(\d+)", src)
    if m:
        return int(m.group(1)), int(m.group(2)), ""
    sys.exit("Не нашёл в тексте ни ссылку вида vk.com/wall123_45, ни код VK.Widgets.Post(...)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("source", help="ссылка на пост или код экспорта")
    ap.add_argument("--title", default="")
    ap.add_argument("--text", default="")
    ap.add_argument("--kind", default="")
    ap.add_argument("--hide", action="store_true", help="добавить, но не показывать на сайте")
    a = ap.parse_args()

    owner, pid, hsh = parse(a.source)
    data = json.loads(DATA.read_text(encoding="utf-8"))
    post = next((p for p in data["posts"] if p["owner"] == owner and p["id"] == pid), None)
    if post is None:
        if not a.title:
            sys.exit("Новый пост: укажите --title (заголовок карточки)")
        post = {"owner": owner, "id": pid, "hash": "", "show": True, "kind": a.kind or "Пост",
                "title": a.title, "text": a.text}
        data["posts"].insert(0, post)
        action = "добавлен"
    else:
        action = "обновлён"
    if hsh:
        post["hash"] = hsh
    for k in ("title", "text", "kind"):
        if getattr(a, k):
            post[k] = getattr(a, k)
    if a.hide:
        post["show"] = False
    DATA.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Пост wall{owner}_{pid} {action}; виджет ВК: {'да' if post['hash'] else 'нет, будет карточка со ссылкой'}")


if __name__ == "__main__":
    main()
