"""Share links: every item, song and download has a Share button that copies its share page's link, the header copies
the shop's and Randis UDS's links, and every share page has the preview tags Discord reads, with a picture that's really there.
    python tests/share_test.py"""
import os, re, time

import harness

PUBLIC = "https://randywilliammoore.github.io/randis-shop/"
UDS_REPO = "https://github.com/RandyWilliamMoore/randis-uds"
SHOP = harness.SHOP


def meta(text, prop):
    m = re.search(r'<meta (?:property|name)="' + re.escape(prop) + r'" content="([^"]*)"', text)
    return m.group(1) if m else None


def page_ok(check, label, path, want_url):
    if not os.path.isfile(path):
        return check(f"{label}: has a share page", False, path)
    text = open(path, encoding="utf-8").read()
    image = meta(text, "og:image") or ""
    local = os.path.join(SHOP, *image[len(PUBLIC):].split("/")) if image.startswith(PUBLIC) else ""
    check(f"{label}: share page has a title, description, its own address and a picture that's in the shop",
          bool(meta(text, "og:title")) and bool(meta(text, "og:description")) and meta(text, "og:url") == want_url
          and meta(text, "twitter:card") == "summary_large_image" and os.path.isfile(local), (image, meta(text, "og:url")))


def test(page, check):
    base = harness.serve()
    # the shop's own front door is the share page for the shop
    page_ok(check, "The shop", os.path.join(SHOP, "index.html"), PUBLIC)
    things = [(i["kind"], i["slug"], i["name"]) for i in harness.items()]
    page.go(base + "index.html#/")
    page.until("!!document.querySelector('.nav')")
    page.js("window.__copied = []; navigator.clipboard.writeText = t => { __copied.push(t); return Promise.resolve(); };")
    links = page.json("[...document.querySelectorAll('.nav [data-act=share]')].map(b => b.dataset.link)") or []
    check("the header has Share the shop and Share Randis UDS", links == [PUBLIC, UDS_REPO], links)
    page.js("document.querySelectorAll('.nav [data-act=share]').forEach(b => b.click())"); time.sleep(0.3)
    check("clicking them copies those links", page.json("__copied") == [PUBLIC, UDS_REPO], page.json("__copied"))
    check("the button says the link was copied", page.js("document.querySelector('.nav [data-act=share]').textContent") == "Link copied")
    soft = page.json("(window.SOFTWARE || []).map(s => s.slug)") or []
    songs = page.json("(window.MUSIC || []).map(s => [s.slug, s.name])") or []
    things += [("software", s, s) for s in soft] + [("music", s, n) for s, n in songs]
    for kind, slug, name in things:
        want = f"{PUBLIC}share/{kind}/{slug}/"
        page_ok(check, name, os.path.join(SHOP, "share", kind, slug, "index.html"), want)
        page.go(base + f"index.html#/{kind}/{slug}")
        sel = f"#song-{slug} [data-act=share]" if kind == "music" else ".item-top [data-act=share]"
        if not page.until(f"!!document.querySelector('{sel}')", 5):
            check(f"{name}: has a Share button", False)
            continue
        page.js(f"window.__copied = []; navigator.clipboard.writeText = t => {{ __copied.push(t); return Promise.resolve(); }}; document.querySelector('{sel}').click();")
        time.sleep(0.2)
        check(f"{name}: Share copies its share link", page.json("__copied") == [want], page.json("__copied"))


harness.run(test)
