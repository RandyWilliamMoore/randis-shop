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
    if set(info) - {"version"} != {"name", "by", "blurb", "status", "real_items", "reviews"}:
        problem(where, "info.json has the wrong fields")
    if "version" in info and not (type(info["version"]) is int and 1 <= info["version"] <= 9999):
        problem(where, "version must be a whole number from 1 up")
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
    return {"kind": kind, "slug": slug, **info, "open_with": f"randisuds://open?item={kind}/{slug}", "file": f"{kind}/{slug}/item.html", "logo": f"{kind}/{slug}/{logos.pop()}", "video_pic": f"{kind}/{slug}/video.png" if "video.png" in names else None}


SOFT_FIELDS = {"name", "by", "version", "blurb", "download", "source", "new", "fine"}
SOFT_ALLOWED = {"info.json"}


def read_software(slug):
    where = f"software/{slug}"
    if not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", slug):
        problem(where, "folder name must be lowercase words with dashes")
    names = set(os.listdir(os.path.join(ROOT, "software", slug)))
    if names - SOFT_ALLOWED:
        problem(where, f"files that don't belong: {sorted(names - SOFT_ALLOWED)}")
    logos = [n for n in (f"{slug}.png", f"{slug}.svg") if os.path.isfile(os.path.join(ROOT, "site", "logos", n))]
    if "info.json" not in names or len(logos) != 1:
        problem(where, f"needs info.json, and one logo at site/logos/{slug}.png or .svg")
    with open(os.path.join(ROOT, "software", slug, "info.json"), encoding="utf-8") as f:
        info = json.load(f)
    if set(info) != SOFT_FIELDS:
        problem(where, "info.json has the wrong fields")
    for field, most in {"name": 60, "by": 40, "blurb": 400, "fine": 400}.items():
        if not isinstance(info[field], str) or not info[field].strip() or len(info[field]) > most:
            problem(where, f"{field} must be text of at most {most} characters")
    if not isinstance(info["version"], str) or not re.fullmatch(r"\d+\.\d+\.\d+", info["version"]):
        problem(where, "version must look like 1.2.3")
    for field in ("download", "source"):
        if not (isinstance(info[field], str) and re.fullmatch(r"https://github\.com/[^\s\"'<>]+", info[field])):
            problem(where, f"{field} must be a github.com https link")
    if not info["download"].endswith("/v" + info["version"]):
        problem(where, "download must be the release page for this version")
    if not isinstance(info["new"], list) or not 1 <= len(info["new"]) <= 8 or not all(isinstance(t, str) and t.strip() and len(t) <= 300 for t in info["new"]):
        problem(where, "new must be 1 to 8 lines of at most 300 characters")
    shot = f"site/screens/{slug}.png"
    return {"kind": "software", "slug": slug, **info, "logo": f"site/logos/{logos[0]}",
            "screenshot": shot if os.path.isfile(os.path.join(ROOT, *shot.split("/"))) else None}


SONG_FILES = {"song.mp3", "cover.jpg", "info.json"}
SONG_FIELDS = {"name", "by", "blurb", "genre", "length", "added"}
SONG_MAX = 95 * 1024 * 1024


def read_song(slug):
    where = f"music/{slug}"
    if not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", slug):
        problem(where, "folder name must be lowercase words with dashes")
    folder = os.path.join(ROOT, "music", slug)
    names = set(os.listdir(folder))
    if names - SONG_FILES:
        problem(where, f"files that don't belong: {sorted(names - SONG_FILES)}")
    if names != SONG_FILES:
        problem(where, "needs song.mp3, cover.jpg and info.json (tools/add_music.py makes all three)")
    song = "song.mp3"
    if os.path.getsize(os.path.join(folder, song)) > SONG_MAX:
        problem(where, "the song file is over 95 MB")
    with open(os.path.join(folder, "info.json"), encoding="utf-8") as f:
        info = json.load(f)
    if set(info) != SONG_FIELDS:
        problem(where, "info.json has the wrong fields")
    for field, most in {"name": 60, "by": 40, "genre": 40, "blurb": 400}.items():
        if not isinstance(info[field], str) or not info[field].strip() or len(info[field]) > most:
            problem(where, f"{field} must be text of at most {most} characters")
    if info["length"] is not None and not (isinstance(info["length"], str) and re.fullmatch(r"\d{1,3}:\d\d", info["length"])):
        problem(where, "length must look like 3:05, or be null")
    if not (isinstance(info["added"], str) and re.fullmatch(r"\d{4}-\d\d-\d\d", info["added"])):
        problem(where, "added must look like 2026-11-07")
    plain = re.sub(r"[^\w .()-]+", "", info["name"]).strip() or slug
    return {"kind": "music", "slug": slug, **info, "file": f"music/{slug}/{song}", "cover": f"music/{slug}/cover.jpg", "download": plain + os.path.splitext(song)[1]}


def write_list(name, var, entries):
    text = json.dumps(entries, ensure_ascii=True, indent=1).replace("<", "\\u003c")
    with open(os.path.join(ROOT, name), "w", encoding="utf-8", newline="\n") as f:
        f.write("window." + var + " = " + text + ";\n")
    print(f"{name}: {len(entries)} item(s)")


NOSCRIPT = re.compile(r"<noscript>.*?</noscript>", re.S)


def write_noscript(items, software, music):
    import html
    e = lambda s: html.escape(s, quote=True)
    rows = [f'<li><a href="{e(s["download"])}">Download {e(s["name"])} {e(s["version"])}</a>: {e(s["blurb"])}</li>' for s in software]
    rows += [f'<li><a href="share/{e(i["kind"])}/{e(i["slug"])}/">{e(i["name"])}</a>: {e(i["blurb"])}</li>' for i in items]
    rows += [f'<li><a href="share/music/{e(m["slug"])}/">{e(m["name"])}</a> ({e(m["genre"])}): {e(m["blurb"])}</li>' for m in music]
    block = ("<noscript><div class=\"noscript\"><p>The Randis Shop needs JavaScript to play. Here is everything on its shelves:</p>\n<ul>\n"
             + "\n".join(rows) + "\n</ul>\n<p><a href=\"https://www.etsy.com/shop/UberRandis\">Real in-game items on Etsy</a> · "
             "<a href=\"https://ko-fi.com/moorescombinatoricsmatrix\">Support on Ko-fi</a></p></div></noscript>")
    path = os.path.join(ROOT, "index.html")
    with open(path, encoding="utf-8") as f:
        page = f.read()
    if len(NOSCRIPT.findall(page)) != 1:
        problem("index.html", "needs exactly one <noscript> block")
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(NOSCRIPT.sub(lambda _: block, page))
    print(f"index.html: noscript list of {len(rows)} item(s)")


def main():
    items = []
    for kind in KINDS:
        top = os.path.join(ROOT, kind)
        for slug in sorted(os.listdir(top)) if os.path.isdir(top) else []:
            items.append(read_item(kind, slug))
    top = os.path.join(ROOT, "software")
    software = [read_software(slug) for slug in (sorted(os.listdir(top)) if os.path.isdir(top) else [])]
    top = os.path.join(ROOT, "music")
    music = [read_song(slug) for slug in (sorted(os.listdir(top)) if os.path.isdir(top) else [])]
    music.sort(key=lambda t: t["added"], reverse=True)
    write_list("items.js", "ITEMS", items)
    write_list("software.js", "SOFTWARE", software)
    write_list("music.js", "MUSIC", music)
    write_noscript(items, software, music)
    import build_share
    build_share.main()


if __name__ == "__main__":
    main()
