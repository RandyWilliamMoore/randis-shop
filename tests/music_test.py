"""The Jukebox and the music it holds: Randis Sound Forge makes elevator music and saves it, add_music.py puts a song in the
Jukebox, and the shop plays it and hands it out royalty free. Also Sound Forge's own Save button inside the real shop.
    python tests/music_test.py"""
import base64, io, json, math, os, shutil, struct, subprocess, sys, tempfile, time, wave

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
COVER = base64.b64decode("/9j/4AAQSkZJRgABAQEASABIAAD/2wBDAP//////////////////////////////////////////////////////////////////////////////////////wgALCAABAAEBAREA/8QAFBABAAAAAAAAAAAAAAAAAAAAAP/aAAgBAQABPxA=")
SONG_ENTRY = {"kind": "music", "slug": "lobby-test", "name": "Lobby Test", "by": "Randy", "blurb": "A test song.", "genre": "Elevator Music",
              "length": "0:03", "added": "2026-11-07", "file": "music/lobby-test/song.wav", "cover": "music/lobby-test/cover.jpg",
              "download": "Lobby Test.wav"}
# what the shop page saves, read back from the file it hands the browser (the same recorder as save_test.py)
RECORD = """window.__saved = []; window.__files = {};
const __make = URL.createObjectURL; URL.createObjectURL = b => { const u = __make.call(URL, b); __files[u] = b; return u; };
const __press = HTMLAnchorElement.prototype.click;
HTMLAnchorElement.prototype.click = function () {
  if (!this.download) return __press.call(this);
  const name = this.download; __files[this.href].arrayBuffer().then(b => { const u = new Uint8Array(b);
    __saved.push({file: name, size: u.length, head: String.fromCharCode(...u.slice(0, 4))}); }); };"""


def probe(path):
    """What's inside an MP3, read by ffprobe: its tags and whether it carries a picture."""
    import add_music_tools
    r = subprocess.run([add_music_tools.ffmpeg("ffprobe"), "-v", "error", "-show_entries", "format_tags:stream=codec_type,codec_name:stream_disposition=attached_pic",
                        "-of", "json", path], capture_output=True, text=True)
    return json.loads(r.stdout or "{}")


def tools_check(check):
    """add_music.py and build_index.py in a scratch copy of the shop's tools, so the real shop isn't touched."""
    top = tempfile.mkdtemp(prefix="jukebox_test_")
    try:
        shutil.copytree(os.path.join(harness.SHOP, "tools"), os.path.join(top, "tools"))
        os.makedirs(os.path.join(top, "site"))
        shutil.copyfile(os.path.join(harness.SHOP, "site", "band.js"), os.path.join(top, "site", "band.js"))
        sys.path.insert(0, os.path.join(top, "tools"))
        sys.modules["add_music_tools"] = __import__("add_music")
        song = os.path.join(top, "My Lobby Song.wav")
        with open(song, "wb") as f:
            f.write(SONG)
        run = lambda *a: subprocess.run([sys.executable, os.path.join(top, "tools", "add_music.py"), *a], capture_output=True, text=True)
        r = run(song, "--name", "My Lobby Song!", "--genre", "Elevator Music", "--blurb", "Soft and slow, for a hotel lobby.")
        folder = os.path.join(top, "music", "my-lobby-song")
        info = json.load(open(os.path.join(folder, "info.json"), encoding="utf-8")) if r.returncode == 0 else {}
        check("add_music.py puts a song in the Jukebox: an MP3, its cover and its info, with the length read from the file",
              r.returncode == 0 and info.get("length") == "0:03" and info.get("blurb") == "Soft and slow, for a hotel lobby."
              and sorted(os.listdir(folder)) == ["cover.jpg", "info.json", "song.mp3"], r.stdout + r.stderr)
        mp3 = os.path.join(folder, "song.mp3")
        sound = os.path.getsize(mp3) - os.path.getsize(os.path.join(folder, "cover.jpg")) if os.path.isfile(mp3) else 0
        check("the WAV became a real MP3, its sound a fraction of the WAV's size", open(mp3, "rb").read(3) == b"ID3" and 0 < sound < len(SONG) / 2, (sound, len(SONG)))
        inside = probe(mp3) if os.path.isfile(mp3) else {}
        tags = {k.lower(): v for k, v in inside.get("format", {}).get("tags", {}).items()}
        check("the MP3 carries its title, artist, album, genre and year", tags.get("title") == "My Lobby Song!" and tags.get("artist") == "Randy Moore"
              and tags.get("album") == "Randis Shop Jukebox" and tags.get("genre") == "Elevator Music" and tags.get("date", "").isdigit(), tags)
        check("and its description and the royalty-free note", tags.get("comment") == "Soft and slow, for a hotel lobby."
              and "Royalty free" in tags.get("copyright", "") and "randis-shop" in tags.get("copyright", ""), tags)
        pics = [st for st in inside.get("streams", []) if st.get("codec_type") == "video" and st.get("disposition", {}).get("attached_pic") == 1]
        check("and its cover art", len(pics) == 1 and pics[0].get("codec_name") == "mjpeg", inside.get("streams"))
        from PIL import Image
        art = Image.open(os.path.join(folder, "cover.jpg")) if os.path.isfile(os.path.join(folder, "cover.jpg")) else None
        colours = len(art.resize((50, 50)).getcolors(10000) or []) if art else 0
        check("the cover is a square picture of the band, not a blank", art and art.size == (1000, 1000) and colours > 200, (art and art.size, colours))
        listed = open(os.path.join(top, "music.js"), encoding="utf-8").read()
        check("music.js lists it, with its cover and a plain download name", '"download": "My Lobby Song.mp3"' in listed
              and '"cover": "music/my-lobby-song/cover.jpg"' in listed, listed[:400])
        mine = os.path.join(top, "mine.png")
        Image.new("RGB", (640, 400), (20, 140, 90)).save(mine)
        r = run(song, "--name", "Own Art", "--genre", "Celtic", "--blurb", "x", "--cover", mine)
        own = Image.open(os.path.join(top, "music", "own-art", "cover.jpg")) if r.returncode == 0 else None
        check("--cover uses your own picture, squared to 1000 x 1000", own and own.size == (1000, 1000) and abs(own.getpixel((500, 500))[1] - 140) < 12, r.stderr)
        check("a song with no description is refused", run(song, "--name", "No Words", "--genre", "x", "--blurb", " ").returncode != 0
              and not os.path.exists(os.path.join(top, "music", "no-words")))
        check("the same name twice is refused", run(song, "--name", "My Lobby Song!", "--genre", "x", "--blurb", "x").returncode != 0)
        bad = os.path.join(top, "page.html")
        open(bad, "w").write("<p>x</p>")
        check("anything but a song file is refused", run(bad, "--name", "Page", "--genre", "x", "--blurb", "x").returncode != 0 and not os.path.exists(os.path.join(top, "music", "page")))
        os.remove(os.path.join(top, "music", "own-art", "cover.jpg"))
        r = subprocess.run([sys.executable, os.path.join(top, "tools", "build_index.py")], capture_output=True, text=True)
        check("a song with no cover stops the build", r.returncode != 0 and "cover.jpg" in r.stdout + r.stderr, r.stdout + r.stderr)
        shutil.rmtree(os.path.join(top, "music", "own-art"))
        open(os.path.join(folder, "extra.exe"), "w").write("MZ")
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
    check("with no app saying publishing is set up (the shop, or anyone else's copy), there's no Publish button",
          page.js("!F.document.getElementById('pubBtn')") is True)
    # inside Randis UDS with publishing set up: the app answers, and the button and its filled-in form appear
    page.js("""addEventListener('message', e => { if (!e.data) return;
      if (e.data.uds === 'can-publish') e.source.postMessage({uds: 'can-publish', ok: true, shop: 'Test Shop'}, '*');
      if (e.data.uds === 'publish-song') window.__pub = {title: e.data.title, blurb: e.data.blurb, genre: e.data.genre, size: e.data.data.size, head: ''}; });""")
    page.js("setTimeout(() => F.document.getElementById('expSong').click(), 0)")
    check("where publishing is set up, a Publish button sits beside Save", page.until("!!F.document.getElementById('pubBtn')", 90)
          and "Test Shop" in (page.js("F.document.getElementById('pubBtn').textContent") or ""))
    page.js("F.document.getElementById('pubBtn').click()")
    form = page.json("({t: F.document.getElementById('pubTitle').value, b: F.document.getElementById('pubBlurb').value, g: F.document.getElementById('pubGenre').value})") or {}
    check("its form comes filled in: a made-up title, a description from the song's settings, the genre",
          len(form.get("t", "")) > 3 and "Elevator Music song at" in form.get("b", "") and "BPM" in form.get("b", "") and form.get("g") == "Elevator Music", form)
    page.js("F.document.getElementById('pubRoll').click()")
    titles = {form.get("t")}
    for _ in range(4):
        titles.add(page.js("F.document.getElementById('pubTitle').value")); page.js("F.document.getElementById('pubRoll').click()")
    check("the dice give other titles", len(titles) >= 3, titles)
    page.js("F.document.getElementById('pubTitle').value = 'My Own Title'; F.document.getElementById('pubGo').click()")
    pub = page.json("window.__pub") if page.until("!!window.__pub", 5) else None
    check("Publish hands the app the song with your title, the description and the genre",
          bool(pub) and pub["title"] == "My Own Title" and pub["genre"] == "Elevator Music" and pub["blurb"] == form.get("b") and pub["size"] > 100000, pub)
    check("and says to answer the app's question", "Say yes" in (page.js("F.document.getElementById('pubNote').textContent") or ""))
    # the Raisin Band, inside Sound Forge
    forge = open(os.path.join(harness.SHOP, "apps", "randis-sound-forge", "item.html"), encoding="utf-8").read().replace("\r\n", "\n")
    inside = forge.split('<script id="raisin-band">\n', 1)[-1].split("</script>", 1)[0]
    shop_band = open(os.path.join(harness.SHOP, "site", "band.js"), encoding="utf-8").read().replace("\r\n", "\n")
    check("Sound Forge's Raisin Band is the same as the Jukebox's (site/band.js)", inside == shop_band, (len(inside), len(shop_band)))
    cap = lambda: page.js("(F.document.querySelector('#bandCard .band-cap') || {}).textContent || ''") or ""
    check("Sound Forge shows the band's stage, rehearsing before you play", page.until("(F.document.querySelector('#bandCard .band-cap') || {}).textContent.startsWith('Rehearsing')", 3), cap())
    page.js("F.document.getElementById('play').click()")
    playing = page.until("F.Band.theme === 'elevator' && F.document.querySelector('#bandCard .band-cap').textContent.startsWith('Now playing')", 6)
    check("pressing Play brings on the lobby band for elevator music", playing, [page.js("F.Band.theme"), cap()])
    snap = "(() => { const c = F.document.querySelector('#bandCard canvas'), d = c.getContext('2d').getImageData(0, 0, c.width, c.height).data; let h = 0; for (let i = 0; i < d.length; i += 41) h = (h * 31 + d[i]) | 0; return h; })()"
    frames = set()
    for _ in range(6):
        frames.add(page.js(snap)); time.sleep(0.15)
    check("the band moves with the song", len(frames) >= 4, len(frames))
    page.js("(() => { const e = F.document.getElementById('era'); e.value = 'Medieval tavern'; e.dispatchEvent(new F.Event('change')); })()")
    check("switching the era to Medieval tavern changes into the castle band, mid-song", page.until("F.Band.theme === 'medieval'", 3), page.js("F.Band.theme"))
    page.js("F.document.getElementById('stop').click()")
    check("Stop sends the band back to rehearsing", page.until("F.document.querySelector('#bandCard .band-cap').textContent.startsWith('Rehearsing')", 3), cap())

    # the Jukebox in the shop
    def extra(path):
        if path == "/music.js":
            return "window.MUSIC = " + json.dumps([SONG_ENTRY]) + ";", "application/javascript"
        if path == "/music/lobby-test/song.wav":
            return SONG, "audio/wav"
        if path == "/music/lobby-test/cover.jpg":
            return COVER, "image/jpeg"
    base = harness.serve(extra)
    page.go(base + "index.html#/")
    page.until("!!document.querySelector('.jukebox')")
    check("the front door has the Jukebox, with the song", "Lobby Test" in (page.js("document.querySelector('.jukebox').textContent") or ""))
    check("the menu has a Jukebox button", page.js("[...document.querySelectorAll('.nav a')].some(a => a.getAttribute('href') === '#/music')") is True)
    page.js("location.hash = '#/music/lobby-test'"); time.sleep(0.6)
    check("each song shows its cover art", page.js("(() => { const i = document.querySelector('#song-lobby-test .track-cover'); return !!i && i.getAttribute('src') === 'music/lobby-test/cover.jpg'; })()") is True)
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
    cap = page.js("document.querySelector('.band-cap').textContent") or ""
    check("the Raisin Band plays along, dressed for the song: an elevator song gets the lobby band",
          page.js("Band.theme") == "elevator" and cap.startswith("Now playing: Lobby Test"), [page.js("Band.theme"), cap])
    snap = "(() => { const c = document.querySelector('.band-stage'), d = c.getContext('2d').getImageData(0, 0, c.width, c.height).data; let h = 0; for (let i = 0; i < d.length; i += 41) h = (h * 31 + d[i]) | 0; return h; })()"
    frames = set()
    for _ in range(6):
        frames.add(page.js(snap)); time.sleep(0.15)
    check("the band is moving", len(frames) >= 4, len(frames))
    picks = page.json("['Deep House', 'SNES Style', 'Celtic', 'Heavy Metal', 'Hardcore Punk', 'Lo-fi Hip Hop', 'Bossa Nova', 'Baroque', 'Sleep', 'Bluegrass', 'K-Pop'].map(g => Band.themeFor(g).id)")
    check("each genre gets its own band: house DJs, a 16-bit fantasy party, a castle band, rockers...", picks ==
          ["club", "quest", "medieval", "rock", "rock", "lofi", "jazz", "orchestra", "ambient", "country", "pop"], picks)
    page.js("document.querySelector('.track audio').pause()"); time.sleep(0.4)
    check("with the song paused, the band rehearses", (page.js("document.querySelector('.band-cap').textContent") or "").startswith("Rehearsing"))
    check("Sound Forge is linked from the Jukebox", page.js("!!document.querySelector('.jukebox a[href=\"#/apps/randis-sound-forge\"]')") is True)
    base = harness.serve(lambda p: ("window.MUSIC = [];", "application/javascript") if p == "/music.js" else None)
    page.go(base + "index.html#/music")
    page.until("!!document.querySelector('.jukebox')")
    check("an empty Jukebox says songs are coming", "on their way" in (page.js("document.querySelector('.jukebox').textContent") or ""))
    check("and the band still rehearses on its stage", page.until("(document.querySelector('.band-cap') || {}).textContent.startsWith('Rehearsing')", 3))

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
