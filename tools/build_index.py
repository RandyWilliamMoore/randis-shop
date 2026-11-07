"""Reads every item folder and writes items.js, the list the shop's page shows. Stops on anything that doesn't belong.

  games/<slug>/  or  apps/<slug>/
      item.html    the game or app, one page
      logo.svg     its thumbnail (or logo.png)
      video.png    its video thumbnail, wide (optional)
      info.json    name, by, blurb, status, real_items, reviews

  software/<slug>/   a program to download and install, shown first on the Software Shelf (written to software.js); its logo is site/logos/<slug>.png,
                     and a screenshot of it, if there is one, site/screens/<slug>.png
      info.json    name, by, version, blurb, download (its release page), source, new (what changed), fine (how to install)

  music/<slug>/      a royalty-free song made with Randis Sound Forge, in the Jukebox (written to music.js); add one with tools/add_music.py
      song.mp3, song.ogg or song.wav   the song
      info.json    name, by, blurb, genre, length (like "3:05"), added (like "2026-11-07")
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


SOFT_FIELDS = {"name", "by", "version", "blurb", "download", "source", "new", "fine"}
SOFT_ALLOWED = {"info.json"}


def read_software(slug):
    """software/<slug>/: a program you download and install (Randis UDS itself), not a page that plays in the shop.
    It goes in software.js, not items.js: Randis UDS's own Shop tab reads items.js and opens every entry there as a tab."""
    where = f"software/{slug}"
    if not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", slug):
        problem(where, "folder name must be lowercase words with dashes")
    names = set(os.listdir(os.path.join(ROOT, "software", slug)))
    if names - SOFT_ALLOWED:
        problem(where, f"files that don't belong: {sorted(names - SOFT_ALLOWED)}")
    # its logo sits in site/logos/ (the repo's picture check allows pictures only in the item folders and site/)
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


SONG_FILES = {"song.mp3", "song.ogg", "song.wav"}
SONG_FIELDS = {"name", "by", "blurb", "genre", "length", "added"}
SONG_MAX = 95 * 1024 * 1024     # GitHub refuses files over 100 MB


def read_song(slug):
    where = f"music/{slug}"
    if not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", slug):
        problem(where, "folder name must be lowercase words with dashes")
    folder = os.path.join(ROOT, "music", slug)
    names = set(os.listdir(folder))
    if names - SONG_FILES - {"info.json"}:
        problem(where, f"files that don't belong: {sorted(names - SONG_FILES - {'info.json'})}")
    songs = names & SONG_FILES
    if "info.json" not in names or len(songs) != 1:
        problem(where, "needs info.json and one song file: song.mp3, song.ogg or song.wav")
    song = songs.pop()
    if os.path.getsize(os.path.join(folder, song)) > SONG_MAX:
        problem(where, "the song file is over 95 MB")
    with open(os.path.join(folder, "info.json"), encoding="utf-8") as f:
        info = json.load(f)
    if set(info) != SONG_FIELDS:
        problem(where, "info.json has the wrong fields")
    for field, most in {"name": 60, "by": 40, "genre": 40}.items():
        if not isinstance(info[field], str) or not info[field].strip() or len(info[field]) > most:
            problem(where, f"{field} must be text of at most {most} characters")
    if not isinstance(info["blurb"], str) or len(info["blurb"]) > 400:
        problem(where, "blurb must be text of at most 400 characters (it can be empty)")
    if info["length"] is not None and not (isinstance(info["length"], str) and re.fullmatch(r"\d{1,3}:\d\d", info["length"])):
        problem(where, "length must look like 3:05, or be null")
    if not (isinstance(info["added"], str) and re.fullmatch(r"\d{4}-\d\d-\d\d", info["added"])):
        problem(where, "added must look like 2026-11-07")
    plain = re.sub(r"[^\w .()-]+", "", info["name"]).strip() or slug
    return {"kind": "music", "slug": slug, **info, "file": f"music/{slug}/{song}", "download": plain + os.path.splitext(song)[1]}


def write_list(name, var, entries):
    text = json.dumps(entries, ensure_ascii=True, indent=1).replace("<", "\\u003c")
    with open(os.path.join(ROOT, name), "w", encoding="utf-8", newline="\n") as f:
        f.write("// Written by tools/build_index.py. Change the item folders, not this file.\nwindow." + var + " = " + text + ";\n")
    print(f"{name}: {len(entries)} item(s)")


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
    music.sort(key=lambda t: t["added"], reverse=True)     # newest first; sort is stable, so same-day songs stay by name
    write_list("items.js", "ITEMS", items)
    write_list("software.js", "SOFTWARE", software)
    write_list("music.js", "MUSIC", music)


if __name__ == "__main__":
    main()
