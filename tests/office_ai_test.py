"""Randis Office's "Add office product" in the shop: the app asks its parent page, and the shop page asks Anthropic with the
person's own API key (site/office_ai.js). Nothing here reaches the internet: Anthropic is faked inside the page.
    python tests/office_ai_test.py"""
import json, time

import harness

PAGE = "<!doctype html><html><head><title>Tip Calc</title></head><body>tips</body></html>"
ANSWER = "Here it is.\n```html\n" + PAGE + "\n```"


def item_side(page, check, base):
    """The app itself, under the player's rules, held by a parent that answers like the shop does."""
    page.go(base + "frame.html?/walled/apps/randis-office")
    page.js("window.asks = []; addEventListener('message', e => { if (e.data && e.data.uds === 'office-ask') { asks.push(e.data);"
            " e.source.postMessage({uds: 'office', id: e.data.id, done: false, status: 'Building…', text: 'Here'}, '*');"
            f" setTimeout(() => e.source.postMessage({{uds: 'office', id: e.data.id, done: true, text: {json.dumps(ANSWER)}}}, '*'), 300); }} }});")
    found = page.until("F && F.document && [...F.document.querySelectorAll('button,[role=tab],.tab')].some(b => /Add office product/.test(b.textContent))", 15)
    if not check("the shop's Randis Office shows the Add office product tab", found):
        return
    page.js("[...F.document.querySelectorAll('button,[role=tab],.tab')].find(b => /Add office product/.test(b.textContent)).click()")
    page.until("!!F.document.querySelector('.bld textarea')", 5)
    check("in the shop it says it uses your own Anthropic API key",
          "your own Anthropic API key" in (page.js("F.document.querySelector('.blog').textContent") or ""))
    page.js("const t = F.document.querySelector('.bld textarea'); t.value = 'a tip calculator';"
            " [...F.document.querySelectorAll('.bld button')].find(b => b.textContent === 'Send').click()")
    check("Send asks the shop page (no 'only works inside Randis UDS')", page.until("asks.length === 1", 5),
          page.js("F.document.body.innerText.slice(-300)"))
    asked = page.json("asks[0]") or {}
    check("the ask carries the chat so far", (asked.get("history") or [{}])[-1].get("content") == "a tip calculator", asked)
    check("the built product shows up with its name", page.until("/Tip Calc/.test(F.document.querySelector('.btop').textContent)", 5),
          page.js("F.document.querySelector('.btop') && F.document.querySelector('.btop').textContent"))


FAKE = """window.__req = []; window.__status = 200; const realFetch = window.fetch;
window.fetch = (u, o) => { if (!String(u).startsWith('https://api.anthropic.com/')) return realFetch(u, o);
  __req.push({u: String(u), h: o.headers, b: JSON.parse(o.body)});
  if (__status !== 200) return Promise.resolve(new Response(JSON.stringify({error: {message: 'invalid x-api-key'}}), {status: __status}));
  const ev = (t, d) => 'event: ' + t + '\\ndata: ' + JSON.stringify(d) + '\\n\\n';
  const parts = [ev('message_start', {type: 'message_start'}), ev('content_block_start', {type: 'content_block_start', index: 0}),
    ...ANSWER.match(/[\\s\\S]{1,7}/g).map(t => ev('content_block_delta', {type: 'content_block_delta', index: 0, delta: {type: 'text_delta', text: t}})),
    ev('message_delta', {type: 'message_delta', delta: {stop_reason: 'end_turn'}}), ev('message_stop', {type: 'message_stop'})].join('');
  const bytes = new TextEncoder().encode(parts);
  return Promise.resolve(new Response(new ReadableStream({start(c) { for (let i = 0; i < bytes.length; i += 50) c.enqueue(bytes.slice(i, i + 50)); c.close(); }}), {status: 200})); };
try { sessionStorage.removeItem('office_ai_key'); localStorage.removeItem('office_ai_key'); } catch (e) {}
window.__bar = document.createElement('div'); __bar.hidden = true; document.body.append(__bar); window.__got = [];
window.__ask = () => { __got = []; OfficeAI.ask({history: [{role: 'assistant', content: 'hi'}, {role: 'user', content: 'a tip calculator'}], page: ''}, m => __got.push(m), __bar); };"""


def shop_side(page, check, base):
    page.go(base + "index.html#/apps/randis-office")
    if not check("the shop page loads its AI helper", page.until("!!window.OfficeAI", 10)):
        return
    page.js("const ANSWER = " + json.dumps(ANSWER) + ";\n" + FAKE)
    page.js("__ask()")
    check("with no key yet, it asks for one in the shop's bar (not in the app)", page.until("!__bar.hidden && !!__bar.querySelector('input[type=password]')", 5))
    check("and tells the app it's waiting", page.until("__got.some(m => !m.done && /API key/.test(m.status))", 3), page.json("__got"))
    page.js("__bar.querySelector('input[type=password]').value = 'sk-ant-test-0123456789abcdef'; __bar.querySelector('[data-act=office-key]').click()")
    done = page.until("__got.some(m => m.done)", 10)
    last = (page.json("__got") or [{}])[-1]
    check("the whole streamed answer goes back to the app", done and last.get("text") == ANSWER and not last.get("error"), last)
    check("progress went back while it streamed", page.js("__got.some(m => !m.done && m.status === 'Building…')") is True, page.json("__got.map(m => m.status)"))
    req = (page.json("__req") or [{}])[0]
    h, b = req.get("h") or {}, req.get("b") or {}
    check("it calls Anthropic's Messages API with the key and the browser header",
          req.get("u") == "https://api.anthropic.com/v1/messages" and h.get("x-api-key") == "sk-ant-test-0123456789abcdef"
          and h.get("anthropic-dangerous-direct-browser-access") == "true" and bool(h.get("anthropic-version")), h)
    check("it sends Randis Office's instructions, the model and a stream request",
          "Randis Office" in str(b.get("system")) and b.get("model") == "claude-opus-5-5" and b.get("stream") is True, {k: b.get(k) for k in ("model", "stream")})
    check("the chat is sent starting from a person's message", [m["role"] for m in b.get("messages") or []] == ["user"], b.get("messages"))
    check("the key is kept for this visit only unless they tick Remember",
          page.js("sessionStorage.getItem('office_ai_key') === 'sk-ant-test-0123456789abcdef' && !localStorage.getItem('office_ai_key')") is True)
    page.js("__req = []; __ask()")
    check("the next ask reuses the key without asking", page.until("__got.some(m => m.done)", 10) and page.js("__bar.hidden") is True)
    page.js("__status = 401; __ask()")
    page.until("__got.some(m => m.done)", 10)
    last = (page.json("__got") or [{}])[-1]
    check("a rejected key is forgotten and the app is told why",
          "didn't accept" in str(last.get("error")) and page.js("!sessionStorage.getItem('office_ai_key')") is True, last)
    rules = page.js("document.querySelector('meta[http-equiv=Content-Security-Policy]').content") or ""
    check("the shop page may reach only itself and Anthropic", "connect-src 'self' https://api.anthropic.com;" in rules, rules)


def test(page, check):
    base = harness.serve()
    item_side(page, check, base)
    shop_side(page, check, base)


harness.run(test)
