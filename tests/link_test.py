"""Outside links in games: the player hands them to the shop page, which asks first, and only "Open it" opens one,
in a new tab cut off from the shop. First with a test game in the real shop page and real player; then every item's own
outside links, through the real player script.
    python tests/link_test.py"""
import time

import harness

PROBE_PAGE = """<!doctype html><html><head><meta charset="utf-8"></head><body>
<a id="go" href="https://example.com/some/page?x=1" target="_blank">outside</a>
<a id="local" href="#here">same page</a>
<script>
addEventListener('message', e => { if (!e.data || !e.data.do) return;
  if (e.data.do == 'click') document.getElementById('go').click();
  if (e.data.do == 'local') document.getElementById('local').click();
  if (e.data.do == 'open') window.open('https://example.org/w');
  if (e.data.do == 'bad') { parent.postMessage({uds: 'open-link', url: 'javascript:alert(1)'}, '*'); parent.postMessage({uds: 'open-link', url: 'file:///C:/Windows/win.ini'}, '*'); }
  parent.postMessage({done: e.data.do, where: location.href}, '*'); });
setInterval(() => parent.postMessage({alive: 1}, '*'), 300);
</script></body></html>"""
PROBE = {"kind": "games", "slug": "probe", "name": "Probe", "by": "test", "blurb": "x", "status": "ok",
         "reviews": {"randy": None, "maker": None}, "file": "games/probe/item.html"}
OUTSIDE = "[...F.document.querySelectorAll('a[href]')].filter(a => /^https?:\\/\\//i.test(a.getAttribute('href')))"


def test(page, check):
    base = harness.serve(lambda p: (PROBE_PAGE, "text/html") if p == "/games/probe/item.html" else None, [PROBE])
    page.go(base + "index.html#/games/probe/play")
    page.until("!!document.querySelector('.play iframe[sandbox]')")
    page.js("""window.__opened = []; window.open = (u, t, f) => { __opened.push([u, t, f]); return null; }; window.__done = [];
      addEventListener('message', e => { if (e.data && e.data.done) __done.push(e.data); if (e.data && e.data.alive) window.__alive = 1; });
      window.__tell = d => document.querySelector('.play iframe').contentWindow.postMessage({do: d}, '*');""")
    bar = "(document.querySelector('.play .ask') || {})"
    check("the test game runs in the player", page.until("window.__alive"))
    check("no ask bar before any link", page.js(f"{bar}.hidden") is True)
    page.js("__tell('click')"); time.sleep(0.8)
    check("clicking a link in the game shows the ask bar", page.js(f"{bar}.hidden") is False)
    check("it names the real site", "example.com" in (page.js(f"{bar}.textContent") or ""), page.js(f"{bar}.textContent"))
    check("nothing opened yet", page.js("__opened.length") == 0)
    check("the game stayed in the player", page.until("__done.some(m => m.done == 'click' && /player\\.html/.test(m.where))", 3))
    page.js("document.querySelector('[data-act=no-link]').click()"); time.sleep(0.3)
    check("'No' closes the bar and opens nothing", page.js(f"{bar}.hidden") is True and page.js("__opened.length") == 0)
    page.js("__tell('click')"); time.sleep(0.8)
    page.js("document.querySelector('[data-act=open-link]').click()"); time.sleep(0.3)
    opened = page.json("__opened")
    check("'Open it' opens exactly that address, in a new tab cut off from the shop",
          opened == [["https://example.com/some/page?x=1", "_blank", "noopener,noreferrer"]], opened)
    page.js("__tell('open')"); time.sleep(0.8)
    check("window.open in a game goes to the ask bar too", "example.org" in (page.js(f"{bar}.textContent") or "") and page.js(f"{bar}.hidden") is False)
    page.js("document.querySelector('[data-act=no-link]').click(); __tell('bad')"); time.sleep(0.8)
    check("javascript: and file: addresses are ignored", page.js(f"{bar}.hidden") is True, page.js(f"{bar}.textContent"))
    page.js("__tell('local')"); time.sleep(0.8)
    check("links within the game's own page aren't caught", page.js(f"{bar}.hidden") is True)
    check("still only one page opened", page.js("__opened.length") == 1)

    for it in harness.items():
        page.go(base + f"rig.html?{it['kind']}/{it['slug']}", ready="!!window.F && !!F.document.body && F.document.body.children.length > 0")
        time.sleep(1.5)
        hrefs = page.json(f"(() => {{ const L = {OUTSIDE}; L.forEach(a => a.click()); return L.map(a => a.getAttribute('href')); }})()") or []
        time.sleep(0.8)
        got = [g["link"] for g in (page.json("got") or []) if "link" in g]
        if hrefs:
            check(f"{it['name']}: all {len(hrefs)} outside links on its first screen reach the shop's ask", got == hrefs, (len(hrefs), len(got)))
        check(f"{it['name']}: stays in the player", (page.js("F.location.pathname") or "").endswith("/site/player.html"))


harness.run(test)
