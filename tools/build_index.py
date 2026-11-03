"""Reads every item folder and writes items.js, the list the shop's page shows. Stops on anything that doesn't belong.

  games/<slug>/  or  apps/<slug>/
      item.html    the game or app, one page
      logo.svg     its thumbnail (or logo.png)
      video.png    its video thumbnail, wide (optional)
      info.json    name, by, blurb, status, real_items, reviews
"""
import json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KINDS = ("games", "apps")
ALLOWED = {"item.html", "logo.svg", "logo.png", "info.json", "video.png"}
TEXT_MAX = {"name": 60, "by": 40, "blurb": 400}


def problem(where, what):
    sys.exit(f"build_index: {where}: {what}")


def web_or_none(where, field, value):
    if value is not None and not (isinstance(value, str) and re.fullmatch(r"https://[^\s\"'<>]+", value)):
        problem(where, f"{field} must be an https link or null")


def read_item(kind, slug):
    where = f"{kind}/{slug}"
    if not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", slug):
        problem(where, "folder name must be lowercase words with dashes")
    folder = os.path.join(ROOT, kind, slug)
    names = set(os.listdir(folder))
    extra = names - ALLOWED
    if extra:
        problem(where, f"files that don't belong: {sorted(extra)}")
    logos = names & {"logo.svg", "logo.png"}
    if "item.html" not in names or "info.json" not in names or len(logos) != 1:
        problem(where, "needs item.html, info.json and one logo")
    with open(os.path.join(folder, "info.json"), encoding="utf-8") as f:
        info = json.load(f)
    if set(info) != {"name", "by", "blurb", "status", "real_items", "reviews"}:
        problem(where, "info.json has the wrong fields")
    for field, most in TEXT_MAX.items():
        if not isinstance(info[field], str) or not info[field].strip() or len(info[field]) > most:
            problem(where, f"{field} must be text of at most {most} characters")
    if info["status"] not in ("ok", "flagged"):
        problem(where, "status must be ok or flagged")
    if set(info["reviews"]) != {"randy", "maker"}:
        problem(where, "reviews needs randy and maker")
    web_or_none(where, "real_items", info["real_items"])
    web_or_none(where, "reviews.randy", info["reviews"]["randy"])
    web_or_none(where, "reviews.maker", info["reviews"]["maker"])
    # every item opens in Randis UDS by this link; the folder-name rule above matches the one the app accepts
    return {"kind": kind, "slug": slug, **info, "open_with": f"randisuds://open?item={kind}/{slug}", "file": f"{kind}/{slug}/item.html", "logo": f"{kind}/{slug}/{logos.pop()}", "video_pic": f"{kind}/{slug}/video.png" if "video.png" in names else None}


def main():
    items = []
    for kind in KINDS:
        top = os.path.join(ROOT, kind)
        for slug in sorted(os.listdir(top)) if os.path.isdir(top) else []:
            items.append(read_item(kind, slug))
    text = json.dumps(items, ensure_ascii=True, indent=1).replace("<", "\\u003c")
    with open(os.path.join(ROOT, "items.js"), "w", encoding="utf-8", newline="\n") as f:
        f.write("// Written by tools/build_index.py. Change the item folders, not this file.\nwindow.ITEMS = " + text + ";\n")
    print(f"items.js: {len(items)} item(s)")


if __name__ == "__main__":
    main()
