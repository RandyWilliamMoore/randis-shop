"""Puts a song made with Randis Sound Forge in the Jukebox, royalty free, then rebuilds the lists.
    python tools/add_music.py "C:/path/My Song.wav" --name "My Song" --genre "Elevator Music" [--blurb "..."] [--by Randy]
The song is copied to music/<slug>/song.<wav|mp3|ogg>; nothing else changes. Push it to put it on the live shop."""
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


def main():
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("file")
    p.add_argument("--name", required=True)
    p.add_argument("--genre", required=True)
    p.add_argument("--blurb", default="")
    p.add_argument("--by", default="Randy")
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
