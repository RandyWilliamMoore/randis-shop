"""The Jukebox and the music it holds: Randis Sound Forge makes elevator music and saves it, add_music.py puts a song in the
Jukebox, and the shop plays it and hands it out royalty free. Also Sound Forge's own Save button inside the real shop.
    python tests/music_test.py"""
import base64, io, json, math, os, shutil, struct, subprocess, sys, tempfile, time, wave

import harness



def on_time(beats, bpm):
    """True when the beats the band heard keep time: most gaps are one beat (or two) at this tempo."""
    gaps = [round(b - a, 3) for a, b in zip(beats, beats[1:])]
    one = 60 / bpm
    good = [g for g in gaps if min(abs(g - one), abs(g - 2 * one)) < 0.07]
    return len(gaps) >= 4 and len(good) >= 0.8 * len(gaps), gaps

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
        credit = 'Music: "My Lobby Song!" by Randy Moore, from the Randis Shop (randywilliammoore.github.io/randis-shop)'
        check("and its description and the royalty-free terms, with credit required", tags.get("comment") == "Soft and slow, for a hotel lobby."
              and "Royalty free, with credit required" in tags.get("copyright", "") and credit in tags.get("copyright", ""), tags)
        check("and its exact credit line, in its own tag", tags.get("attribution") == credit, tags)
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
      if (e.data.uds === 'publish-song') window.__pub = {title: e.data.title, blurb: e.data.blurb, genre: e.data.genre, size: e.data.data.size, head: '',
        cover: String(e.data.cover || '').slice(0, 23), coverSize: String(e.data.cover || '').length}; });""")
    page.js("setTimeout(() => F.document.getElementById('expSong').click(), 0)")
    check("where publishing is set up, a Publish button sits beside Save", page.until("!!F.document.getElementById('pubBtn')", 90)
          and "Test Shop" in (page.js("F.document.getElementById('pubBtn').textContent") or ""))
    page.js("F.document.getElementById('pubBtn').click()")
    form = page.json("({t: F.document.getElementById('pubTitle').value, b: F.document.getElementById('pubBlurb').value, g: F.document.getElementById('pubGenre').value})") or {}
    check("its form shows the cover it will use: the band dressed for the genre, with the title",
          page.js("(F.document.getElementById('pubCover') || {}).src || ''").startswith("data:image/jpeg"))
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
    check("the cover goes with it", bool(pub) and pub["cover"] == "data:image/jpeg;base64," and pub["coverSize"] > 20000, pub and pub.get("coverSize"))
    check("if the app never answers, Publish doesn't stay stuck: it says so and can be pressed again",
          page.until("F.document.getElementById('pubNote').textContent.startsWith('No answer from Randis UDS') && !F.document.getElementById('pubGo').disabled", 12),
          page.js("F.document.getElementById('pubNote').textContent"))
    # the Raisin Band, inside Sound Forge
    shop_band = open(os.path.join(harness.SHOP, "site", "band.js"), encoding="utf-8").read().replace("\r\n", "\n")
    carriers = {}
    for it in harness.items():
        page_text = open(os.path.join(harness.SHOP, it["kind"], it["slug"], "item.html"), encoding="utf-8").read().replace("\r\n", "\n")
        if '<script id="raisin-band">' in page_text:
            carriers[it["slug"]] = page_text.split('<script id="raisin-band">\n', 1)[1].split("</script>", 1)[0] == shop_band
    check("every page carrying the Raisin Band has the same band as the Jukebox (tools/sync_band.py)",
          {"randis-sound-forge", "hotdog-tycoon"} <= set(carriers) and all(carriers.values()), carriers)
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
    pick = "(() => { const d = F.document; for (const [id, v] of %s) { const e = d.getElementById(id); e.value = v; e.dispatchEvent(new F.Event('change')); } })()"
    page.js(pick % '[["cat", "Electronic"], ["genre", "House"], ["sub", "Deep House"], ["era", "Auto"]]')
    bpm = int(page.js("F.document.getElementById('bpm').value"))
    page.js("F.document.getElementById('play').click()"); time.sleep(5)
    ok, gaps = on_time(page.json("F.Band.beats") or [], bpm)
    check(f"on Play, the band bounces on the song's own beat (Deep House at {bpm} BPM)", ok and page.js("F.Band.theme") == "club", [page.js("F.Band.theme"), gaps])
    page.js("F.document.getElementById('stop').click()")
    page.js(pick % '[["cat", "Functional & Long-form"], ["genre", "Elevator & Lobby"], ["sub", "Hotel Lobby"]]')
    page.js("F.document.getElementById('expLoop').click()")
    page.until("!!F.document.querySelector('#expOut audio') && F.document.querySelector('#expOut').textContent.includes('Hotel_Lobby')", 90)
    page.js("const a = F.document.querySelector('#expOut audio'); a.muted = true; a.play()")
    check("pressing play on the rendered song brings on the band for its genre (the lobby band)",
          page.until("F.Band.theme === 'elevator' && F.document.querySelector('#bandCard .band-cap').textContent.startsWith('Now playing: Hotel Lobby')", 5), [page.js("F.Band.theme"), cap()])
    page.js("F.document.querySelector('#expOut audio').pause()")
    check("pausing it sends the band back to rehearsing", page.until("F.document.querySelector('#bandCard .band-cap').textContent.startsWith('Rehearsing')", 3), cap())

    # the bug hunter's findings (Sound Forge v010)
    sets = lambda c, g, sub: page.json((pick % json.dumps([["cat", c], ["genre", g], ["sub", sub]])).replace("} })()", "} return {bpm: +d.getElementById('bpm').value, "
        "drums: d.getElementById('drums').value, scale: d.getElementById('scale').value, chip: +d.getElementById('chip').value}; })()")) or {}
    got = {k: sets(*v) for k, v in {"swing": ("Jazz, Blues & Soul", "Jazz", "Swing"), "blues": ("Jazz, Blues & Soul", "Blues", "Delta Blues"),
           "bossa": ("Jazz, Blues & Soul", "Jazz", "Bossa Nova"), "rock": ("Rock & Metal", "Rock", "Classic Rock"),
           "breakcore": ("Electronic", "Breaks & Garage", "Breakcore"), "bigbeat": ("Electronic", "Breaks & Garage", "Big Beat"),
           "shooter": ("Video Game & Chiptune", "Game Moods", "Space Shooter"), "dungeon": ("Video Game & Chiptune", "Game Moods", "Dungeon")}.items()}
    check("jazz gets swing drums, not Soul & Funk's rock beat", got["swing"].get("drums") == "swing" and got["swing"].get("bpm", 0) >= 140, got["swing"])
    check("blues gets the blues scale", got["blues"].get("scale") == "blues" and got["blues"].get("drums") == "swing", got["blues"])
    check("Bossa Nova gets a Latin beat in a major key, not the video-game boss fight", got["bossa"].get("drums") == "latin"
          and got["bossa"].get("scale") == "major" and got["bossa"].get("bpm", 0) <= 130, got["bossa"])
    check("Classic Rock gets rock drums, not Metal's", got["rock"].get("drums") == "rock" and got["rock"].get("bpm", 0) <= 150, got["rock"])
    check("Breakcore gets breakbeats at 160 to 190 BPM, not UK Garage", got["breakcore"].get("drums") == "break" and 160 <= got["breakcore"].get("bpm", 0) <= 190, got["breakcore"])
    check("Big Beat gets breakbeats too", got["bigbeat"].get("drums") == "break", got["bigbeat"])
    check("video-game moods keep their chip sound, and Space Shooter its drums", got["dungeon"].get("chip") == 8 and got["shooter"].get("chip") == 8
          and got["shooter"].get("drums") != "none", [got["dungeon"], got["shooter"]])
    page.js("F.document.getElementById('setTxt').value = JSON.stringify({song: {bpm: 100, sections: [{name: 'Verse', tracks: ['drums', 'bass'], bars: [{chord: [57, 60, 64], bass: [[0, 45, 4]], drums: {k: [1,0,0,0,1,0,0,0,1,0,0,0,1,0,0,0]}}]}]}}); F.document.getElementById('loadSet').click()")
    page.js("(() => { const e = F.document.getElementById('key'); e.value = 'D'; e.dispatchEvent(new F.Event('change')); })()")
    check("a song loaded from text is kept when a setting changes", page.js("!!F.forge.song && F.forge.song.fromText") is True
          and "Kept the song from the text" in (page.js("F.document.getElementById('status').textContent") or ""))
    page.js("F.document.getElementById('gen').click()")
    check("New song replaces it", page.js("!!F.forge.song && !F.forge.song.fromText") is True)
    page.js("F.document.getElementById('ambOnly').click()")
    check("Ambience only with no layers on says to turn one on, and stays quiet", page.js("F.forge.engine.playing") is False
          and "at least one ambience layer" in (page.js("F.document.getElementById('status').textContent") or ""))
    page.js("F.document.getElementById('a_rain').click(); F.document.getElementById('ambOnly').click()")
    n_rain = page.js("F.forge.engine.amb.length")
    page.js("F.document.getElementById('a_ocean').click()"); time.sleep(0.3)
    check("turning on another layer while playing is heard right away", page.js("F.forge.engine.playing") is True and page.js("F.forge.engine.amb.length") > n_rain, [n_rain, page.js("F.forge.engine.amb.length")])
    page.js("F.document.getElementById('a_rain').click(); F.document.getElementById('a_ocean').click()"); time.sleep(0.3)
    check("turning the last layer off stops the ambience", page.js("F.forge.engine.playing") is False)
    themes = []
    page.js(pick % '[["cat", "Electronic"], ["genre", "House"], ["sub", "Deep House"], ["evolve", "3"], ["evEvery", "1"]]')
    page.js("F.document.getElementById('lfGo').click()"); time.sleep(0.5)
    themes.append(page.js("F.Band.theme"))
    page.js("(() => { F.document.getElementById('cat').value = 'Jazz, Blues & Soul'; F.fillGenre(); F.forge.engine.loops = 1; F.onLoop(); })()"); time.sleep(0.5)
    themes.append(page.js("F.Band.theme"))
    check("Drift (new songs, new sub-genre) tells the band, which changes outfit with the genre", themes[0] == "club" and themes[1] == "jazz", themes)
    page.js("F.document.getElementById('stop').click()")
    page.js("(() => { const d = F.document; d.getElementById('sfxRndType').value = 'laser'; d.getElementById('sfxRnd').click(); d.getElementById('sfxBank').click(); })()")
    check("a random sound effect's pad says Random, not the preset's name", "Random laser" in (page.js("F.document.getElementById('pads').textContent") or ""),
          page.js("F.document.getElementById('pads').textContent"))
    page.js("F.document.getElementById('sfxMut').click(); F.document.getElementById('sfxExp').click()")
    check("a mutated one saves as mutated", page.until("(F.document.querySelector('#sfxOut') || {}).textContent.includes('Random_laser_mutated')", 10),
          page.js("F.document.querySelector('#sfxOut').textContent"))

    # the idea finder's three (Sound Forge v011): a saved-songs shelf, MIDI and stems, lyrics sung over the song
    page.js(pick % '[["cat", "Electronic"], ["genre", "House"], ["sub", "Deep House"], ["form", "short"], ["evolve", "1"]]')
    page.js("F.document.getElementById('gen').click()")
    # the shelf: kept inside the page itself (inside Randis UDS, the tab saves that page as its next version)
    page.js("""window.__shelfSaves = []; addEventListener('message', e => { if (e.data && e.data.uds === 'save-file') {
      __shelfSaves.push(e.data.text); e.source.postMessage({uds: 'saved', note: 'Saved in this tab, as version 12.'}, '*'); } });""")
    rows = lambda: page.json("[...F.document.querySelectorAll('#shelfList .shelf-row')].map(r => r.textContent)") or []
    check("the shelf starts empty and says how to keep a song", "No saved songs yet" in (page.js("F.document.getElementById('shelfList').textContent") or ""))
    seed_kept = page.js("F.document.getElementById('seed').value")
    page.js("F.document.getElementById('shelfName').value = 'My Keeper'; F.document.getElementById('shelfKeep').click()")
    check("Keep this song puts it on the shelf with its genre and tempo", page.until("F.document.querySelectorAll('#shelfList .shelf-row').length === 1", 3)
          and "My Keeper · Deep House" in rows()[0], rows())
    saved_page = page.js("__shelfSaves[__shelfSaves.length - 1] || ''") or ""
    check("inside an app, the shelf is saved into the page itself and the app says where",
          '"name":"My Keeper"' in saved_page and saved_page.startswith("<!doctype html>") and "const PAGE_SRC" in saved_page
          and saved_page.count('id="forge-shelf"') == 1 and "Saved songs kept" in (page.js("F.document.getElementById('status').textContent") or ""), saved_page[:200])
    page.js("(() => { const d = F.document; d.getElementById('seed').value = 77; d.getElementById('seed').dispatchEvent(new F.Event('change')); "
            "d.getElementById('shelfName').value = 'Second Song'; d.getElementById('shelfKeep').click(); })()")
    page.until("F.document.querySelectorAll('#shelfList .shelf-row').length === 2", 3)
    check("the newest kept song comes first", rows()[0].startswith("☆Second Song"), rows())
    page.js("[...F.document.querySelectorAll('#shelfList .shelf-row')].find(r => r.textContent.includes('My Keeper')).querySelector('[data-act=fav]').click()")
    check("a ⭐ favourite moves to the top", page.until("F.document.querySelector('#shelfList .shelf-row').textContent.startsWith('⭐My Keeper')", 3), rows())
    page.js("[...F.document.querySelectorAll('#shelfList .shelf-row')].find(r => r.textContent.includes('My Keeper')).querySelector('[data-act=load]').click()")
    check("▶ Load brings the song back exactly: its settings and seed", page.js("F.document.getElementById('seed').value") == seed_kept
          and "Loaded \"My Keeper\"" in (page.js("F.document.getElementById('status').textContent") or ""), page.js("F.document.getElementById('seed').value"))
    page.js("[...F.document.querySelectorAll('#shelfList .shelf-row')].find(r => r.textContent.includes('Second Song')).querySelector('[data-act=del]').click()")
    check("✕ takes a song off the shelf", rows() and len(rows()) == 1 and "My Keeper" in rows()[0], rows())
    shelf_page = page.js("__shelfSaves[__shelfSaves.length - 1] || ''") or ""
    base_saved = harness.serve(lambda pth: (shelf_page, "text/html; charset=utf-8") if pth == "/kept.html" else None)
    page.go(base_saved + "frame.html?/kept.html", ready="!!window.F && !!F.document && !!F.document.getElementById('shelfList') && F.document.readyState === 'complete'")
    time.sleep(1)
    check("the saved page opens with its shelf in it, favourite and all",
          "⭐My Keeper" in (page.js("F.document.getElementById('shelfList').textContent") or "")
          and "Second Song" not in (page.js("F.document.getElementById('shelfList').textContent") or ""), page.js("F.document.getElementById('shelfList').textContent"))
    page.go(base + "rig.html?apps/randis-sound-forge", ready="!!window.F && !!F.document.getElementById('expSong')")
    time.sleep(1.5)
    page.js(pick % '[["cat", "Electronic"], ["genre", "House"], ["sub", "Deep House"], ["form", "short"]]')
    page.js("F.document.getElementById('gen').click()")
    # lyrics: a synth singer on the melody; the band's singer mouths along, and gives the mouth back on Stop
    page.js("(() => { const d = F.document; d.getElementById('lyText').value = 'hello there my friend\\nsing along with me'; d.getElementById('lyOn').click(); })()")
    plan = page.json("F.voxPlan(F.forge.song).map(b => b ? b.map(x => x.syl).join('-') : null)") or []
    check("lyrics are split into syllables and laid on the verses and choruses, lines taking turns",
          "hel-lo-the-re-my-friend" in plan and "sing-a-long-with-me" in plan, [x for x in plan if x][:4])
    page.js("F.document.getElementById('play').click()")
    opened = page.until("F.Band.voice !== null", 15)
    check("while it plays, the band's singer opens their mouth on each sung syllable", opened, page.js("F.Band.voice"))
    page.js("F.document.getElementById('stop').click()")
    check("Stop gives the singer's mouth back to the beat", page.until("F.Band.voice === null", 3))
    # MIDI: a real Standard MIDI File, with the lyrics in it
    page.js("window.__b64 = null; F.forge.midi().arrayBuffer().then(b => { let s = ''; new Uint8Array(b).forEach(x => s += String.fromCharCode(x)); window.__b64 = btoa(s); })")
    page.until("!!window.__b64", 5)
    mid = base64.b64decode(page.js("window.__b64") or "")
    tracks = mid.count(b"MTrk")
    check("the MIDI file is a real one: a header, a tempo, a track per part", mid[:4] == b"MThd" and mid[8:10] == b"\x00\x01"
          and int.from_bytes(mid[10:12], "big") == tracks and tracks >= 5 and b"\xff\x51\x03" in mid
          and all(n.encode() in mid for n in ("Drums", "Bass", "Lead melody", "Vocals")), [mid[:14], tracks])
    check("the sung words are in it as lyric events", b"\xff\x05\x03hel" in mid and b"\xff\x05\x02me" in mid, mid.count(b"\xff\x05"))
    page.js("F.document.getElementById('expMidi').click()")
    check("🎼 MIDI file offers it to save", page.until("F.document.getElementById('stemOut').textContent.includes('.mid')", 3))
    # stems: one WAV per part, the same length, the vocals among them, and all of it as one zip
    page.js("setTimeout(() => F.document.getElementById('expStems').click(), 0)")
    ready = page.until("!!F.document.getElementById('stemZip')", 180)
    names = page.json("[...F.document.querySelectorAll('#stemOut .row span:not(.muted)')].map(s => s.textContent.split(' · ')[0])") or []
    check("🎚 Stems renders a WAV per part playing, plus the vocals and the MIDI file",
          ready and any(n.endswith(".mid") for n in names) and any(n.endswith("_drums.wav") for n in names)
          and any(n.endswith("_bass.wav") for n in names) and any(n.endswith("_vocals.wav") for n in names), names)
    page.js("""window.__stems = null; (async () => { const out = [], c = new F.OfflineAudioContext(2, 44100, 44100);
      for (const b of [...F.document.querySelectorAll('#stemOut .row')]) { const n = (b.querySelector('span:not(.muted)') || {}).textContent || ''; if (!n.includes('.wav')) continue;
        b.querySelector('button').click(); await new Promise(r => setTimeout(r, 300)); }
      window.__stems = out; })()""")
    page.until("got.filter(g => g.name && g.name.endsWith('.wav')).length >= 3", 20)
    wavs = page.json("got.filter(g => g.name && g.name.endsWith('.wav'))") or []
    check("every stem saves as a real WAV, all the same length, so they line up in another app",
          len(wavs) >= 3 and all(w["head"] == "RIFF" for w in wavs) and len({w["size"] for w in wavs}) == 1, wavs)
    page.js("F.document.getElementById('stemZip').click()")
    page.until("got.some(g => g.name && g.name.endsWith('_stems.zip'))", 20)
    z = (page.json("got.filter(g => g.name && g.name.endsWith('_stems.zip'))") or [{}])[0]
    check("Save all as one .zip hands over a zip", z.get("head") == "PK\x03\x04" and z.get("size", 0) > sum(w["size"] for w in wavs), z)
    page.js("window.__z = null; F.forge.zip([{name: 'song.mid', blob: F.forge.midi()}, {name: 'note.txt', blob: new Blob(['hi'])}]).then(b => b.arrayBuffer()).then(b => { let s = ''; new Uint8Array(b).forEach(x => s += String.fromCharCode(x)); window.__z = btoa(s); })")
    page.until("!!window.__z", 5)
    import zipfile
    zf = zipfile.ZipFile(io.BytesIO(base64.b64decode(page.js("window.__z") or "")))
    check("the zip opens in any zip tool, every file whole", zf.testzip() is None and zf.namelist() == ["song.mid", "note.txt"]
          and zf.read("note.txt") == b"hi" and zf.read("song.mid") == mid, zf.namelist())
    vocal_peak = page.js("""(() => { window.__peak = null; const row = [...F.document.querySelectorAll('#stemOut .row')].find(r => r.textContent.includes('_vocals.wav'));
      return 1; })()""")
    page.js("""window.__peak = null; F.forge.vocals && 0; (async () => { const ctx = new F.OfflineAudioContext(2, 44100, 44100);
      const buf = await F.renderPart(F.forge.song, 'vocals'); let m = 0; const d = buf.getChannelData(0); for (let i = 0; i < d.length; i += 7) m = Math.max(m, Math.abs(d[i])); window.__peak = m; })()""")
    page.until("window.__peak !== null", 60)
    check("the vocals stem really has singing in it", (page.js("window.__peak") or 0) > 0.02, page.js("window.__peak"))

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
    terms = page.js("document.querySelector('.terms').textContent") or ""
    check("the terms say royalty free, paid work included, no payment, and credit required",
          all(w in terms for w in ("Royalty free, with credit", "paid work", "No payment", "must credit")) and "never required" not in terms, terms)
    check("each song shows the exact credit to give, the same as inside its MP3",
          page.js("document.querySelector('#song-lobby-test .credit-line').textContent") == 'Music: "Lobby Test" by Randy Moore, from the Randis Shop (randywilliammoore.github.io/randis-shop)')
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
    beat = """(() => { const c = new AudioContext(), sr = c.sampleRate, n = sr * 6, buf = c.createBuffer(1, n, sr), d = buf.getChannelData(0);
      for (let i = 0; i < n; i++) d[i] = 0.05 * Math.sin(2 * Math.PI * 220 * i / sr) + 0.02 * (Math.random() * 2 - 1);   // a pad and hiss
      for (let t = 0.3; t < 6; t += 60 / %(bpm)s) for (let i = 0; i < sr * 0.15; i++) {                             // the beats
        const k = Math.floor(t * sr) + i, e = Math.exp(-i / sr * 25);
        if (k < n) d[k] += %(bass)s ? 0.8 * e * Math.sin(2 * Math.PI * (50 + 80 * e) * i / sr) : 0.5 * e * Math.sin(2 * Math.PI * 880 * i / sr);
      }
      const s = c.createBufferSource(), an = c.createAnalyser(), hush = c.createGain(); an.fftSize = 2048; hush.gain.value = 0;
      s.buffer = buf; s.connect(an); an.connect(hush); hush.connect(c.destination); s.start();
      Band.play(an, %(genre)s, 'test beat'); window.__testBeat = an; })()"""
    for bpm, bass, genre in ((120, "true", "'Deep House'"), (90, "true", "'Boom Bap'"), (100, "false", "'Elevator Music'")):
        page.js(beat % {"bpm": bpm, "bass": bass, "genre": genre}); time.sleep(5)
        ok, gaps = on_time(page.json("Band.beats") or [], bpm)
        check(f"the band bounces on the beat at {bpm} BPM" + ("" if bass == "true" else ", even with no bass (a piano)"), ok, gaps)
        page.js("Band.stop(window.__testBeat)")
    picks = page.json("['UK Garage', 'Breakcore', 'Cyberpunk', 'Dancehall', 'Garage Rock'].map(g => Band.themeFor(g).id)")
    check("garage and breaks get the club band, cyberpunk the neon band, dancehall the beach band",
          picks == ["club", "club", "synth", "tropic", "rock"], picks)
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
