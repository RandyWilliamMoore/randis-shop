"""Every item, or the ones named, as a visitor meets it: listed with its logo, its page and real-items link, Play opening
the walled player. Then the item runs under the player's own rules, and every button on its first screen is clicked.
    python tests/ship_test.py                  every item
    python tests/ship_test.py dice-master ...   just these"""
import json, sys, time

import harness

CLICK = """(() => { const D = F.document; let n = 0; const seen = new Set();
  for (let round = 0; round < 3; round++) for (const e of [...D.querySelectorAll('button,[onclick],.btn')].filter(e => e.getClientRects().length > 0)) {
    const k = (e.id || '') + '|' + (e.textContent || '').trim().slice(0, 30); if (seen.has(k)) continue; seen.add(k);
    try { e.click() } catch (x) { F.__errs.push('click: ' + x) } n++; }
  return n; })()"""


def test(page, check):
    base = harness.serve()
    want = sys.argv[1:]
    for it in [i for i in harness.items() if not want or i["slug"] in want]:
        name, kind, slug = it["name"], it["kind"], it["slug"]
        page.go(base + f"index.html#/{kind}")
        check(f"{name}: its logo shows in the shop", page.until(f"[...document.images].some(i => i.src.endsWith({json.dumps(it['logo'])}) && i.complete && i.naturalWidth > 0)"))
        page.go(base + f"index.html#/{kind}/{slug}")
        check(f"{name}: its page opens", page.until(f"document.title.startsWith({json.dumps(name)})"), page.js("document.title"))
        if it.get("real_items"):
            check(f"{name}: its real-items link", page.until(f"!!document.querySelector('.real a[href={json.dumps(it['real_items'])}]')"))
        page.go(base + f"index.html#/{kind}/{slug}/play")
        check(f"{name}: Play opens the walled player", page.until("!!document.querySelector('.play iframe[sandbox]')"))
        time.sleep(2)
        check(f"{name}: it loads there", "wouldn't load" not in (page.js("(document.querySelector('.walled span') || {}).textContent") or ""))

        page.go(base + f"frame.html?/walled/{kind}/{slug}", ready="!!window.F && F.document.readyState === 'complete'")
        time.sleep(1.5)
        start = page.json("{errs: F.__errs, text: F.document.body.innerText.length}") or {}
        check(f"{name}: starts with no errors under the player's rules", start.get("errs") == [], start.get("errs"))
        check(f"{name}: shows something", start.get("text", 0) > 50, start.get("text"))
        page.until("[...F.document.querySelectorAll('button,[onclick],.btn')].some(e => e.getClientRects().length > 0)")   # some draw their buttons a moment after loading
        clicked = page.js(CLICK) or 0
        time.sleep(2)
        after = page.json("{errs: F.__errs, csp: F.__csp}") or {}
        check(f"{name}: every button on its first screen clicks with no error ({clicked})", clicked > 0 and after.get("errs") == [], after.get("errs"))
        # loads from the internet are blocked behind the wall on purpose; anything else blocked means the item needs it and can't have it
        check(f"{name}: the player's rules block nothing it needs", not [c for c in after.get("csp", []) if "http" not in c], after.get("csp"))


harness.run(test)
