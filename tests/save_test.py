"""Files a game or app makes (a song, a picture) are saved by the shop page, so the wall stays up: only known kinds,
under a plain name, one at a time. First the real apps that save, through the real player script; then a test game in the
real shop page and real player, trying files it shouldn't save.
    python tests/save_test.py"""
import time

import harness

PROBE_PAGE = """<!doctype html><html><head><meta charset="utf-8"></head><body><p>probe</p><script>
function wav() { const b = new ArrayBuffer(52), v = new DataView(b); 'RIFF'.split('').forEach((c, i) => v.setUint8(i, c.charCodeAt(0)));
  v.setUint32(4, 44, true); 'WAVE'.split('').forEach((c, i) => v.setUint8(8 + i, c.charCodeAt(0))); return new Blob([b], {type: 'audio/wav'}); }
function save(href, name, attach) { const a = document.createElement('a'); a.href = href; a.download = name; if (attach) document.body.append(a); a.click(); a.remove(); }
addEventListener('message', e => { const d = e.data && e.data.do; if (!d) return;
  if (d == 'wav') save(URL.createObjectURL(wav()), 'my song.wav', true);
  if (d == 'png') save('data:image/png;base64,iVBORw0KGgo=', 'painting.png', false);
  if (d == 'html') save(URL.createObjectURL(new Blob(['<p>page</p>'], {type: 'text/html'})), 'page.html', true);
  if (d == 'docx') save(URL.createObjectURL(new Blob(['PK\x03\x04'])), 'letter.docx', true);
  if (d == 'store') parent.postMessage({uds: 'store-get'}, '*');
  if (d == 'exe') save(URL.createObjectURL(new Blob(['MZ'])), 'setup.exe', true);
  if (d == 'svg') save(URL.createObjectURL(new Blob(['<svg/>'], {type: 'image/svg+xml'})), 'pic.svg', true);
  if (d == 'path') save(URL.createObjectURL(wav()), '../../Windows/x.wav', true);
  if (d == 'burst') for (let i = 0; i < 5; i++) save(URL.createObjectURL(wav()), 'b' + i + '.wav', true);
});
addEventListener('message', e => { if (e.data && e.data.uds === 'store-none') parent.postMessage({nostore: 1}, '*'); });
setInterval(() => parent.postMessage({alive: 1}, '*'), 300);
</script></body></html>"""
PROBE = {"kind": "games", "slug": "probe", "name": "Probe", "by": "test", "blurb": "x", "status": "ok",
         "reviews": {"randy": None, "maker": None}, "file": "games/probe/item.html"}
# what the shop page saves, read back from the file it hands the browser
RECORD = """window.__saved = []; window.__files = {};
const __make = URL.createObjectURL; URL.createObjectURL = b => { const u = __make.call(URL, b); __files[u] = b; return u; };
const __press = HTMLAnchorElement.prototype.click;
HTMLAnchorElement.prototype.click = function () {
  if (!this.download) return __press.call(this);
  const name = this.download; __files[this.href].arrayBuffer().then(b => { const u = new Uint8Array(b);
    __saved.push({file: name, size: u.length, head: String.fromCharCode(...u.slice(0, 4))}); }); };"""


def test(page, check):
    base = harness.serve(lambda p: (PROBE_PAGE, "text/html") if p == "/games/probe/item.html" else None, [PROBE])

    page.go(base + "rig.html?apps/randis-sound-forge", ready="!!window.F && !!F.document.getElementById('sfxExp')")
    time.sleep(1.5)
    page.js("setTimeout(() => F.document.getElementById('sfxExp').click(), 0)")
    rendered = page.until("!!F.document.querySelector('#sfxOut button')", 20)
    page.js("setTimeout(() => F.document.querySelector('#sfxOut button').click(), 0)")
    page.until("got.length >= 1", 8)
    got = page.json("got") or []
    check("Randis Sound Forge: Render WAV, then Save, hands the shop a real WAV",
          rendered and len(got) == 1 and got[0]["head"] == "RIFF" and got[0]["name"].endswith(".wav") and got[0]["size"] > 1000, got)

    page.go(base + "rig.html?apps/randis-paint", ready="!!window.F && !!F.document.getElementById('save')")
    page.js("setTimeout(() => F.document.getElementById('save').click(), 0)")
    page.until("got.length >= 1", 8)
    got = page.json("got") or []
    check("Randis Paint: Save PNG hands the shop a real PNG",
          len(got) == 1 and got[0]["name"] == "painting.png" and got[0]["head"] == "\x89PNG" and got[0]["size"] > 100, got)

    page.go(base + "index.html#/games/probe/play")
    page.until("!!document.querySelector('.play iframe[sandbox]')")
    page.js(RECORD + "window.__tell = d => document.querySelector('.play iframe').contentWindow.postMessage({do: d}, '*');"
            "addEventListener('message', e => { if (e.data && e.data.alive) window.__alive = 1; });")
    check("the test game runs in the player", page.until("window.__alive"))
    page.js("addEventListener('message', e => { if (e.data && e.data.nostore) window.__nostore = 1; }); __tell('store')")
    check("an app asking for Randis UDS storage hears at once that the shop keeps none", page.until("window.__nostore", 3))
    saved = lambda: page.json("__saved") or []
    page.js("__tell('wav')"); page.until("__saved.length >= 1", 4)
    check("a song made in memory is saved by the shop, bytes intact", saved()[:1] == [{"file": "my song.wav", "size": 52, "head": "RIFF"}], saved())
    check("the shop says where it went", "Saved my song.wav" in (page.js("document.querySelector('.walled span').textContent") or ""))
    time.sleep(1.6); page.js("__tell('png')"); page.until("__saved.length >= 2", 4)
    s = saved()
    check("a picture from a data link, on a link not in the page, is saved", len(s) == 2 and s[1]["file"] == "painting.png" and s[1]["head"] == "\x89PNG", s)
    time.sleep(1.6); page.js("__tell('docx')"); page.until("__saved.length >= 3", 4)
    s = saved()
    check("a Word document (Randis Office's export) is saved", len(s) == 3 and s[2]["file"] == "letter.docx" and s[2]["head"] == "PK\x03\x04", s[2:])
    for kind in ("html", "exe", "svg"):
        time.sleep(1.6); page.js(f"__tell('{kind}')"); time.sleep(1.2)
        check(f"a .{kind} file is refused", len(saved()) == 3, saved())
    time.sleep(1.6); page.js("__tell('path')"); page.until("__saved.length >= 4", 4)
    s = saved()
    check("folders in the name are flattened", len(s) == 4 and "/" not in s[3]["file"] and "\\" not in s[3]["file"] and s[3]["file"].endswith(".wav"), s[3:])
    time.sleep(1.6); page.js("__tell('burst')"); time.sleep(2)
    check("five saves at once: only one goes through", len(saved()) == 5, [x["file"] for x in saved()])
    check("the game stayed in the player", page.js("location.hash") == "#/games/probe/play")


harness.run(test)
