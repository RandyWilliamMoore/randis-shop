"""Copies site/band.js into every game or app page that carries its own copy of the Raisin Band
(<script id="raisin-band">), so they stay the same as the Jukebox's. Run it after changing site/band.js.
    python tools/sync_band.py"""
import os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TAG = re.compile(r'(<script id="raisin-band">\r?\n)(.*?)(</script>)', re.S)


def main():
    band = open(os.path.join(ROOT, "site", "band.js"), encoding="utf-8").read().replace("\r\n", "\n")
    if "</script" in band:
        sys.exit("sync_band: band.js can't contain </script")
    for kind in ("games", "apps"):
        for slug in sorted(os.listdir(os.path.join(ROOT, kind))):
            p = os.path.join(ROOT, kind, slug, "item.html")
            page = open(p, encoding="utf-8", newline="").read()
            if not TAG.search(page):
                continue
            nl = "\r\n" if "\r\n" in page else "\n"
            new = TAG.sub(lambda m: m.group(1) + band.replace("\n", nl) + m.group(3), page, count=1)
            if new != page:
                open(p, "w", encoding="utf-8", newline="").write(new)
                print(f"updated {kind}/{slug}")
            else:
                print(f"same    {kind}/{slug}")


if __name__ == "__main__":
    main()
