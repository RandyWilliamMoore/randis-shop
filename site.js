// The Randis Shop. Item text is shown as text, never as HTML, and every game or app runs in a walled-off frame.
"use strict";
const SHOP = {
  repo: "https://github.com/RandyWilliamMoore/randis-uds",
  download: "https://github.com/RandyWilliamMoore/randis-uds/releases/tag/v0.1.2",
  video: "https://youtu.be/VZeMAVmKJrY",
  videoPic: "https://img.youtube.com/vi/VZeMAVmKJrY/maxresdefault.jpg",
  guestbook: "https://github.com/RandyWilliamMoore/randis-uds/discussions",
  maxSave: 30 * 1024 * 1024,
  discord: "https://discord.gg/83RmuHcQTR",
  kofi: "https://ko-fi.com/moorescombinatoricsmatrix",
  etsy: "https://www.etsy.com/shop/UberRandis",
};
const SECTIONS = { games: "The Arcade", apps: "The Software Shelf" };

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
    el("div", { class: "ticker" }, el("span", {}, "*** WELCOME TO THE SHOP *** PLAY RIGHT HERE, NOTHING TO INSTALL *** EVERY GAME RUNS WALLED OFF FROM YOUR COMPUTER *** FIND REAL IN-GAME ITEMS AT THE ETSY SHOP ***")),
    el("nav", { class: "nav" },
      el("a", { class: "btn", href: "#/" }, "Front door"),
      el("a", { class: "btn", href: "#/games" }, "Arcade"),
      el("a", { class: "btn", href: "#/apps" }, "Software Shelf"),
      out(SHOP.guestbook, "Guestbook", "btn")));
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

function arcade() {
  const items = byKind("games");
  return win(SECTIONS.games, el("div", { class: "arcade" },
    el("p", {}, "Walk up and play. No install, no account, no quarters."),
    items.length ? el("div", { class: "cabs" }, ...items.map(cabinet)) : el("p", {}, "The arcade is empty right now.")));
}

function shelf() {
  const items = byKind("apps");
  return win(SECTIONS.apps, el("div", { class: "shelf" },
    el("div", { class: "boxes" }, ...(items.length ? items.map(softwareBox) : [el("p", { class: "empty" }, "The shelf is empty right now.")]))));
}

function frontDoor() {
  return [
    win("New here? Start with the app", el("div", { class: "feature" },
      el("a", { class: "tv", href: SHOP.video, target: "_blank", rel: "noopener noreferrer" }, el("img", { src: SHOP.videoPic, alt: "Walkthrough video of Randis UDS" }), el("em", {}, "PLAY THE WALKTHROUGH")),
      el("div", {},
        el("p", {}, "Randis UDS is a universal software with no fixed purpose. Describe what you need, and the LLM inside it builds that into the app while you're using it."),
        el("p", {}, "Everything in this shop was made with it."),
        out(SHOP.download, "Get Randis UDS", "btn go")))),
    arcade(), shelf(),
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
          el("a", { class: "btn", href: `#/${i.kind}` }, "Back")),
        i.status === "flagged" ? null : el("p", { class: "fine" }, "Playing here runs it walled off. A downloaded copy opens as a normal page in your browser, without this wall."),
        real ? el("div", { class: "inset real" }, el("b", {}, "Find real in-game items here: "), out(real, real)) : null))),
    win("On the TV", el("div", { class: "slots" }, ...reviews))];
}

function playWindow(i) {
  let stop = () => {};
  const close = () => { stop(); location.hash = `#/${i.kind}/${i.slug}`; };
  // allow-scripts without allow-same-origin: the page can run, but it can't reach this site or its storage.
  // allow-modals: games use confirm prompts. allow-pointer-lock: mouse look in the 3D games. The player's own rules block ordinary loads from the internet.
  const start = page => {
    stop();
    const frame = el("iframe", { src: "site/player.html", sandbox: "allow-scripts allow-modals allow-pointer-lock", title: i.name, referrerpolicy: "no-referrer" });
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
  const box = el("div", { class: "play", role: "dialog", "aria-label": i.name },
    el("div", { class: "win" },
      el("div", { class: "bar" }, el("h2", {}, i.name), el("button", { class: "sq", "aria-label": "Close", "data-act": "close", on: { click: close } }, "X")),
      el("div", { class: "walled" }, note, " ", el("button", { class: "btn small", "data-act": "load-save", on: { click: () => pick.click() } }, "Load a saved file"), pick)));
  start(fetch(i.file).then(r => { if (!r.ok) throw new Error(r.status); return r.text(); }));
  return box;
}

function render() {
  const app = document.getElementById("app");
  const parts = location.hash.replace(/^#\/?/, "").split("/").filter(Boolean);
  const [kind, slug, act] = parts;
  const item = slug ? window.ITEMS.find(i => i.kind === kind && i.slug === slug) : null;
  let main;
  if (!kind) main = frontDoor();
  else if (kind === "games" && !slug) main = [arcade()];
  else if (kind === "apps" && !slug) main = [shelf()];
  else if (item) main = itemPage(item);
  else main = [win("Not on the shelf", el("div", { class: "inset" }, "That item isn't here. ", el("a", { href: "#/" }, "Back to the front door")))];
  const page = el("div", { class: "page" }, header(), ...main, footer());
  app.replaceChildren(page);
  if (item && act === "play" && item.status !== "flagged") app.append(playWindow(item));
  document.title = item ? `${item.name} | The Randis Shop` : "The Randis Shop";
  window.scrollTo(0, 0);
}

document.addEventListener("keydown", e => {
  if (e.key === "Escape" && /\/play$/.test(location.hash)) location.hash = location.hash.replace(/\/play$/, "");
});
window.addEventListener("hashchange", render);
render();
