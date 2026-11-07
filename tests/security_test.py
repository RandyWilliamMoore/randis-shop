"""The wall around games: a hostile test game runs in the real shop page and real player, and tries to get out.
It tries WebRTC (in its own page and in frames it makes), fetching from the internet, and sending its frame to another page:
first one of the shop's raw item files (outside the player's rules), then a stand-in internet server. Then every real item
still has to open in the player.
    python tests/security_test.py"""
import http.server, json, threading, time

import harness

hits = {"shop": [], "internet": []}


class Internet(http.server.BaseHTTPRequestHandler):
    """Stands in for any server on the internet and records every request that reaches it."""
    def do_GET(self):
        hits["internet"].append(self.path)
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        self.wfile.write(b"<p>outside page</p>")

    def log_message(self, *a):
        pass


inet = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Internet)
threading.Thread(target=inet.serve_forever, daemon=True).start()
INET = f"http://127.0.0.1:{inet.server_port}"

HOSTILE = """<!doctype html><html><head><meta charset="utf-8"><title>probe</title></head><body><script>
const R = {};
const say = () => parent.postMessage({probe: R}, "*");
const rtcNames = n => Object.getOwnPropertyNames(n).filter(k => /^(webkit)?RTC/.test(k) && n[k]);
R.rtc_here = rtcNames(window).join(",") || "none";
try { new RTCPeerConnection({iceServers: [{urls: "stun:127.0.0.1:%PORT%"}]}); R.rtc_new = "made"; } catch (e) { R.rtc_new = "blocked"; }
try { const f = document.createElement("iframe"); document.body.append(f); const w = window[0];
  R.blank_frame = w ? (rtcNames(w).join(",") || "none") : "no frame";
  try { new w.RTCPeerConnection(); R.blank_new = "made"; } catch (e) { R.blank_new = "blocked"; } } catch (e) { R.blank_frame = "error " + e; }
try { const f = document.createElement("iframe"); f.srcdoc = "<p>x</p>"; document.body.append(f);
  R.srcdoc_frame = window[1] ? (rtcNames(window[1]).join(",") || "none") : "no frame"; } catch (e) { R.srcdoc_frame = "error " + e; }
fetch("%INET%/fetch").then(() => R.fetch = "reached", () => R.fetch = "blocked").finally(() => {
  say(); setInterval(say, 250);
  setTimeout(() => { location.href = "%NAV%"; }, 4000);
});
</script></body></html>"""
PROBE = {"kind": "games", "slug": "probe", "name": "Probe", "by": "test", "blurb": "x", "status": "ok",
         "reviews": {"randy": None, "maker": None}, "file": "games/probe/item.html"}
WATCH = "window.__probe = null; addEventListener('message', e => { if (e.data && e.data.probe) window.__probe = e.data.probe; });"


def test(page, check):
    for label, key, nav in (("one of the shop's raw item files", "shop", "/games/coin-flipper/item.html?escaped"),
                            ("the internet", "internet", INET + "/escaped")):
        seen = []

        def extra(path, nav=nav, seen=seen):
            seen.append(path)
            if path == "/games/probe/item.html":
                return HOSTILE.replace("%PORT%", str(inet.server_port)).replace("%INET%", INET).replace("%NAV%", nav), "text/html"
        base = harness.serve(extra, [PROBE])
        page.go(base + "index.html#/games/probe/play")
        page.until("!!document.querySelector('.play iframe')")
        page.js(WATCH)
        got = page.until("!!window.__probe", 15)
        probe = page.json("window.__probe") or {}
        time.sleep(5)    # the probe tries to leave after 4 s
        if key == "shop":
            check("the hostile game runs in the real player", got, probe)
            check("it has no WebRTC", probe.get("rtc_here") == "none", probe.get("rtc_here"))
            check("it can't open a WebRTC connection", probe.get("rtc_new") == "blocked", probe.get("rtc_new"))
            check("an empty frame it makes has no WebRTC either", probe.get("blank_frame") in ("none", "no frame") and probe.get("blank_new") != "made", probe)
            check("a srcdoc frame it makes has no WebRTC either", probe.get("srcdoc_frame") in ("none", "no frame"), probe.get("srcdoc_frame"))
            check("it can't fetch from the internet", probe.get("fetch") == "blocked", probe.get("fetch"))
            reached = [p for p in seen if p == "/games/coin-flipper/item.html"]
        else:
            reached = [p for p in hits["internet"] if p == "/escaped"]
        check(f"it can't send its frame to {label}", not reached, reached)
        check("the shop page is still there", page.js("location.hash") == "#/games/probe/play")
    check("nothing reached the stand-in internet", not hits["internet"], hits["internet"])

    base = harness.serve()
    for it in [i for i in harness.items() if i.get("status") != "flagged"]:
        page.go(base + f"index.html#/{it['kind']}/{it['slug']}/play")
        ok = page.until("!!document.querySelector('.play iframe')", 10)
        time.sleep(2.5)
        note = page.js("(document.querySelector('.walled span') || {}).textContent || ''") or ""
        check(f"{it['name']}: still opens in the player", ok and "wouldn't load" not in note, note)


harness.run(test)
