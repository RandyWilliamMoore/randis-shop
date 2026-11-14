"""Writes the share pages: one small page per shop item, song and download, plus the picture Discord (and other chat apps) show for it.

The shop is one page that draws itself with JavaScript, and Discord doesn't run JavaScript, so a link to #/games/blockwild
shows no picture. A share link points at share/<kind>/<slug>/ instead: a plain page with the item's name, blurb and
picture in its preview tags, which sends a person on to the item in the shop.

  share/<kind>/<slug>/index.html     the page (rewritten every run)
  site/share/<kind>-<slug>.png       its 1200x630 picture card (made with Microsoft Edge, only when it's missing or the logo changed)
  site/share/shop.png                the shop's own card, for the front door link

Run it after build_index.py (build_index.py runs it for you). --cards-again remakes every picture.
"""
import glob, hashlib, html, json, os, re, shutil, subprocess, sys, tempfile, time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PUBLIC = "https://randywilliammoore.github.io/randis-shop/"
CARDS = os.path.join(ROOT, "site", "share")
PAGES = os.path.join(ROOT, "share")
STAMPS = os.path.join(CARDS, "stamps.json")   # which logo each card was made from, so a changed logo gets a new card
EDGE = [r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe", r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"]
NOUN = {"games": "A game", "apps": "An app", "music": "A royalty-free song", "software": "A download"}


def load_list(name, var):
    text = open(os.path.join(ROOT, name), encoding="utf-8").read()
    return json.loads(text[text.index("["):text.rindex("]") + 1]) if var in text else []


def everything():
    """(kind, slug, name, blurb, picture made from, picture is already a card) for every thing on the shop."""
    out = []
    for i in load_list("items.js", "ITEMS"):
        out.append((i["kind"], i["slug"], i["name"], i["blurb"], i["logo"], False))
    for s in load_list("software.js", "SOFTWARE"):
        out.append(("software", s["slug"], s["name"], s["blurb"], s["logo"], False))
    for t in load_list("music.js", "MUSIC"):
        out.append(("music", t["slug"], t["name"], t["blurb"], f"music/{t['slug']}/cover.jpg", True))
    return out


CARD = """<!doctype html><html><head><meta charset="utf-8"><style>
html,body{{margin:0;width:1200px;height:630px;overflow:hidden}}
body{{background:#0f7f7f;background-image:linear-gradient(45deg,#0b6a6a 25%,transparent 25%,transparent 75%,#0b6a6a 75%),linear-gradient(45deg,#0b6a6a 25%,transparent 25%,transparent 75%,#0b6a6a 75%);
background-size:16px 16px;background-position:0 0,8px 8px;font-family:"Trebuchet MS",Tahoma,Verdana,sans-serif}}
.win{{position:absolute;left:40px;top:36px;width:1120px;height:558px;background:#c6c6c6;border:4px solid;border-color:#fff #2c2c2c #2c2c2c #fff;box-shadow:8px 8px 0 rgba(0,0,0,.35)}}
.bar{{height:56px;line-height:56px;padding:0 20px;color:#fff;font-weight:700;font-size:30px;background:linear-gradient(90deg,#000080,#1084d0);white-space:nowrap;overflow:hidden}}
.in{{display:flex;gap:44px;align-items:center;padding:34px 40px}}
.logo{{width:400px;height:400px;flex:none;background:#fff;border:4px solid;border-color:#2c2c2c #fff #fff #2c2c2c;display:flex;align-items:center;justify-content:center}}
.logo img{{max-width:380px;max-height:380px;width:380px;height:380px;object-fit:contain}}
h1{{margin:0 0 18px;font-size:{size}px;line-height:1.1;color:#101010}}
p{{margin:0 0 26px;font-size:26px;line-height:1.35;color:#2c2c2c;max-height:144px;overflow:hidden}}
b{{display:inline-block;padding:12px 26px;font-size:28px;background:#ffd23f;border:4px solid;border-color:#fff #2c2c2c #2c2c2c #fff}}
</style></head><body><div class="win"><div class="bar">The Randis Shop</div><div class="in">
<div class="logo"><img src="{logo}"></div><div><h1>{name}</h1><p>{blurb}</p><b>{action}</b></div></div></div></body></html>"""

ACTION = {"games": "Play free in your browser", "apps": "Use free in your browser", "music": "Listen free, royalty free", "software": "Free download"}


def short(text, most):
    return text if len(text) <= most else text[:most].rsplit(" ", 1)[0] + "..."


def edge():
    for p in EDGE:
        if os.path.isfile(p):
            return p
    return None


def make_card(path, logo_file, name, blurb, action):
    browser = edge()
    if not browser:
        sys.exit("build_share: Microsoft Edge wasn't found, so the picture cards can't be made")
    work = tempfile.mkdtemp(prefix="shop_card_")
    try:
        page = os.path.join(work, "card.html")
        size = 64 if len(name) <= 18 else 52 if len(name) <= 30 else 42
        with open(page, "w", encoding="utf-8") as f:
            f.write(CARD.format(logo="file:///" + logo_file.replace("\\", "/"), name=html.escape(name), blurb=html.escape(short(blurb, 150)),
                                action=html.escape(action), size=size))
        shot = os.path.join(work, "card.png")
        subprocess.run([browser, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--allow-file-access-from-files",
                        f"--user-data-dir={os.path.join(work, 'profile')}", "--window-size=1200,630", "--force-device-scale-factor=1",
                        "--virtual-time-budget=3000", f"--screenshot={shot}", "file:///" + page.replace("\\", "/")],
                       check=True, capture_output=True, timeout=90)
        # Edge hands the job to a background copy of itself and returns at once; wait for the picture to land
        last, until = -1, time.time() + 60
        while time.time() < until:
            size = os.path.getsize(shot) if os.path.isfile(shot) else -1
            if size > 0 and size == last:
                break
            last = size
            time.sleep(0.5)
        time.sleep(0.5)
        if not os.path.isfile(shot) or os.path.getsize(shot) < 2000:
            sys.exit(f"build_share: Edge didn't make the card for {name}")
        shutil.move(shot, path)
    finally:
        shutil.rmtree(work, ignore_errors=True)


PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; img-src 'self'; base-uri 'none'; form-action 'none'">
<title>{title}</title>
<meta name="description" content="{desc}">
<meta property="og:site_name" content="The Randis Shop">
<meta property="og:type" content="website">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{image}">
{dims}<meta property="og:image:alt" content="{alt}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:image" content="{image}">
<meta name="theme-color" content="#ffd23f">
<meta http-equiv="refresh" content="0; url={go}">
<link rel="canonical" href="{url}">
</head>
<body>
<p><a href="{go}">{title}</a></p>
</body>
</html>
"""


CARD_SIZE = """<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
"""


def write_page(kind, slug, name, blurb, image):
    url = f"{PUBLIC}share/{kind}/{slug}/"
    folder = os.path.join(PAGES, kind, slug)
    os.makedirs(folder, exist_ok=True)
    with open(os.path.join(folder, "index.html"), "w", encoding="utf-8", newline="\n") as f:
        f.write(PAGE.format(title=html.escape(f"{name} | The Randis Shop"), desc=html.escape(f"{NOUN[kind]} on the Randis Shop. {blurb}"),
                            url=url, image=PUBLIC + image, alt=html.escape(f"{name} on the Randis Shop"),
                            go=f"../../../index.html#/{kind}/{slug}",
                            dims="" if kind == "music" else CARD_SIZE))
    return url


def main():
    again = "--cards-again" in sys.argv
    os.makedirs(CARDS, exist_ok=True)
    stamps = json.load(open(STAMPS, encoding="utf-8")) if os.path.isfile(STAMPS) else {}
    things = everything()
    keep_pages, keep_cards, made = set(), {"stamps.json"}, 0
    shop = ("shop", "", "The Randis Shop", "Games, apps and royalty-free music made with Randis UDS. Play right here, nothing to install.", "site/icon.svg", False)
    for kind, slug, name, blurb, pic, is_card in [shop] + things:
        if is_card:
            image = pic
        else:
            card_name = "shop.png" if kind == "shop" else f"{kind}-{slug}.png"
            card = os.path.join(CARDS, card_name)
            logo_file = os.path.join(ROOT, *pic.split("/"))
            if not os.path.isfile(logo_file):      # a scratch copy of the shop (the tests make one) has no pictures
                print(f"build_share: no picture at {pic}, so no share card for {name}")
                continue
            stamp = hashlib.sha1(open(logo_file, "rb").read() + f"{name}|{blurb}".encode("utf-8")).hexdigest()
            if again or not os.path.isfile(card) or stamps.get(card_name) != stamp:
                make_card(card, logo_file, name, blurb, "Play, use and listen free" if kind == "shop" else ACTION[kind])
                stamps[card_name] = stamp
                made += 1
            keep_cards.add(card_name)
            image = f"site/share/{card_name}"
        if kind != "shop":
            write_page(kind, slug, name, blurb, image)
            keep_pages.add(f"{kind}/{slug}")
    # an item that left the shop takes its share page and card with it
    for page in glob.glob(os.path.join(PAGES, "*", "*")):
        rel = os.path.relpath(page, PAGES).replace("\\", "/")
        if rel not in keep_pages:
            shutil.rmtree(page)
    for card in os.listdir(CARDS):
        if card not in keep_cards:
            os.remove(os.path.join(CARDS, card))
            stamps.pop(card, None)
    with open(STAMPS, "w", encoding="utf-8", newline="\n") as f:
        json.dump({k: stamps[k] for k in sorted(stamps) if k in keep_cards}, f, indent=1)
        f.write("\n")
    print(f"build_share: {len(keep_pages)} share pages, {made} new picture cards")


if __name__ == "__main__":
    main()
