"""Puts a song made with Randis Sound Forge in the Jukebox, royalty free, then rebuilds the lists.
    python tools/add_music.py "C:/path/My Song.wav" --name "My Song" --genre "Elevator Music" [--blurb "..."] [--by Randy]
The song is copied to music/<slug>/; nothing else changes. A WAV is made into an MP3 (192 kbps, about a tenth the size) when
ffmpeg is on this computer; --keep-wav keeps the WAV as it is. Push it to put it on the live shop."""
import argparse, datetime, json, os, re, shutil, subprocess, sys, wave

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KINDS = (".wav", ".mp3", ".ogg")


def length_of(path):
    if path.lower().endswith(".wav"):
        try:
            with wave.open(path) as w:
                secs = round(w.getnframes() / w.getframerate())
            return f"{secs // 60}:{secs % 60:02d}"
        except (wave.Error, EOFError, ZeroDivisionError):
            sys.exit("add_music: that WAV file couldn't be read")
    return None


def ffmpeg():
    """ffmpeg on the PATH, or where winget puts its link (a shell opened before the install doesn't have it on the PATH yet)."""
    found = shutil.which("ffmpeg")
    link = os.path.join(os.environ.get("LOCALAPPDATA", ""), "Microsoft", "WinGet", "Links", "ffmpeg.exe")
    return found or (link if os.path.isfile(link) else None)


def main():
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("file")
    p.add_argument("--name", required=True)
    p.add_argument("--genre", required=True)
    p.add_argument("--blurb", default="")
    p.add_argument("--by", default="Randy")
    p.add_argument("--keep-wav", action="store_true", help="don't make a WAV into an MP3")
    a = p.parse_args()
    ext = os.path.splitext(a.file)[1].lower()
    if ext not in KINDS:
        sys.exit("add_music: the song must be a .wav, .mp3 or .ogg file")
    if os.path.getsize(a.file) > 95 * 1024 * 1024:
        sys.exit("add_music: the song is over 95 MB; GitHub won't take it")
    slug = re.sub(r"[^a-z0-9]+", "-", a.name.lower()).strip("-")
    folder = os.path.join(ROOT, "music", slug)
    if not slug or os.path.exists(folder):
        sys.exit(f"add_music: there's already a song at music/{slug}; pick another name")
    info = {"name": a.name, "by": a.by, "blurb": a.blurb, "genre": a.genre, "length": length_of(a.file),
            "added": datetime.date.today().isoformat()}
    os.makedirs(folder)
    tool = ffmpeg() if ext == ".wav" and not a.keep_wav else None
    if tool:
        r = subprocess.run([tool, "-hide_banner", "-loglevel", "error", "-i", a.file, "-codec:a", "libmp3lame", "-b:a", "192k",
                            "-map_metadata", "-1", os.path.join(folder, "song.mp3")])
        if r.returncode:
            shutil.rmtree(folder)
            sys.exit("add_music: ffmpeg couldn't make the MP3")
    else:
        if ext == ".wav" and not a.keep_wav:
            print("add_music: no ffmpeg here, so the song stays a WAV")
        shutil.copyfile(a.file, os.path.join(folder, "song" + ext))
    with open(os.path.join(folder, "info.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(info, f, indent=1, ensure_ascii=False)
        f.write("\n")
    r = subprocess.run([sys.executable, os.path.join(ROOT, "tools", "build_index.py")])
    if r.returncode:
        shutil.rmtree(folder)
        sys.exit("add_music: the song was taken back out")
    print(f"Added music/{slug}")


if __name__ == "__main__":
    main()
