"""The Jukebox and the music it holds: Randis Sound Forge makes elevator music and saves it, add_music.py puts a song in the
Jukebox, and the shop plays it and hands it out royalty free. Also Sound Forge's own Save button inside the real shop.
    python tests/music_test.py"""
import io, json, math, os, shutil, struct, subprocess, sys, tempfile, time, wave

import harness


def a_song(secs=3):
    """A real WAV: a soft tone that steps up a major scale."""
    rate, frames = 22050, io.BytesIO()
    with wave.open(frames, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(rate)
        steps = [0, 2, 4, 5, 7, 9, 11, 12]
        w.writeframes(b"".join(struct.pack("<h", int(6000 * math.sin(2 * math.pi * 261.6 * 2 ** (steps[i * 8 // (rate * secs)] / 12) * i / rate)))
                               for i in range(rate * secs)))
    return frames.getvalue()


SONG = a_song()
SONG_ENTRY = {"kind": "music", "slug": "lobby-test", "name": "Lobby Test", "by": "Randy", "blurb": "A test song.", "genre": "Elevator Music",
              "length": "0:03", "added": "2026-11-07", "file": "music/lobby-test/song.wav", "download": "Lobby Test.wav"}
# what the shop page saves, read back from the file it hands the browser (the same recorder as save_test.py)
RECORD = """window.__saved = []; window.__files = {};
const __make = URL.createObjectURL; URL.createObjectURL = b => { const u = __make.call(URL, b); __files[u] = b; return u; };
const __press = HTMLAnchorElement.prototype.click;
HTMLAnchorElement.prototype.click = function () {
  if (!this.download) return __press.call(this);
  const name = this.download; __files[this.href].arrayBuffer().then(b => { const u = new Uint8Array(b);
    __saved.push({file: name, size: u.length, head: String.fromCharCode(...u.slice(0, 4))}); }); };"""


def tools_check(check):
    """add_music.py and build_index.py in a scratch copy of the shop's tools, so the real shop isn't touched."""
    top = tempfile.mkdtemp(prefix="jukebox_test_")
    try:
        shutil.copytree(os.path.join(harness.SHOP, "tools"), os.path.join(top, "tools"))
        song = os.path.join(top, "My Lobby Song.wav")
        with open(song, "wb") as f:
            f.write(SONG)
        run = lambda *a: subprocess.run([sys.executable, os.path.join(top, "tools", "add_music.py"), *a], capture_output=True, text=True)
        r = run(song, "--name", "My Lobby Song!", "--genre", "Elevator Music", "--blurb", "Soft and slow.")
        info = json.load(open(os.path.join(top, "music", "my-lobby-song", "info.json"), encoding="utf-8")) if r.returncode == 0 else {}
        check("add_music.py puts a song in the Jukebox, with its length read from the file",
              r.returncode == 0 and info.get("length") == "0:03" and info.get("genre") == "Elevator Music"
              and os.listdir(os.path.join(top, "music", "my-lobby-song")) == ["info.json", "song.mp3"], r.stdout + r.stderr)
        mp3 = os.path.join(top, "music", "my-lobby-song", "song.mp3")
        head = open(mp3, "rb").read(3) if os.path.isfile(mp3) else b""
        check("the WAV became a real, smaller MP3", (head == b"ID3" or head[:1] == bytes([255])) and os.path.getsize(mp3) < len(SONG) / 2,
              (head, os.path.getsize(mp3) if head else 0, len(SONG)))
        listed = open(os.path.join(top, "music.js"), encoding="utf-8").read()
        check("music.js lists it, with a plain download name", '"download": "My Lobby Song.mp3"' in listed and '"file": "music/my-lobby-song/song.mp3"' in listed, listed[:300])
        r = run(song, "--name", "Kept", "--genre", "x", "--keep-wav")
        check("--keep-wav keeps the WAV", r.returncode == 0 and os.path.isfile(os.path.join(top, "music", "kept", "song.wav")), r.stdout + r.stderr)
        check("the same name twice is refused", run(song, "--name", "My Lobby Song!", "--genre", "x").returncode != 0)
        bad = os.path.join(top, "page.html")
        open(bad, "w").write("<p>x</p>")
        check("anything but a song file is refused", run(bad, "--name", "Page", "--genre", "x").returncode != 0 and not os.path.exists(os.path.join(top, "music", "page")))
        open(os.path.join(top, "music", "my-lobby-song", "extra.exe"), "w").write("MZ")
        r = subprocess.run([sys.executable, os.path.join(top, "tools", "build_index.py")], capture_output=True, text=True)
        check("a song folder with anything else in it stops the build", r.returncode != 0 and "don't belong" in r.stdout + r.stderr, r.stdout + r.stderr)
    finally:
        shutil.rmtree(top, ignore_errors=True)


def test(page, check):
    tools_check(check)

    # Sound Forge makes elevator music, and its Save hands over the song
    base = harness.serve()
    page.go(base + "rig.html?apps/randis-sound-forge", ready="!!window.F && !!F.document.getElementById('expSong')")
    time.sleep(1.5)
    picked = page.json("""(() => { const d = F.document, set = (id, v) => { const e = d.getElementById(id); e.value = v; e.onchange && e.onchange(); };
      set('cat', 'Functional & Long-form'); set('genre', 'Elevator & Lobby'); set('sub', 'Elevator Music');
      return {subs: [...d.getElementById('sub').options].map(o => o.value), bpm: +d.getElementById('bpm').value, scale: d.getElementById('scale').value,
              drums: d.getElementById('drums').value, lead: d.getElementById('w_lead').value, kit: d.getElementById('kit').value}; })()""") or {}
    check("Sound Forge has an Elevator & Lobby genre", picked.get("subs", [])[:2] == ["Elevator Music", "Hotel Lobby"], picked)
    check("elevator music comes out soft and easy: slow, major key, brushed swing, a bell lead",
          84 <= picked.get("bpm", 0) <= 104 and picked.get("scale") == "major" and picked.get("drums") == "swing"
          and picked.get("lead") == "bell" and picked.get("kit") == "acoustic", picked)
    cut = page.js("(() => { const d = F.document, e = d.getElementById('era'); e.value = 'Elevator speaker'; e.onchange(); return +d.getElementById('cut').value; })()")
    check("the Elevator speaker sound narrows the tone like a small ceiling speaker", cut == 3800, cut)
    page.js("(() => { const d = F.document, f = d.getElementById('form'); f.value = 'short'; f.dispatchEvent(new F.Event('change')); })()")
    page.js("setTimeout(() => F.document.getElementById('expSong').click(), 0)")
    rendered = page.until("!!F.document.querySelector('#expOut button')", 90)
    page.js("setTimeout(() => F.document.querySelector('#expOut button').click(), 0)")
    page.until("got.length >= 1", 10)
    got = page.json("got") or []
    check("an elevator song renders, and Save hands over a real WAV", rendered and len(got) == 1 and got[0]["head"] == "RIFF"
          and got[0]["name"].endswith(".wav") and got[0]["size"] > 100000, got)
    check("after Save, Sound Forge says it's saved", "Saved" in (page.js("F.document.querySelector('#expOut .row span').textContent") or ""))

    # the Jukebox in the shop
    def extra(path):
        if path == "/music.js":
            return "window.MUSIC = " + json.dumps([SONG_ENTRY]) + ";", "application/javascript"
        if path == "/music/lobby-test/song.wav":
            return SONG, "audio/wav"
    base = harness.serve(extra)
    page.go(base + "index.html#/")
    page.until("!!document.querySelector('.jukebox')")
    check("the front door has the Jukebox, with the song", "Lobby Test" in (page.js("document.querySelector('.jukebox').textContent") or ""))
    check("the menu has a Jukebox button", page.js("[...document.querySelectorAll('.nav a')].some(a => a.getAttribute('href') === '#/music')") is True)
    page.js("location.hash = '#/music/lobby-test'"); time.sleep(0.6)
    check("a song's own link shows the Jukebox and points out that song", page.js("!!document.querySelector('#song-lobby-test.picked')") is True)
    check("the terms say royalty free, paid work included, no payment",
          all(w in (page.js("document.querySelector('.terms').textContent") or "") for w in ("Royalty free", "paid work", "No payment")))
    link = page.json("(() => { const a = document.querySelector('[data-act=download-song]'); return [a.getAttribute('href'), a.download]; })()")
    check("its download button hands out the song under its own name", link == ["music/lobby-test/song.wav", "Lobby Test.wav"], link)
    page.js("window.__csp = []; document.addEventListener('securitypolicyviolation', e => __csp.push(e.violatedDirective)); "
            "const a = document.querySelector('.track audio'); a.muted = true; a.play().catch(e => window.__playErr = String(e));")
    played = page.until("document.querySelector('.track audio').currentTime > 0.5", 10)
    check("the song plays right in the shop, under the shop's rules", played and not page.json("__csp") and not page.js("window.__playErr"),
          [page.js("document.querySelector('.track audio').currentTime"), page.json("__csp"), page.js("window.__playErr")])
    check("Sound Forge is linked from the Jukebox", page.js("!!document.querySelector('.jukebox a[href=\"#/apps/randis-sound-forge\"]')") is True)
    base = harness.serve(lambda p: ("window.MUSIC = [];", "application/javascript") if p == "/music.js" else None)
    page.go(base + "index.html#/music")
    page.until("!!document.querySelector('.jukebox')")
    check("an empty Jukebox says songs are coming", "on their way" in (page.js("document.querySelector('.jukebox').textContent") or ""))

    # Sound Forge's own Save button, in the real shop and the real walled player
    base = harness.serve()
    page.go(base + "index.html#/apps/randis-sound-forge/play")
    page.until("!!document.querySelector('.play iframe[sandbox]')")
    page.js(RECORD + "window.__heard = []; addEventListener('message', e => { if (e.data && e.data.uds === 'export-file') __heard.push(e.data.name); });")
    time.sleep(4)
    # the test can't reach into the walled frame, so it plays the frame's part: the same message its Save button sends
    page.js("""(() => { const b = new Uint8Array(4000); b.set([82, 73, 70, 70]);
      window.__reply = null; addEventListener('message', e => { if (e.data && e.data.uds === 'exported') window.__reply = e.data; });
      const f = document.querySelector('.play iframe');
      window.dispatchEvent(new MessageEvent('message', {source: f.contentWindow, data: {uds: 'export-file', name: 'elevator song.wav', data: new Blob([b])}})); })()""")
    page.until("__saved.length >= 1", 5)
    saved = page.json("__saved") or []
    check("an app's own Save button saves through the shop", saved[:1] == [{"file": "elevator song.wav", "size": 4000, "head": "RIFF"}], saved)
    check("the shop says where it went", "Saved elevator song.wav" in (page.js("document.querySelector('.walled span').textContent") or ""))
    time.sleep(1.6)
    page.js("""(() => { const f = document.querySelector('.play iframe');
      window.dispatchEvent(new MessageEvent('message', {source: f.contentWindow, data: {uds: 'export-file', name: 'page.html', data: new Blob(['<p>x'])}})); })()""")
    time.sleep(1)
    check("a page is still refused that way too", len(page.json("__saved") or []) == 1)


harness.run(test)
