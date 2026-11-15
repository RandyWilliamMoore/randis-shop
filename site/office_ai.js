window.OfficeAI = (function () {
  "use strict";
  const SYSTEM = "You build new office products for Randis Office, an office suite in a web page. A product is ONE self-contained HTML page (inline CSS and JavaScript; no external files, links, fonts, CDNs or network calls) that edits one document at a time, like a word processor, spreadsheet, invoice maker or diagram tool. It runs in a sandboxed frame, so don't use localStorage, cookies or window.open. How it talks to the suite: listen with window.addEventListener('message', ...) for {office:'load', data}, sent once after the page loads (data is null for a new document) and fill the page from it. Whenever the document changes, send parent.postMessage({office:'save', data}, '*') where data is any JSON value (keep it under 200 KB). To give the person a file, send parent.postMessage({office:'export', name:'file.ext', text:'...', mime:'text/plain'}, '*'). Put these in the head: <title>Product name</title>, <meta name=\"office-icon\" content=\"one emoji\">, <meta name=\"office-noun\" content=\"what one document is called, e.g. invoice\"> and <meta name=\"office-color\" content=\"#hex accent colour\">. Make it look clean and work fully; keep the page under about 40 KB. When you make or change the product, reply with one or two plain sentences about it, then the whole page in one ```html block. When the person only asks a question, answer in words without a page. Don't use tools or change any files; just answer.";
  const KEY = "office_ai_key", URL_ = "https://api.anthropic.com/v1/messages", MODEL = "claude-opus-5-5";
  let running = null;
  const getKey = () => { try { return sessionStorage.getItem(KEY) || localStorage.getItem(KEY) || ""; } catch (e) { return ""; } };
  const forget = () => { try { sessionStorage.removeItem(KEY); localStorage.removeItem(KEY); } catch (e) {} };
  const keep = (k, remember) => { try { (remember ? localStorage : sessionStorage).setItem(KEY, k); } catch (e) {} };

  function messages(d) {
    const msgs = (Array.isArray(d.history) ? d.history : []).slice(-16)
      .filter(m => m && typeof m === "object" && m.content)
      .map(m => ({ role: m.role === "assistant" ? "assistant" : "user", content: String(m.content).slice(0, 6000) }));
    while (msgs.length && msgs[0].role !== "user") msgs.shift();
    if (!msgs.length || msgs[msgs.length - 1].role !== "user") return null;
    const page = String(d.page || "").slice(0, 150000);
    if (page) msgs[msgs.length - 1] = { role: "user", content: "The product's current page:\n```html\n" + page + "\n```\n\n" + msgs[msgs.length - 1].content };
    return msgs;
  }

  function askKey(bar) {
    return new Promise(done => {
      const input = el("input", { type: "password", placeholder: "sk-ant-...", autocomplete: "off", "aria-label": "Your Anthropic API key", style: "width:16em" });
      const remember = el("input", { type: "checkbox" });
      const finish = k => { bar.hidden = true; bar.replaceChildren(); done(k); };
      const use = () => { const k = input.value.trim(); if (!/^sk-ant-[\w-]{10,}$/.test(k)) { input.focus(); return; } keep(k, remember.checked); finish(k); };
      input.addEventListener("keydown", e => { if (e.key === "Enter") use(); });
      bar.replaceChildren(
        el("span", {}, "Add office product uses your own Anthropic API key. It stays in this browser and goes only to Anthropic, never to this shop. "),
        input, " ", el("label", {}, remember, " Remember on this computer"), " ",
        el("button", { class: "btn small", "data-act": "office-key", on: { click: use } }, "Use key"), " ",
        el("button", { class: "btn small", "data-act": "office-no-key", on: { click: () => finish("") } }, "Cancel"), " ",
        el("a", { href: "https://console.anthropic.com/settings/keys", target: "_blank", rel: "noopener noreferrer" }, "Get a key"));
      bar.hidden = false;
      input.focus();
    });
  }

  async function ask(d, reply, bar) {
    const msgs = messages(d);
    if (!msgs) return reply({ done: true, error: "nothing to ask yet" });
    if (running) return reply({ done: true, error: "Still working on the last one. Wait for it to finish." });
    let key = getKey();
    if (!key) { reply({ done: false, status: "Waiting for your API key (yellow bar above)…" }); key = await askKey(bar); }
    if (!key) return reply({ done: true, error: "No API key given, so nothing was built. Press Send again when you have one." });
    const ctl = running = new AbortController();
    let text = "", stop = null, last = 0;
    try {
      reply({ done: false, status: "Asking…" });
      const r = await fetch(URL_, {
        method: "POST", signal: ctl.signal,
        headers: { "content-type": "application/json", "x-api-key": key, "anthropic-version": "2026-10-21",
          "anthropic-beta": "server-side-fallback-2026-07-01", "anthropic-dangerous-direct-browser-access": "true" },
        body: JSON.stringify({ model: MODEL, max_tokens: 64000, system: SYSTEM, messages: msgs, stream: true, fallbacks: "default" })
      });
      if (!r.ok) {
        let why = ""; try { why = ((await r.json()).error || {}).message || ""; } catch (e) {}
        if (r.status === 401 || r.status === 403) { forget(); return reply({ done: true, error: "Anthropic didn't accept that API key, so I forgot it. Press Send again to enter another." }); }
        return reply({ done: true, error: "Anthropic said " + r.status + (why ? ": " + why : "") + ". Try again in a moment." });
      }
      const rd = r.body.getReader(), dec = new TextDecoder();
      let buf = "";
      for (;;) {
        const { value, done } = await rd.read();
        if (done) break;
        buf += dec.decode(value, { stream: true });
        let cut;
        while ((cut = buf.indexOf("\n\n")) >= 0) {
          const chunk = buf.slice(0, cut); buf = buf.slice(cut + 2);
          for (const line of chunk.split("\n")) {
            if (!line.startsWith("data:")) continue;
            let ev; try { ev = JSON.parse(line.slice(5)); } catch (e) { continue; }
            if (ev.type === "content_block_delta" && ev.delta && ev.delta.type === "text_delta") text += ev.delta.text;
            else if (ev.type === "message_delta" && ev.delta && ev.delta.stop_reason) stop = ev.delta.stop_reason;
            else if (ev.type === "error") throw new Error((ev.error && ev.error.message) || "the AI stopped with an error");
          }
        }
        if (Date.now() - last > 600) { last = Date.now(); reply({ done: false, status: "Building…", text }); }
      }
      if (stop === "refusal" && !text) return reply({ done: true, error: "The AI declined to build that. Try describing it differently." });
      reply({ done: true, text });
    } catch (e) {
      reply({ done: true, error: ctl.signal.aborted ? "Stopped." : "Couldn't reach Anthropic (" + (e.message || e) + ")." });
    } finally { if (running === ctl) running = null; }
  }
  return { ask, cancel: () => { if (running) running.abort(); }, forget };
})();
