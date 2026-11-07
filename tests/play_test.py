"""Plays real rounds of the games that have a play check, under the player's own rules: not just "no errors", but
"the game does what it says". Each game below is one function; add one when a game needs more than ship_test's clicks.
    python tests/play_test.py                       every game here
    python tests/play_test.py sandwich-master ...    just these"""
import json, re, sys, time

import harness

D = "F.document"


def helpers(page):
    click = lambda sel: page.js(f"(() => {{ const e = {D}.querySelector({json.dumps(sel)}); if (!e) return false; e.click(); return true; }})()")
    text = lambda sel: page.js(f"({D}.querySelector({json.dumps(sel)}) || {{}}).textContent || ''") or ""
    errs = lambda: page.json("F.__errs.concat(F.__csp.filter(c => !/http/.test(c)))") or []
    return click, text, errs


def sandwich_master(page, check):
    click, text, errs = helpers(page)
    click("#play"); time.sleep(0.5)
    perfect = 0
    for k in range(3):
        click("#open"); time.sleep(1.8)
        check(f"Sandwich Master: order {k + 1}: takes the order", click("#take")); time.sleep(1.2)
        m = re.search(r"Ticket:\s*(\w+) bread → (.*?)Bread first", text(".ticket"))
        parts = [m.group(1)] + [x.strip() for x in m.group(2).split("→")] if m else []
        for p in parts:
            page.js(f"[...{D}.querySelectorAll('#ings button')].find(b => b.textContent == {json.dumps(p)}).click()")
        click("#wrap"); time.sleep(1.0)
        click("#srv"); time.sleep(1.4)
        perfect += "Perfect" in text("#msg")
        time.sleep(2.5)
    check("Sandwich Master: three orders built from the ticket are all served perfect", perfect == 3, perfect)
    check("Sandwich Master: no errors", not errs(), errs())


def hotdog_tycoon(page, check):
    click, text, errs = helpers(page)
    click("#playBtn"); time.sleep(1.5)
    cash = text("#cash")
    for _ in range(140):
        page.js(f"(() => {{ const s = {D}.getElementById('scene'), r = s.getBoundingClientRect(); s.dispatchEvent(new F.MouseEvent('click', {{bubbles: true, clientX: r.right - 160, clientY: r.top + 120}})); }})()")
        time.sleep(0.25)
    check("Hotdog Tycoon: customers get served and cash comes in", text("#cash") != cash and text("#served").strip() not in ("", "0"), (cash, text("#cash")))
    bought = page.js(f"(() => {{ const b = [...{D}.querySelectorAll('#items button')].find(b => !b.disabled); if (!b) return ''; b.click(); return b.textContent; }})()")
    check("Hotdog Tycoon: an upgrade can be bought", bool(bought), page.js(f"[...{D}.querySelectorAll('#items button')].map(b => b.textContent.slice(0, 20)).join(' | ')"))
    snap = f"(() => {{ const c = {D}.querySelector('#bandstand canvas'), d = c.getContext('2d').getImageData(0, 0, c.width, c.height).data; let h = 0, n = 0; for (let i = 3; i < d.length; i += 41) {{ h = (h * 31 + d[i - 1]) | 0; n += d[i] > 0; }} return [h, n]; }})()"
    shots = []
    for _ in range(5):
        shots.append(page.json(snap) or [0, 0]); time.sleep(0.15)
    check("Hotdog Tycoon: the Raisin Band busks beside the line, dressed for the beach, and moves",
          page.js("F.Band.theme") == "tropic" and min(n for _, n in shots) > 500 and len({h for h, _ in shots}) >= 3, [page.js("F.Band.theme"), shots[:2]])
    check("Hotdog Tycoon: the band stands over the scene without blocking clicks",
          page.js(f"getComputedStyle({D}.getElementById('bandstand')).pointerEvents") == "none")
    check("Hotdog Tycoon: no errors", not errs(), errs())


def pachinko_player(page, check):
    click, text, errs = helpers(page)
    balls = text("#balls")
    click("#auto"); time.sleep(15); click("#auto")
    check("Pachinko Player: balls fly and get counted", text("#balls") != balls, (balls, text("#balls")))
    click('[data-s="counter"]'); time.sleep(0.3)
    yen = text("#yen"); click("#buyBtn"); time.sleep(0.3)
    check("Pachinko Player: renting balls costs yen", text("#yen") != yen)
    click('[data-tok="s"]'); time.sleep(0.3)
    check("Pachinko Player: a token can be bought", text("#ts").strip() not in ("", "0"), text("#cmsg"))
    click('[data-s="alley"]'); time.sleep(0.3)
    for _ in range(80):
        if text("#ah") == "The little window":
            break
        click("#routes button"); time.sleep(0.25)
    # a pickpocket on the way can take the token; either way the window answers
    check("Pachinko Player: the back alley reaches the window, and it answers",
          text("#ah") == "The little window" and ("in cash" in text("#log") or "no tokens" in text("#log")), text("#log"))
    check("Pachinko Player: no errors", not errs(), errs())


def battle_tanks_royale(page, check):
    click, text, errs = helpers(page)
    key = lambda kind, code, k: page.js(f"for (const t of [F, {D}]) t.dispatchEvent(new F.KeyboardEvent('{kind}', {{code: '{code}', key: '{k}', bubbles: true}}))")
    press = lambda words: page.js(f"(() => {{ const b = [...{D}.querySelectorAll('button')].find(b => b.getClientRects().length && b.textContent.includes({json.dumps(words)})); if (!b) return false; b.click(); return true; }})()")
    frame = lambda: page.js(f"(() => {{ const c = {D}.getElementById('cv'), d = c.getContext('2d').getImageData(0, 0, c.width, c.height).data; let h = 0; for (let i = 0; i < d.length; i += 37) h = (h * 31 + d[i]) | 0; return h; }})()")

    def battle(label, secs):
        frames = set()
        key("keydown", "KeyW", "w")
        for i in range(int(secs / 0.3)):
            key("keydown", "Space", " "); time.sleep(0.15); key("keyup", "Space", " ")
            if i % 6 == 0:
                key("keydown", "KeyA", "a"); time.sleep(0.15); key("keyup", "KeyA", "a")
            else:
                time.sleep(0.15)
            frames.add(frame())
        key("keyup", "KeyW", "w")
        check(f"Battle Tanks Royale: {label}: the battle runs (the picture keeps changing)", len(frames) > 10, len(frames))
        key("keydown", "Escape", "Escape"); time.sleep(0.5); press("Back"); time.sleep(0.5)

    check("Battle Tanks Royale: Defend starts", press("Defend Your Base")); time.sleep(1); battle("Defend", 15)
    check("Battle Tanks Royale: Story opens", press("Story")); time.sleep(0.5)
    page.js(f"{D}.querySelector('#chs [onclick]').click()"); time.sleep(0.5)
    check("Battle Tanks Royale: chapter 1 deploys", press("Deploy")); time.sleep(1); battle("Story", 10)
    press("Versus a Friend"); time.sleep(0.5)
    check("Battle Tanks Royale: a same-keyboard match starts", press("Start local match")); time.sleep(1); battle("Same keyboard", 8)
    press("Versus a Friend"); time.sleep(0.5); press("Host a game"); time.sleep(6.5)
    check("Battle Tanks Royale: online play with no app behind it says so", "only works in a Randis UDS app" in text("#nst"), text("#nst"))
    press("Back"); time.sleep(0.5)
    check("Battle Tanks Royale: Garage opens", press("Garage"))
    check("Battle Tanks Royale: no errors", not errs(), errs())


GAMES = {"sandwich-master": sandwich_master, "hotdog-tycoon": hotdog_tycoon, "pachinko-player": pachinko_player,
         "battle-tanks-royale": battle_tanks_royale}


def test(page, check):
    base = harness.serve()
    for slug in sys.argv[1:] or GAMES:
        page.go(base + f"frame.html?/walled/games/{slug}", ready="!!window.F && F.document.readyState === 'complete'")
        time.sleep(1.5)
        GAMES[slug](page, check)


harness.run(test)
