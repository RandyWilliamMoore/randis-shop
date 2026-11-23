"""One command from "I changed the shop" to "it's live on GitHub", stopping on the first thing that's wrong.

  python tools/publish.py "what changed"            dry run: build, test, show what would be committed (nothing is pushed)
  python tools/publish.py "what changed" --push     same, then commit, push and check GitHub has the new commit
  options:  --quick         only the fast tests (link, share, security)
            --no-build      skip build_index.py (it also writes the share pages)
            --add PATH      also commit this untracked file or folder (repeatable); other untracked files stay out
            --only SLUG     run the item tests for just these items (repeatable)

Steps: 1 build_index.py  2 every test in tests/ (an item that fails is run again once on its own, since a cold browser
sometimes misses the first check; it only passes if the rerun is clean)  3 stage tracked changes (+ --add)  4 commit
5 push  6 git ls-remote must show the same commit as HEAD. Any step that fails stops the run with exit 1.
"""
import os, re, subprocess, sys

SHOP = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TESTS = ["link_test", "share_test", "security_test", "ship_test", "play_test", "music_test", "save_test", "pdf_maker_test", "office_ai_test"]
QUICK = ["link_test", "share_test", "security_test"]
PER_ITEM = {"ship_test", "play_test"}


def sh(cmd, check=True):
    env = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUTF8="1")
    r = subprocess.run(cmd, cwd=SHOP, capture_output=True, text=True, encoding="utf-8", errors="replace", env=env)
    if check and r.returncode != 0:
        stop(f"{' '.join(cmd)} failed:\n{r.stdout[-1500:]}{r.stderr[-1500:]}")
    return r


def stop(msg):
    print(f"STOP: {msg}", flush=True)
    sys.exit(1)


def failed_names(out):
    return {m.group(1) for m in re.finditer(r"^FAIL (.+?): ", out, re.M)}


def slugs_for(names):
    sys.path.insert(0, os.path.join(SHOP, "tests"))
    import harness
    by_name = {i["name"]: i["slug"] for i in harness.items()}
    return [by_name[n] for n in names if n in by_name], [n for n in names if n not in by_name]


def run_test(name, only):
    args = [sys.executable, os.path.join("tests", name + ".py")] + (only if name in PER_ITEM else [])
    r = sh(args, check=False)
    out = r.stdout + r.stderr
    total = re.findall(r"^(\d+)/(\d+) passed", out, re.M)
    ok = r.returncode == 0 and bool(total) and total[-1][0] == total[-1][1]
    if ok:
        return True, f"{total[-1][0]}/{total[-1][1]} passed"
    if name in PER_ITEM and failed_names(out):
        slugs, unknown = slugs_for(failed_names(out))
        if unknown or not slugs:
            return False, "failed: " + ", ".join(sorted(failed_names(out)))
        again = sh([sys.executable, os.path.join("tests", name + ".py")] + slugs, check=False)
        t2 = re.findall(r"^(\d+)/(\d+) passed", again.stdout, re.M)
        if again.returncode == 0 and t2 and t2[-1][0] == t2[-1][1]:
            return True, f"failed once on {', '.join(slugs)}, clean on rerun ({t2[-1][0]}/{t2[-1][1]})"
        return False, "failed twice: " + ", ".join(sorted(failed_names(again.stdout))) + "\n" + again.stdout[-1500:]
    return False, "failed:\n" + out[-1500:]


def main():
    a = sys.argv[1:]
    if not a or a[0].startswith("--"):
        print(__doc__)
        sys.exit(2)
    msg, flags = a[0], a[1:]
    push, quick, build = "--push" in flags, "--quick" in flags, "--no-build" not in flags
    adds = [flags[i + 1] for i, f in enumerate(flags) if f == "--add" and i + 1 < len(flags)]
    only = [flags[i + 1] for i, f in enumerate(flags) if f == "--only" and i + 1 < len(flags)]

    if sh(["git", "rev-parse", "--abbrev-ref", "HEAD"]).stdout.strip() != "main":
        stop("not on main")
    if build:
        print("1 build_index.py ...", flush=True)
        sh([sys.executable, os.path.join("tools", "build_index.py")])
    for t in (QUICK if quick else TESTS):
        print(f"2 {t} ...", end=" ", flush=True)
        ok, note = run_test(t, only)
        print(note, flush=True)
        if not ok:
            stop(f"{t} {note}")

    sh(["git", "add", "-u"])
    for p in adds:
        sh(["git", "add", "--", p])
    staged = sh(["git", "diff", "--cached", "--name-only"]).stdout.split()
    left = [l[3:] for l in sh(["git", "status", "--porcelain"]).stdout.splitlines() if l.startswith("??")]
    print(f"3 staged {len(staged)} files" + (f"; left out (untracked): {', '.join(left)}" if left else ""), flush=True)
    if not staged:
        stop("nothing to commit")
    added = "\n".join(l for l in sh(["git", "diff", "--cached", "-U0", "--", "*.html", "*.js", "*.css", "*.json", "*.md"]).stdout.splitlines()
                      if l.startswith("+") and not l.startswith("+++"))
    dangling = [p for p in left if not p.endswith("/") and p in added]
    dangling += [p for p in left if p.endswith("/") and p.rstrip("/") + "/" in added]
    if dangling:
        sh(["git", "reset", "-q"])
        stop("staged changes point at files left out: " + ", ".join(dangling) + " (add them with --add, or leave the file that points at them out with git restore/stash)")
    if not push:
        sh(["git", "reset", "-q"])
        print("dry run: nothing committed or pushed. Add --push to publish.")
        return
    sh(["git", "commit", "-q", "-m", msg])
    sh(["git", "push", "-q", "origin", "main"])
    head = sh(["git", "rev-parse", "HEAD"]).stdout.strip()
    remote = sh(["git", "ls-remote", "origin", "refs/heads/main"]).stdout.split()[:1]
    if remote != [head]:
        stop(f"GitHub shows {remote} but HEAD is {head}")
    print(f"6 live: GitHub main = {head[:7]}")


if __name__ == "__main__":
    main()
