"""Shared parts of the shop's tests: a local copy of the shop on a test server, and a real browser window to drive it.

The window is a real Chromium one (Edge WebView2, through pywebview), placed off screen rather than hidden,
because a hidden window stops animations and game loops."""
import http.server, json, os, re, sys, threading, time

import webview

SHOP = os.environ.get("SHOP_DIR") or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # SHOP_DIR: test another copy, say an older one
LIVE_PLAYER = "https://randywilliammoore.github.io/randis-shop/site/player.html"
ETSY = "https://www.etsy.com/shop/UberRandis"

# Added to a game page when the test runs it directly: it records errors and blocked loads, answers its prompts,
# keeps file pickers and downloads from opening, and blocks storage the way the player's sandbox does.
HOOK = """<script>window.__errs=[];window.__csp=[];
addEventListener('error',e=>__errs.push(String(e.message)+' @'+e.lineno));
addEventListener('unhandledrejection',e=>__errs.push('rejected: '+String(e.reason)));
document.addEventListener('securitypolicyviolation',e=>__csp.push(e.violatedDirective+' '+e.blockedURI));
window.confirm=()=>true;window.alert=()=>{};window.prompt=()=>'';
window.__saves=[];const __pick=HTMLInputElement.prototype.click,__press=HTMLAnchorElement.prototype.click;
HTMLInputElement.prototype.click=function(){if(this.type!=='file')return __pick.call(this)};
HTMLAnchorElement.prototype.click=function(){if(this.hasAttribute('download')){__saves.push(this.download);return}return __press.call(this)};
document.addEventListener('click',e=>{const a=e.target.closest&&e.target.closest('a[download]');if(a){e.preventDefault();__saves.push(a.download)}},true);
Object.defineProperty(window,'localStorage',{get(){throw new DOMException('blocked','SecurityError')}});</script>"""


def items():
    text = open(os.path.join(SHOP, "items.js"), encoding="utf-8").read()
    return json.loads(re.search(r"window\.ITEMS = (\[.*\]);", text, re.S).group(1))


def player_rules():
    text = open(os.path.join(SHOP, "site", "player.html"), encoding="utf-8").read()
    return re.search(r'Content-Security-Policy" content="([^"]+)"', text).group(1)


class Results:
    def __init__(self):
        self.n, self.failed = 0, []

    def check(self, name, ok, detail=""):
        self.n += 1
        if not ok:
            self.failed.append(name)
        print(("PASS " if ok else "FAIL ") + name + ("" if ok or detail == "" else f"  [{str(detail)[:400]}]"), flush=True)
        return ok

    def finish(self):
        print(f"\n{self.n - len(self.failed)}/{self.n} passed", flush=True)
        return 1 if self.failed else 0


def serve(extra=None, extra_items=()):
    """Serves the shop folder. The shop page names the live player; here it's pointed at this server's copy.
    extra(path) can answer a path itself with (text, content type, headers); extra_items are added to items.js."""
    class Handler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *a, **k):
            super().__init__(*a, directory=SHOP, **k)

        def log_message(self, *a):
            pass

        def send_text(self, text, ctype, headers=None):
            body = text.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", ctype)
            self.send_header("Cache-Control", "no-store")
            for k, v in (headers or {}).items():
                self.send_header(k, v)
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            path = self.path.split("?")[0]
            here = f"http://127.0.0.1:{self.server.server_port}"
            if path in ("/", "/index.html"):
                page = open(os.path.join(SHOP, "index.html"), encoding="utf-8").read()
                return self.send_text(page.replace(LIVE_PLAYER, here + "/site/player.html"), "text/html")
            if path == "/items.js" and extra_items:
                js = open(os.path.join(SHOP, "items.js"), encoding="utf-8").read()
                js += "".join(f";window.ITEMS.push({json.dumps(i)});\n" for i in extra_items)
                return self.send_text(js, "application/javascript")
            if path.startswith("/walled/"):    # an item run directly, under the player's own rules, so the test can reach in
                kind, slug = path.split("/")[2:4]
                page = open(os.path.join(SHOP, kind, slug, "item.html"), encoding="utf-8").read()
                i = page.lower().find("<head>")
                page = page[:i + 6] + HOOK + page[i + 6:] if i >= 0 else HOOK + page
                return self.send_text(page, "text/html; charset=utf-8", {"Content-Security-Policy": player_rules()})
            if path == "/frame.html":           # holds one page in a frame the test can reach: frame.html?<address>
                return self.send_text('<!doctype html><body style="margin:0"><iframe id=f style="width:1180px;height:780px;border:0">'
                                      '</iframe><script>var F;f.onload=()=>{F=f.contentWindow};f.src=location.search.slice(1)</script>', "text/html")
            if path == "/rig.html":             # the real player script, without the sandbox, holding one item: rig.html?<kind>/<slug>
                return self.send_text("""<!doctype html><body><iframe id=f src="/site/player.html" style="width:1100px;height:700px"></iframe><script>
window.got = []; var F;
addEventListener('message', e => {
  if (e.data === 'player-ready') { F = f.contentWindow; fetch('/' + location.search.slice(1) + '/item.html').then(r => r.text()).then(t => F.postMessage(t, '*')); }
  else if (e.data && e.data.uds === 'open-link') got.push({link: e.data.url});
  else if (e.data && e.data.uds === 'download') { const u = new Uint8Array(e.data.data); got.push({name: e.data.name, size: u.length, head: String.fromCharCode(...u.slice(0, 4))}); }
});</script>""", "text/html")
            if extra:
                answer = extra(path)
                if answer:
                    return self.send_text(*answer)
            return super().do_GET()

    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return f"http://127.0.0.1:{server.server_port}/"


class Page:
    """The test's handle on the window. Every call has a time limit: a call that starts a page load may never return."""
    def __init__(self, window):
        self.w = window

    def js(self, code, secs=10):
        out = [None, None]

        def call():
            try:
                out[0] = self.w.evaluate_js(code)
            except Exception as e:
                out[1] = e
        t = threading.Thread(target=call, daemon=True)
        t.start()
        t.join(secs)
        if t.is_alive() or out[1]:
            return None
        return out[0]

    def json(self, code, secs=10):
        text = self.js(f"JSON.stringify({code})", secs)
        return json.loads(text) if text else None

    def until(self, code, secs=10):
        end = time.time() + secs
        while time.time() < end:
            if self.js(code, 3):
                return True
            time.sleep(0.2)
        return False

    def go(self, url, ready="document.readyState === 'complete'"):
        """A full page load every time; setting only the #part wouldn't reload the shop."""
        self.js("location.href = 'about:blank'", 2)
        self.until("location.href === 'about:blank'", 5)
        self.js(f"location.href = {json.dumps(url)}", 2)
        self.until(f"location.href === {json.dumps(url)} && {ready}", 15)
        time.sleep(0.5)


def run(test):
    """Opens the window, runs test(page), closes it, exits 1 on any failure."""
    results = Results()
    window = webview.create_window("shop test", html="<p>.</p>", x=-3000, y=-3000, width=1200, height=820)

    def body():
        try:
            test(Page(window), results.check)
        except Exception as e:
            results.check("the test itself crashed", False, repr(e))
        finally:
            code = results.finish()
            window.destroy()
            os._exit(code)
    webview.start(body)
