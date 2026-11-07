"""Puts a song made with Randis Sound Forge in the Jukebox, royalty free, then rebuilds the lists.
    python tools/add_music.py "C:/path/My Song.wav" --name "My Song" --genre "Elevator Music" --blurb "Soft piano for a hotel lobby." [--cover art.png] [--by Randy]

Every song in the Jukebox is the same kind of file: a 192 kbps MP3 with its title, artist, album, genre, year, description, the
royalty-free note and its cover art inside it, so it carries them wherever it's downloaded to. The cover is the Raisin Band
dressed for the song's genre, with the song's name on it, unless --cover gives a picture. It goes in music/<slug>/ as song.mp3,
cover.jpg and info.json; nothing else changes. Needs ffmpeg, and pywebview for the band's cover. Push it to put it on the live shop."""
import argparse, base64, datetime, json, os, re, shutil, subprocess, sys, tempfile, time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KINDS = (".wav", ".mp3", ".ogg", ".flac")
SHOP = "https://randywilliammoore.github.io/randis-shop/#/music"
ALBUM = "Randis Shop Jukebox"
SHOP_PAGE = "randywilliammoore.github.io/randis-shop"


def credit_for(title, artist):
    """The credit everyone who uses the song must give; the Jukebox shows the same words."""
    return f'Music: "{title}" by {artist}, from the Randis Shop ({SHOP_PAGE})'


def terms_for(title, artist):
    return (f"Royalty free, with credit required. Use it in anything, paid work included, no payment needed, but credit it wherever "
            f"you use it: {credit_for(title, artist)}. Don't sell or hand out the song itself as your own music. Terms: {SHOP}")
ARTISTS = {"Randy": "Randy Moore"}


def stop(why):
    sys.exit("add_music: " + why)


def ffmpeg(name="ffmpeg"):
    """ffmpeg on the PATH, or where winget puts its link (a shell opened before the install doesn't have it on the PATH yet)."""
    found = shutil.which(name)
    link = os.path.join(os.environ.get("LOCALAPPDATA", ""), "Microsoft", "WinGet", "Links", name + ".exe")
    return found or (link if os.path.isfile(link) else None)


def band_cover(genre, title, by, out):
    """The Raisin Band's cover, drawn by the shop's own site/band.js in a browser window placed off screen."""
    import webview
    band = open(os.path.join(ROOT, "site", "band.js"), encoding="utf-8").read()
    w = webview.create_window("cover", html="<!doctype html><meta charset='utf-8'><body><script>" + band + "</script></body>",
                              x=-3000, y=-3000, width=320, height=240)
    got = {}

    def draw():
        try:
            for _ in range(100):
                if w.evaluate_js("!!window.Band"):
                    break
                time.sleep(0.1)
            got["jpg"] = w.evaluate_js(f"Band.cover({json.dumps(genre)}, {json.dumps(title)}, {json.dumps(by)})")
        finally:
            w.destroy()
    webview.start(draw)
    if not (got.get("jpg") or "").startswith("data:image/jpeg;base64,"):
        stop("the band's cover couldn't be drawn")
    with open(out, "wb") as f:
        f.write(base64.b64decode(got["jpg"].split(",", 1)[1]))


def length_of(path):
    r = subprocess.run([ffmpeg("ffprobe"), "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path], capture_output=True, text=True)
    try:
        secs = round(float(r.stdout.strip()))
    except ValueError:
        stop("that song file couldn't be read")
    return f"{secs // 60}:{secs % 60:02d}"


def main():
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("file")
    p.add_argument("--name", required=True, help="the song's title")
    p.add_argument("--genre", required=True)
    p.add_argument("--blurb", required=True, help="a line or two about the song; it's the description in the file too")
    p.add_argument("--cover", help="a picture for the cover instead of the band (.png or .jpg)")
    p.add_argument("--by", default="Randy")
    a = p.parse_args()
    if not a.blurb.strip() or len(a.blurb) > 400:
        stop("--blurb must be a line or two, at most 400 characters")
    if os.path.splitext(a.file)[1].lower() not in KINDS:
        stop("the song must be a .wav, .mp3, .ogg or .flac file")
    if a.cover and os.path.splitext(a.cover)[1].lower() not in (".png", ".jpg", ".jpeg"):
        stop("--cover must be a .png or .jpg picture")
    if not ffmpeg() or not ffmpeg("ffprobe"):
        stop("needs ffmpeg (winget install Gyan.FFmpeg.Essentials)")
    slug = re.sub(r"[^a-z0-9]+", "-", a.name.lower()).strip("-")
    folder = os.path.join(ROOT, "music", slug)
    if not slug or os.path.exists(folder):
        stop(f"there's already a song at music/{slug}; pick another name")
    today = datetime.date.today()
    info = {"name": a.name, "by": a.by, "blurb": a.blurb.strip(), "genre": a.genre, "length": length_of(a.file), "added": today.isoformat()}
    work = tempfile.mkdtemp(prefix="add_music_")
    try:
        cover = os.path.join(work, "cover.jpg")
        if a.cover:     # any picture becomes a 1000 x 1000 JPEG, cropped to the middle
            r = subprocess.run([ffmpeg(), "-v", "error", "-i", a.cover, "-vf", "scale=1000:1000:force_original_aspect_ratio=increase,crop=1000:1000",
                                "-frames:v", "1", "-q:v", "3", cover])
            if r.returncode:
                stop("that cover picture couldn't be read")
        else:
            band_cover(a.genre, a.name, ARTISTS.get(a.by, a.by), cover)
        artist = ARTISTS.get(a.by, a.by)
        tags = {"title": a.name, "artist": artist, "album_artist": artist, "album": ALBUM, "genre": a.genre, "date": str(today.year),
                "comment": a.blurb.strip(), "copyright": terms_for(a.name, artist), "publisher": "The Randis Shop",
                "Attribution": credit_for(a.name, artist)}
        song = os.path.join(work, "song.mp3")
        audio = ["-c:a", "copy"] if a.file.lower().endswith(".mp3") else ["-c:a", "libmp3lame", "-b:a", "192k"]
        cmd = [ffmpeg(), "-v", "error", "-i", a.file, "-i", cover, "-map", "0:a:0", "-map", "1:v:0", *audio, "-c:v", "copy",
               "-map_metadata", "-1", "-id3v2_version", "3", "-metadata:s:v", "title=Album cover", "-metadata:s:v", "comment=Cover (front)"]
        for k, v in tags.items():
            cmd += ["-metadata", f"{k}={v}"]
        if subprocess.run(cmd + [song]).returncode:
            stop("ffmpeg couldn't make the MP3")
        if os.path.getsize(song) > 95 * 1024 * 1024:
            stop("the MP3 is over 95 MB; GitHub won't take it")
        os.makedirs(folder)
        shutil.copyfile(song, os.path.join(folder, "song.mp3"))
        shutil.copyfile(cover, os.path.join(folder, "cover.jpg"))
        with open(os.path.join(folder, "info.json"), "w", encoding="utf-8", newline="\n") as f:
            json.dump(info, f, indent=1, ensure_ascii=False)
            f.write("\n")
    finally:
        shutil.rmtree(work, ignore_errors=True)
    r = subprocess.run([sys.executable, os.path.join(ROOT, "tools", "build_index.py")])
    if r.returncode:
        shutil.rmtree(folder)
        stop("the song was taken back out")
    print(f"Added music/{slug}")


if __name__ == "__main__":
    main()
