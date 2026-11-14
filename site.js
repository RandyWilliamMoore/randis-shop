// The Randis Shop. Item text is shown as text, never as HTML, and every game or app runs in a walled-off frame.
"use strict";
const SOFTWARE = Array.isArray(window.SOFTWARE) ? window.SOFTWARE : [];
const UDS = SOFTWARE.find(s => s.slug === "randis-uds");
const MUSIC = Array.isArray(window.MUSIC) ? window.MUSIC : [];
const SHOP = {
  repo: "https://github.com/RandyWilliamMoore/randis-uds",
  // the newest release, from software/randis-uds/info.json; the fixed page is only for when software.js didn't load
  download: (UDS && UDS.download) || "https://github.com/RandyWilliamMoore/randis-uds/releases",
  video: "https://youtu.be/VZeMAVmKJrY",
  videoPic: "https://img.youtube.com/vi/VZeMAVmKJrY/maxresdefault.jpg",
  guestbook: "https://github.com/RandyWilliamMoore/randis-uds/discussions",
  maxSave: 30 * 1024 * 1024,
  maxDownload: 300 * 1024 * 1024,
  saveKinds: { wav: "audio/wav", mp3: "audio/mpeg", ogg: "audio/ogg", flac: "audio/flac", mid: "audio/midi", midi: "audio/midi",
    webm: "video/webm", mp4: "video/mp4", png: "image/png", jpg: "image/jpeg", jpeg: "image/jpeg", gif: "image/gif", webp: "image/webp",
    txt: "text/plain", json: "application/json", csv: "text/csv", md: "text/markdown", ics: "text/calendar",
    docx: "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    xlsx: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" },
  discord: "https://discord.gg/83RmuHcQTR",
  kofi: "https://ko-fi.com/moorescombinatoricsmatrix",
  etsy: "https://www.etsy.com/shop/UberRandis",
};
const SECTIONS = { games: "The Arcade", apps: "The Software Shelf", music: "The Jukebox" };
// The terms every song in the Jukebox comes with.
const ROYALTY_FREE = "Royalty free, with credit: use these songs in anything, paid work included: videos, streams, games, podcasts, shops, on hold lines. "
  + "No payment, no sign-up, no permission needed. The one thing you can't do is sell or hand out the songs themselves as your own music. "
  + "You must credit the song wherever you use it, with the credit line shown under it (in a video, the description is fine).";
const SHOP_PAGE = "randywilliammoore.github.io/randis-shop";
const ARTISTS = { Randy: "Randy Moore" };
// the exact credit for one song, the same words that are inside its MP3
const creditFor = t => `Music: "${t.name}" by ${ARTISTS[t.by] || t.by}, from the Randis Shop (${SHOP_PAGE})`;

function el(tag, attrs, ...kids) {
  const e = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs || {})) {
    if (k === "class") e.className = v;
    else if (k === "on") for (const [ev, fn] of Object.entries(v)) e.addEventListener(ev, fn);
    else e.setAttribute(k, v);
  }
  e.append(...kids.filter(k => k !== null && k !== undefined));
  return e;
}
const out = (href, text, cls) => el("a", { href, target: "_blank", rel: "noopener noreferrer", class: cls || "" }, text);
// A share link: a plain page per item (tools/build_share.py) whose preview shows the item's picture in Discord, then opens the item here.
const PUBLIC = "https://randywilliammoore.github.io/randis-shop/";
const shareLink = (kind, slug) => `${PUBLIC}share/${kind}/${slug}/`;
function copyText(text) {
  if (navigator.clipboard && window.isSecureContext) return navigator.clipboard.writeText(text);
  return new Promise((ok, no) => {
    const t = el("textarea", { readonly: "", class: "offscreen" });
    t.value = text; document.body.append(t); t.select();
    try { document.execCommand("copy") ? ok() : no(); } catch (x) { no(); } finally { t.remove(); }
  });
}
function shareButton(label, link, cls) {
  return el("button", { class: "btn" + (cls ? " " + cls : ""), type: "button", title: link, "data-act": "share", "data-link": link, on: { click: e => {
    const b = e.currentTarget;
    copyText(link).then(() => { b.textContent = "Link copied"; }, () => { b.textContent = "Copy failed: " + link; });
    setTimeout(() => { b.textContent = label; }, 2500);
  } } }, label);
}
const safeWeb = u => (typeof u === "string" && u.startsWith("https://") ? u : null);

function win(title, ...kids) {
  return el("section", { class: "win" },
    el("div", { class: "bar" }, el("h2", {}, title), el("span", { class: "sq", "aria-hidden": "true" }, "_"), el("span", { class: "sq", "aria-hidden": "true" }, "X")),
    el("div", { class: "body" }, ...kids));
}

function visits() {
  try {
    const n = (parseInt(localStorage.getItem("shop_visits"), 10) || 0) + (sessionStorage.getItem("shop_seen") ? 0 : 1);
    localStorage.setItem("shop_visits", String(n));
    sessionStorage.setItem("shop_seen", "1");
    return n;
  } catch (e) { return null; }
}
const visitCount = visits();

function header() {
  return el("section", { class: "win" },
    el("div", { class: "bar" }, el("h1", {}, "The Randis Shop"), el("span", { class: "sq", "aria-hidden": "true" }, "_"), el("span", { class: "sq", "aria-hidden": "true" }, "X")),
    el("div", { class: "sign" }, el("b", {}, "THE RANDIS SHOP"), el("span", {}, "games and apps people made with Randis UDS")),
    el("div", { class: "ticker" }, el("span", {}, "*** WELCOME TO THE SHOP *** PLAY RIGHT HERE, NOTHING TO INSTALL *** EVERY GAME RUNS WALLED OFF FROM YOUR COMPUTER *** ROYALTY-FREE MUSIC IN THE JUKEBOX *** FIND REAL IN-GAME ITEMS AT THE ETSY SHOP ***")),
    el("nav", { class: "nav" },
      el("a", { class: "btn", href: "#/" }, "Front door"),
      el("a", { class: "btn", href: "#/games" }, "Arcade"),
      el("a", { class: "btn", href: "#/apps" }, "Software Shelf"),
      el("a", { class: "btn", href: "#/music" }, "Jukebox"),
      out(SHOP.guestbook, "Guestbook", "btn"),
      shareButton("Share the shop", PUBLIC),
      shareButton("Share Randis UDS", SHOP.repo)));
}

function footer() {
  return win("About this shop", el("div", { class: "foot" },
    el("div", { class: "links" }, out(SHOP.guestbook, "Sign the guestbook"), out(SHOP.discord, "Discord"), out(SHOP.kofi, "Ko-fi"), out(SHOP.etsy, "Real in-game items on Etsy")),
    el("p", {}, "Want to be a sponsor, or host your items, goods and products on the store? Say so in the guestbook or on Discord."),
    visitCount ? el("p", {}, "Your visits: ", el("span", { class: "count" }, String(visitCount).padStart(5, "0")), " (only you can see this; it stays in your browser)") : null,
    el("p", {}, "Made with ", out(SHOP.repo, "Randis UDS"), " by Randy Moore. Support: ", out(SHOP.kofi, "ko-fi.com/moorescombinatoricsmatrix"))));
}

const byKind = kind => window.ITEMS.filter(i => i.kind === kind);

function cabinet(i) {
  return el("a", { class: "cab" + (i.status === "flagged" ? " flagged" : ""), href: `#/${i.kind}/${i.slug}`, "data-item": i.slug },
    el("span", { class: "top" }, i.name),
    el("span", { class: "screen" }, el("img", { src: i.logo, alt: "" })),
    el("span", { class: "deck" }, el("i"), el("i"), el("i")),
    el("span", { class: "slot" }, "INSERT COIN: FREE PLAY"));
}

function softwareBox(i) {
  return el("a", { class: "box" + (i.status === "flagged" ? " flagged" : ""), href: `#/${i.kind}/${i.slug}`, "data-item": i.slug },
    el("b", {}, i.name), el("img", { src: i.logo, alt: "" }), el("small", {}, "BY " + i.by.toUpperCase()));
}

function downloadBox(s) {
  return el("a", { class: "box", href: `#/software/${s.slug}`, "data-item": s.slug },
    el("b", {}, s.name), el("img", { src: s.logo, alt: "" }), el("small", {}, "VERSION " + s.version + ": DOWNLOAD"));
}

function arcade() {
  const items = byKind("games");
  return win(SECTIONS.games, el("div", { class: "arcade" },
    el("p", {}, "Walk up and play. No install, no account, no quarters."),
    items.length ? el("div", { class: "cabs" }, ...items.map(cabinet)) : el("p", {}, "The arcade is empty right now.")));
}

function shelf() {
  const boxes = [...SOFTWARE.map(downloadBox), ...byKind("apps").map(softwareBox)];
  return win(SECTIONS.apps, el("div", { class: "shelf" },
    el("div", { class: "boxes" }, ...(boxes.length ? boxes : [el("p", { class: "empty" }, "The shelf is empty right now.")]))));
}

// Songs made with Randis Sound Forge. They play right here; download any of them, royalty free.
function track(t) {
  const audio = el("audio", { controls: "", preload: "none", src: t.file, on: {
    play: () => { document.querySelectorAll(".track audio").forEach(a => { if (a !== audio) a.pause(); }); if (window.Band) window.Band.play(audio, t.genre, t.name); },
    pause: () => { if (window.Band) window.Band.stop(audio); } } });
  return el("li", { class: "track", id: "song-" + t.slug, "data-item": t.slug },
    el("img", { class: "track-cover", src: t.cover, alt: t.name + " cover art" }),
    el("div", { class: "track-main" },
    el("div", { class: "track-top" },
      el("b", {}, t.name),
      el("span", { class: "track-tags" }, [t.genre, t.length].filter(Boolean).join(" · "))),
    t.blurb ? el("p", {}, t.blurb) : null,
    el("div", { class: "track-play" }, audio,
      el("a", { class: "btn", href: t.file, download: t.download, "data-act": "download-song" }, "Download, royalty free"),
      shareButton("Share", shareLink("music", t.slug))),
    el("div", { class: "credit" }, el("b", {}, "Credit required: "), el("span", { class: "credit-line" }, creditFor(t)), " ",
      el("button", { class: "btn small", "data-act": "copy-credit", on: { click: e => {
        const b = e.currentTarget;
        navigator.clipboard.writeText(creditFor(t)).then(() => { b.textContent = "Copied"; }, () => { b.textContent = "Select it and copy"; });
      } } }, "Copy")),
    el("small", {}, "By " + t.by + ". Made with Randis Sound Forge. The download has its title, description, credit line and cover art inside it.")));
}

function jukebox(short) {
  const songs = short ? MUSIC.slice(0, 3) : MUSIC;
  const forge = window.ITEMS.find(i => i.kind === "apps" && i.slug === "randis-sound-forge");
  return win(SECTIONS.music, el("div", { class: "jukebox" },
    el("div", { class: "juke-sign" }, el("b", {}, "JUKEBOX"), el("span", {}, "royalty-free music, free to use")),
    window.Band ? window.Band.stage() : null,
    songs.length ? el("ol", { class: "tracks" }, ...songs.map(track))
      : el("p", { class: "juke-empty" }, "The first songs are on their way. Check back soon."),
    short && MUSIC.length > songs.length ? el("p", {}, el("a", { class: "btn", href: "#/music" }, `All ${MUSIC.length} songs`)) : null,
    el("div", { class: "inset terms" }, el("b", {}, "The terms. "), ROYALTY_FREE),
    forge ? el("p", { class: "fine juke-made" }, "Every song here was made with ", el("a", { href: `#/apps/${forge.slug}` }, forge.name),
      ", which you can play with right here in the shop.") : null));
}

function softwarePage(s) {
  const link = safeWeb(s.download);
  return [win(s.name + " " + s.version,
    el("div", { class: "item-top" },
      el("div", { class: "item-logo" }, el("img", { src: s.logo, alt: s.name + " logo" })),
      el("div", {},
        el("p", {}, s.blurb),
        el("p", {}, "By " + s.by + ". Version " + s.version + "."),
        el("div", { class: "actions" },
          link ? out(link, `Download ${s.name} ${s.version}`, "btn go") : null,
          safeWeb(s.source) ? out(s.source, "See the code", "btn") : null,
          shareButton("Share", shareLink("software", s.slug)),
          el("a", { class: "btn", href: "#/apps" }, "Back")),
        el("p", { class: "fine" }, s.fine)))),
    s.screenshot ? win("Screenshot", el("img", { class: "screenshot", src: s.screenshot,
      alt: `${s.name} with three tabs open: a notepad, Randis Paint, and the Randis Shop tab listing the shop's games` })) : null,
    win("What's new in " + s.version, el("div", { class: "inset" }, el("ul", { class: "news" }, ...s.new.map(t => el("li", {}, t)))))];
}

function frontDoor() {
  return [
    win("New here? Start with the app", el("div", { class: "feature" },
      el("a", { class: "tv", href: SHOP.video, target: "_blank", rel: "noopener noreferrer" }, el("img", { src: SHOP.videoPic, alt: "Walkthrough video of Randis UDS" }), el("em", {}, "PLAY THE WALKTHROUGH")),
      el("div", {},
        el("p", {}, "Randis UDS is a universal software with no fixed purpose. Describe what you need, and the LLM inside it builds that into the app while you're using it."),
        el("p", {}, "Everything in this shop was made with it."),
        out(SHOP.download, "Get Randis UDS", "btn go"),
        UDS && UDS.screenshot ? el("a", { class: "front-shot", href: `#/software/${UDS.slug}`, title: "More about Randis UDS" },
          el("img", { class: "screenshot", src: UDS.screenshot, alt: "Randis UDS with three tabs open: a notepad, Randis Paint, and the Randis Shop tab listing the shop's games" }),
          el("small", {}, "What it looks like. Click for more.")) : null))),
    arcade(), shelf(), jukebox(true),
    win("Got something to put on the shelf?", el("div", { class: "inset" }, "Submissions open once the safety checks are built. Everything sent in will be checked before it goes on a shelf.")),
  ];
}

function reviewSlot(label, url, pic) {
  const link = safeWeb(url);
  const picture = pic ? el("img", { src: pic, alt: label + " thumbnail" }) : null;
  let screen;
  if (link) screen = el("a", { class: "slot-tv on", href: link, target: "_blank", rel: "noopener noreferrer" }, picture, el("em", {}, "WATCH THE REVIEW"));
  else if (pic) screen = el("div", { class: "slot-tv on" }, picture, el("em", {}, "VIDEO COMING"));
  else screen = el("div", { class: "slot-tv" }, "NO SIGNAL: review coming");
  return el("div", {}, el("h3", {}, label), screen);
}

function itemPage(i) {
  const noun = i.kind === "games" ? "game" : "app";
  const reviews = i.by === "Randy"
    ? [reviewSlot("Randy's review", i.reviews.randy, i.video_pic)]
    : [reviewSlot(`${i.by}'s review`, i.reviews.maker), reviewSlot("Randy's review", i.reviews.randy)];
  const real = safeWeb(i.real_items);
  return [win(i.name,
    el("div", { class: "item-top" },
      el("div", { class: "item-logo" + (i.status === "flagged" ? " flagged" : "") }, el("img", { src: i.logo, alt: i.name + " logo" })),
      el("div", {},
        el("p", {}, i.blurb),
        el("p", {}, "By " + i.by + "."),
        i.status === "flagged" ? el("p", {}, el("b", {}, "This item was flagged and is under review. Play and download are off until it's checked.")) : null,
        i.status === "flagged" ? null : el("div", { class: "actions" },
          el("a", { class: "btn go", href: `#/${i.kind}/${i.slug}/play`, "data-act": "play" }, `Play this ${noun} here`),
          el("a", { class: "btn", href: i.file, download: `${i.slug}.html`, "data-act": "download" }, `Download just this ${noun}`),
          i.open_with ? el("a", { class: "btn", href: i.open_with, "data-act": "open-with" }, "Open With Randis UDS To Edit") : null,
          shareButton("Share", shareLink(i.kind, i.slug)),
          el("a", { class: "btn", href: `#/${i.kind}` }, "Back")),
        i.status === "flagged" ? null : el("p", { class: "fine" }, "Playing here runs it walled off. A downloaded copy opens as a normal page in your browser, without this wall."),
        i.status === "flagged" || !i.open_with ? null : el("p", { class: "fine" }, "Open With needs ", out(SHOP.download, "Randis UDS 0.1.2 or newer"),
          " on your computer. It asks you before it opens anything, then opens the " + noun + " as a tab you can change."),
        real ? el("div", { class: "inset real" }, el("b", {}, "Find real in-game items here: "), out(real, real)) : null))),
    win("On the TV", el("div", { class: "slots" }, ...reviews))];
}

function playWindow(i) {
  let stop = () => {};
  const close = () => { stop(); location.hash = `#/${i.kind}/${i.slug}`; };
  // allow-scripts without allow-same-origin: the page can run, but it can't reach this site or its storage.
  // allow-modals: games use confirm prompts. allow-pointer-lock: mouse look in the 3D games. midi: a music keyboard plugged into this computer. The player's own rules block ordinary loads from the internet.
  const start = page => {
    stop();
    const frame = el("iframe", { src: "site/player.html", sandbox: "allow-scripts allow-modals allow-pointer-lock", allow: "midi *", title: i.name, referrerpolicy: "no-referrer" });
    const hear = e => {
      if (e.source !== frame.contentWindow) return;
      if (e.data === "player-ready") {
        page.then(html => frame.contentWindow.postMessage(html, "*")).catch(() => { note.textContent = "This one wouldn't load. Try again in a moment."; });
      } else if (e.data && e.data.uds === "save-file" && typeof e.data.text === "string" && e.data.text.length <= SHOP.maxSave) {
        // the shop makes the download, under this item's own name, so the wall around the game stays up
        const a = el("a", { href: URL.createObjectURL(new Blob([e.data.text], { type: "text/html" })), download: `${i.slug}.html` });
        document.body.append(a); a.click(); a.remove();
        setTimeout(() => URL.revokeObjectURL(a.href), 5000);
        e.source.postMessage({ uds: "saved", note: `Saved: ${i.slug}.html, in your downloads. Load it here, or open the file, to pick up where you left off.` }, "*");
      } else if (e.data && e.data.uds === "open-link" && typeof e.data.url === "string") {
        askLink(e.data.url);
      } else if (e.data && e.data.uds === "download" && e.data.data instanceof ArrayBuffer) {
        saveDownload(e.data.name, e.data.data);
      } else if (e.data && e.data.uds === "store-get") {
        // an app asking for Randis UDS storage: the shop keeps nothing, and says so at once
        e.source.postMessage({ uds: "store-none" }, "*");
      } else if (e.data && e.data.uds === "export-file" && e.data.data instanceof Blob) {
        // an app's own Save button (the way it saves inside Randis UDS) hands over the file it made; it hears back either way
        const src = e.source, d = e.data;
        const reply = note => src.postMessage({ uds: "exported", ok: /^Saved/.test(note), note }, "*");
        if (d.data.size > SHOP.maxDownload) reply("That file is too big to save from the shop.");
        else d.data.arrayBuffer().then(buf => {
          const file = saveDownload(d.name, buf);
          reply(file ? `Saved ${file} in your downloads.` : "The shop can't save that kind of file, or a save just happened. Try again in a moment.");
        });
      } else if (e.data && typeof e.data.uds === "string" && typeof e.data.id === "string" && e.data.id.length <= 64) {
        // an app asking Randis UDS to do work (web lookups, scans, AI): the shop can't, and says so at once instead of leaving it waiting
        e.source.postMessage({ uds: e.data.uds, id: e.data.id, r: { error: "This part only works inside Randis UDS." } }, "*");
      }
    };
    window.addEventListener("message", hear);
    stop = () => { window.removeEventListener("message", hear); frame.remove(); };
    box.querySelector(".win").append(frame);
  };
  const pick = el("input", { type: "file", accept: ".html,.htm", hidden: "hidden", "data-act": "load-file", on: { change: e => {
    const f = e.target.files[0];
    if (f && f.size <= SHOP.maxSave) start(f.text());
  } } });
  const note = el("span", {}, "Running walled off: it can't reach your files or this site.");
  // A link in the game opens only when the player says so, in a new tab cut off from this site.
  const ask = el("div", { class: "ask", role: "alert" });
  ask.hidden = true;
  const askLink = raw => {
    let u;
    try { u = new URL(raw); } catch (x) { return; }
    if (raw.length > 2000 || !/^https?:$/.test(u.protocol)) return;
    ask.replaceChildren(
      el("span", {}, "This game wants to open a page on ", el("b", { title: u.href }, u.hostname), ". "),
      el("button", { class: "btn small", "data-act": "open-link", on: { click: () => { window.open(u.href, "_blank", "noopener,noreferrer"); ask.hidden = true; } } }, "Open it in a new tab"), " ",
      el("button", { class: "btn small", "data-act": "no-link", on: { click: () => { ask.hidden = true; } } }, "No"));
    ask.hidden = false;
  };
  // A file the game makes (a song, a picture, a recording) is saved by this page, so the wall stays up.
  // Only these kinds, under a plain name, one at a time; never a page or a program.
  let lastSave = 0;
  const saveDownload = (name, buf) => {
    const m = /^(.{0,80}?)\.([a-z0-9]{1,5})$/i.exec(String(name || "").replace(/[^\w .()-]+/g, "_").trim());
    const type = m && SHOP.saveKinds[m[2].toLowerCase()];
    if (!type || buf.byteLength > SHOP.maxDownload || Date.now() - lastSave < 1500) return null;
    lastSave = Date.now();
    const file = `${m[1] || i.slug}.${m[2].toLowerCase()}`;
    const a = el("a", { href: URL.createObjectURL(new Blob([buf], { type })), download: file });
    document.body.append(a); a.click(); a.remove();
    setTimeout(() => URL.revokeObjectURL(a.href), 5000);
    note.textContent = `Saved ${file} in your downloads.`;
    return file;
  };
  const box = el("div", { class: "play", role: "dialog", "aria-label": i.name },
    el("div", { class: "win" },
      el("div", { class: "bar" }, el("h2", {}, i.name), el("button", { class: "sq", "aria-label": "Close", "data-act": "close", on: { click: close } }, "X")),
      ask,
      el("div", { class: "walled" }, note, " ", el("button", { class: "btn small", "data-act": "load-save", on: { click: () => pick.click() } }, "Load a saved file"), pick)));
  start(fetch(i.file).then(r => { if (!r.ok) throw new Error(r.status); return r.text(); }));
  return box;
}

function render() {
  const app = document.getElementById("app");
  const parts = location.hash.replace(/^#\/?/, "").split("/").filter(Boolean);
  const [kind, slug, act] = parts;
  const item = slug ? window.ITEMS.find(i => i.kind === kind && i.slug === slug) : null;
  const soft = kind === "software" && slug && !act ? SOFTWARE.find(s => s.slug === slug) : null;
  let main;
  if (soft) main = softwarePage(soft);
  else if (!kind) main = frontDoor();
  else if (kind === "games" && !slug) main = [arcade()];
  else if (kind === "apps" && !slug) main = [shelf()];
  else if (kind === "music" && !act && (!slug || MUSIC.some(t => t.slug === slug))) main = [jukebox(false)];
  else if (item) main = itemPage(item);
  else main = [win("Not on the shelf", el("div", { class: "inset" }, "That item isn't here. ", el("a", { href: "#/" }, "Back to the front door")))];
  const page = el("div", { class: "page" }, header(), ...main, footer());
  app.replaceChildren(page);
  if (item && act === "play" && item.status !== "flagged") app.append(playWindow(item));
  document.title = item || soft ? `${(item || soft).name} | The Randis Shop` : "The Randis Shop";
  const song = kind === "music" && slug ? document.getElementById("song-" + slug) : null;
  if (song) { song.classList.add("picked"); song.scrollIntoView(); } else window.scrollTo(0, 0);
}

document.addEventListener("keydown", e => {
  if (e.key === "Escape" && /\/play$/.test(location.hash)) location.hash = location.hash.replace(/\/play$/, "");
});
window.addEventListener("hashchange", render);
render();
// The host lets browsers keep music.js for up to 10 minutes, so a song published a moment ago could stay hidden.
// Ask for a fresh copy once the page is up; if it lists songs this one doesn't, show them (never cutting off a song that's playing).
fetch("music.js?t=" + Date.now(), { cache: "no-store" }).then(r => r.ok ? r.text() : "").then(t => {
  const fresh = JSON.parse(t.slice(t.indexOf("["), t.lastIndexOf("]") + 1));
  if (!Array.isArray(fresh) || fresh.map(s => s.slug).join() === MUSIC.map(s => s.slug).join()) return;
  MUSIC.splice(0, MUSIC.length, ...fresh);
  if (![...document.querySelectorAll("audio")].some(a => !a.paused)) render();
}).catch(() => {});
