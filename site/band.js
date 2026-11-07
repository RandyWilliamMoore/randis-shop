// The Raisin Band: a little stage in the Jukebox. Four raisins play along with whatever song is on, dressed for its genre,
// and bounce on its beat (read from the song itself with the Web Audio analyser). With nothing playing they rehearse,
// trying on one outfit after another. Everything is drawn here; no pictures are loaded.
"use strict";
window.Band = (() => {
  const W = 960, H = 540, GROUND = 470;
  const TAU = Math.PI * 2;

  // ---------- the band's looks, by genre ----------
  // act: what a raisin does with its hands. acc: what it wears. Order matters: the first theme whose test matches wins.
  const THEMES = [
    { id: "elevator", name: "the Lobby Lounge Raisins", test: /Elevator|Lobby|On Hold|Department|Waiting|Easy Listening|Corporate|Podcast/i, bg: "elevator", calm: 1,
      band: [{ acc: ["bellhop", "bowtie"], act: "vibes" }, { acc: ["bowtie", "combover"], act: "watch" }, { acc: ["bellhop", "bowtie"], act: "upright" }, { acc: ["bowtie", "round"], act: "keys" }] },
    { id: "quest", name: "the Fellowship of the Raisin", pixel: true, test: /8-bit|16-bit|NES|SNES|Game Boy|C64|Atari|Arcade|Genesis|Amiga|PC-98|Chip|Overworld|Dungeon|Boss Battle|Title Screen|Victory Fanfare|Shop|Puzzle|Racing|Space Shooter|Platformer|Game Over|Credits/, bg: "pixel",
      band: [{ acc: ["wizard", "beard"], act: "staff" }, { acc: ["elf"], act: "lute" }, { acc: ["horned", "beard"], act: "drums" }, { acc: ["knight"], act: "sing" }] },
    { id: "medieval", name: "the Raisins of the Round Table", test: /Medieval|Tavern|Celtic|Fantasy|Nordic|Shanty|Bard/i, bg: "castle",
      band: [{ acc: ["wizard", "beard"], act: "staff" }, { acc: ["elf"], act: "lute" }, { acc: ["horned", "beard"], act: "drums" }, { acc: ["knight"], act: "sing" }] },
    { id: "rock", name: "Raisin Hell", test: /Rock|Metal|Punk|Grunge|Djent|Shoegaze|Surf/i, bg: "rock", wild: 1,
      band: [{ acc: ["mohawk", "leather"], act: "guitar" }, { acc: ["longhair", "leather"], act: "sing" }, { acc: ["bandana"], act: "drums" }, { acc: ["longhair", "leather", "round"], act: "bass" }] },
    { id: "synth", name: "the Neon Raisins", test: /Synthwave|Outrun|Darksynth|Dreamwave|Vaporwave|Chillwave|Cyberpunk|80s|City Pop|Italo/i, bg: "grid",
      band: [{ acc: ["mullet", "visor"], act: "keytar" }, { acc: ["headband", "vipers"], act: "keys" }, { acc: ["mullet", "vipers"], act: "drums" }, { acc: ["visor"], act: "sing" }] },
    { id: "lofi", name: "the Sun-Dried Study Club", test: /Lo-fi|Chillhop|Study|Jazzhop|Cozy|Reading|Rainy|Deep Work|Coding|Trip Hop|Chillout|Downtempo|Downbeat|Lounge/i, bg: "room", calm: 1,
      band: [{ acc: ["hoodie", "headphones"], act: "laptop" }, { acc: ["beanie"], act: "keys" }, { acc: ["hoodie"], act: "nod" }, { acc: ["beanie", "headphones"], act: "upright" }] },
    { id: "hiphop", name: "Raisin the Roof Crew", test: /Hip|Trap|Drill|Boom Bap|Golden Era|Coast|Phonk|Grime|Crunk|Bounce|Rap|G-Funk|Plugg|Rage|Reggaeton|Dembow/i, bg: "city",
      band: [{ acc: ["capback", "chain", "headphones"], act: "scratch" }, { acc: ["capback", "chain", "vipers"], act: "mic" }, { acc: ["chain", "beanie"], act: "hype" }, { acc: ["capback", "chain"], act: "pads" }] },
    { id: "club", name: "the Sun-Maid Selectors", test: /House|Techno|Trance|Disco|Electro|EDM|Dance|Big Room|Garage|2-Step|Hardstyle|Hardcore|Gabber|Eurodance|Eurobeat|Future|Dubstep|Riddim|Brostep|DnB|Drum|Jungle|Neuro|Breaks|Big Beat|Amapiano|Gqom|Psy|Goa|Glitch|IDM|Gaming Stream|Starting Soon/i, bg: "club", wild: 1,
      band: [{ acc: ["headphones", "vipers"], act: "djear", glove: 1 }, { acc: ["vipers"], act: "point", glove: 1 }, { acc: ["vipers", "headphones"], act: "decks", glove: 1 }, { acc: ["vipers"], act: "hype", glove: 1 }] },
    { id: "jazz", name: "Raisin Cane and the Prunes", test: /Jazz|Swing|Bebop|Blues|Soul|Funk|Motown|R&B|Gospel|Bossa|Big Band|Boogie/i, bg: "jazz", calm: 1,
      band: [{ acc: ["beret", "round"], act: "sax" }, { acc: ["fedora", "bowtie"], act: "keys" }, { acc: ["beret"], act: "upright" }, { acc: ["fedora", "bowtie"], act: "drums" }] },
    { id: "orchestra", name: "the Royal Raisin Philharmonic", test: /Classical|Baroque|Romantic|Orchestral|Cinematic|Epic|Trailer|Chamber|Piano|Minimalism|Impressionist|Action|Suspense|Horror|Adventure|Sci-Fi|Documentary|Sad/i, bg: "hall", calm: 1,
      band: [{ acc: ["tux", "wildhair"], act: "conduct" }, { acc: ["tux"], act: "violin" }, { acc: ["tux", "round"], act: "violin" }, { acc: ["tux"], act: "upright" }] },
    { id: "ambient", name: "the Sleepy Sultanas", test: /Ambient|Drone|Sleep|Meditation|New Age|Spa|Yoga|Nature|Space/i, bg: "night", calm: 2,
      band: [{ acc: ["nightcap"], act: "sway" }, { acc: ["nightcap"], act: "chimes" }, { acc: ["nightcap"], act: "sway" }, { acc: ["nightcap"], act: "keys" }] },
    { id: "tropic", name: "the Sunny Side Raisins", test: /Reggae|Dub|Dancehall|Ska|Soca|Calypso|Salsa|Bachata|Cumbia|Samba|Tango|Afro|Highlife|Kuduro|Latin|Flamenco/i, bg: "beach",
      band: [{ acc: ["straw", "flower"], act: "maracas" }, { acc: ["straw"], act: "guitar" }, { acc: ["flower"], act: "steeldrum" }, { acc: ["straw", "vipers"], act: "sing" }] },
    { id: "country", name: "the Grapevine Ramblers", test: /Country|Bluegrass|Americana|Folk|Balkan|Western/i, bg: "barn",
      band: [{ acc: ["cowboy"], act: "banjo" }, { acc: ["cowboy", "bandana"], act: "fiddle" }, { acc: ["straw"], act: "upright" }, { acc: ["cowboy"], act: "sing" }] },
    { id: "pop", name: "the Raisinettes", test: /./, bg: "pop",
      band: [{ acc: ["headset", "star"], act: "sing" }, { acc: ["headset"], act: "dance" }, { acc: ["capback"], act: "keys" }, { acc: ["headset"], act: "dance" }] },
  ];
  const themeFor = genre => THEMES.find(t => t.test.test(String(genre || ""))) || THEMES[THEMES.length - 1];

  // ---------- drawing helpers ----------
  let c;   // the 2d context being drawn on
  const fill = (col, f) => { c.fillStyle = col; c.beginPath(); f(); c.fill(); };
  const stroke = (col, w, f) => { c.strokeStyle = col; c.lineWidth = w; c.lineCap = "round"; c.lineJoin = "round"; c.beginPath(); f(); c.stroke(); };
  const rect = (col, x, y, w, h) => { c.fillStyle = col; c.fillRect(x, y, w, h); };
  const circle = (col, x, y, r) => fill(col, () => c.arc(x, y, r, 0, TAU));
  const ellipse = (col, x, y, rx, ry, rot) => fill(col, () => c.ellipse(x, y, rx, ry, rot || 0, 0, TAU));
  const line = (col, w, x1, y1, x2, y2) => stroke(col, w, () => { c.moveTo(x1, y1); c.lineTo(x2, y2); });
  const hue = (h, s, l, a) => `hsla(${h},${s}%,${l}%,${a === undefined ? 1 : a})`;

  // ---------- backgrounds ----------
  const BG = {
    elevator(t, beat) {
      rect("#d9c9a3", 0, 0, W, H);
      for (let x = 30; x < W; x += 180) { rect("#cbb98f", x, 40, 150, 380); rect("#e4d6b3", x + 8, 48, 134, 364); }
      rect("#8a7449", 0, GROUND, W, H - GROUND); rect("#6e5a35", 0, GROUND, W, 8);
      rect("#2a2a2a", W / 2 - 70, 6, 140, 34); c.fillStyle = "#ff9b2e"; c.font = "bold 24px monospace"; c.textAlign = "center";
      c.fillText("▲ " + (1 + Math.floor(t / 4) % 40), W / 2, 32);
      circle("#f3e7c4", W - 60, 250, 16); circle("#d0b26a", W - 60, 250, 10);
    },
    pixel(t, beat) {
      rect("#5c94fc", 0, 0, W, H);
      for (let i = 0; i < 4; i++) { const x = (i * 300 - t * 20) % (W + 200) + (i * 300 - t * 20 < -200 ? W + 200 : 0); ellipse("#fff", x, 80 + i * 25, 60, 22); ellipse("#fff", x + 40, 70 + i * 25, 40, 20); }
      rect("#7c5020", 0, GROUND, W, H - GROUND);
      for (let x = 0; x < W; x += 60) for (let y = GROUND; y < H; y += 30) { c.strokeStyle = "#3a2410"; c.lineWidth = 4; c.strokeRect(x + (y / 30 % 2) * 30, y, 60, 30); }
      rect("#f8b800", 840, 200, 60, 60); c.fillStyle = "#7c5020"; c.font = "bold 44px monospace"; c.textAlign = "center"; c.fillText("?", 870, 246);
    },
    castle(t, beat) {
      rect("#3d3b45", 0, 0, W, H);
      for (let y = 0; y < GROUND; y += 40) for (let x = (y / 40 % 2) * 40; x < W; x += 80) { c.strokeStyle = "#2b2930"; c.lineWidth = 3; c.strokeRect(x, y, 80, 40); }
      for (const x of [140, 820]) { rect("#5a3a1a", x - 6, 150, 12, 50); ellipse(hue(30 + Math.sin(t * 9 + x) * 10, 100, 55), x, 140 - Math.sin(t * 13 + x) * 4, 12, 22); ellipse("#ffe08a", x, 145, 6, 11); }
      for (const [x, col] of [[300, "#8b1e2b"], [660, "#1e3f8b"]]) { rect(col, x - 40, 40, 80, 150); fill(col, () => { c.moveTo(x - 40, 190); c.lineTo(x, 220); c.lineTo(x + 40, 190); }); circle("#e8c547", x, 110, 18); }
      rect("#5b4636", 0, GROUND, W, H - GROUND);
    },
    rock(t, beat) {
      rect("#140808", 0, 0, W, H);
      for (let i = 0; i < 5; i++) fill(hue(i * 70 + t * 30, 90, 50, .16 + beat * .2), () => { const x = 100 + i * 190; c.moveTo(x - 20, 0); c.lineTo(x + 20, 0); c.lineTo(x + 140 * Math.sin(t + i), GROUND); c.lineTo(x - 140 + 140 * Math.sin(t + i), GROUND); });
      for (const x of [20, 850]) for (let y = 230; y < GROUND; y += 80) { rect("#222", x, y, 90, 76); rect("#3a3a3a", x + 6, y + 6, 78, 64); circle("#111", x + 45, y + 38, 26); }
      rect("#2a1a10", 0, GROUND, W, H - GROUND);
    },
    grid(t, beat) {
      const g = c.createLinearGradient(0, 0, 0, 300); g.addColorStop(0, "#14002e"); g.addColorStop(1, "#ff2a8a"); c.fillStyle = g; c.fillRect(0, 0, W, 300);
      for (let i = 0; i < 8; i++) { const y = 120 + i * 18; c.save(); c.beginPath(); c.arc(W / 2, 220, 110, 0, TAU); c.clip(); rect(i % 2 ? "#ffd23f" : "#ff7a2e", 0, y, W, 9 + i); c.restore(); }
      rect("#14002e", 0, 300, W, H - 300);
      for (let i = -12; i <= 12; i++) line("#ff4fd8", 2, W / 2 + i * 20, 300, W / 2 + i * 160, H);
      for (let k = 0; k < 10; k++) { const y = 300 + ((k * 30 + t * 60) % 240) * ((k * 30 + t * 60) % 240) / 240; line("#38f2ff", 2, 0, y, W, y); }
    },
    room(t, beat) {
      rect("#3b2f45", 0, 0, W, H);
      rect("#1d2340", 600, 60, 260, 200); rect("#4b3a2a", 592, 52, 276, 8); rect("#4b3a2a", 592, 260, 276, 8); rect("#4b3a2a", 726, 60, 8, 200);
      for (let i = 0; i < 40; i++) { const x = 605 + (i * 53) % 250, y = 65 + (i * 37 + t * 220) % 190; line("rgba(170,190,255,.55)", 2, x, y, x - 3, y + 12); }
      fill("rgba(255,210,120,.18)", () => { c.moveTo(120, 90); c.lineTo(40, GROUND); c.lineTo(260, GROUND); });
      rect("#5c4433", 110, 70, 20, 30); ellipse("#ffd27a", 120, 100, 30, 10);
      rect("#4a3528", 0, GROUND, W, H - GROUND);
      ellipse("#222", 880, GROUND - 18, 26, 18); circle("#222", 902, GROUND - 38, 13); fill("#222", () => { c.moveTo(894, GROUND - 48); c.lineTo(898, GROUND - 60); c.lineTo(904, GROUND - 49); });
    },
    city(t, beat) {
      rect("#101028", 0, 0, W, H);
      for (let i = 0; i < 14; i++) { const x = i * 72, h = 120 + (i * 97) % 200; rect("#1c1c3a", x, GROUND - 60 - h, 64, h + 60); for (let y = GROUND - 50 - h; y < GROUND - 70; y += 26) for (let k = 0; k < 3; k++) if ((i + y + k) % 3) rect("#ffd96a", x + 8 + k * 18, y, 10, 12); }
      rect("#3a3a48", 0, GROUND - 120, W, 120);
      for (const [x, col] of [[90, "#ff4fd8"], [380, "#38f2ff"], [700, "#ffd23f"]]) stroke(col, 14, () => { c.moveTo(x, GROUND - 40); c.bezierCurveTo(x + 60, GROUND - 120, x + 120, GROUND - 10, x + 190, GROUND - 90); });
      rect("#222", 0, GROUND, W, H - GROUND);
    },
    club(t, beat) {
      rect("#07040f", 0, 0, W, H);
      for (let i = 0; i < 6; i++) { const a = t * .8 + i * 1.05; stroke(hue(i * 60 + t * 40, 100, 60, .35 + beat * .5), 4, () => { c.moveTo(W / 2, 70); c.lineTo(W / 2 + Math.cos(a) * 900, 70 + Math.abs(Math.sin(a)) * 700); }); }
      circle("#c9c9d6", W / 2, 70, 34); for (let i = 0; i < 18; i++) rect(hue(i * 20 + t * 90, 70, 80), W / 2 - 30 + (i % 6) * 10, 44 + Math.floor(i / 6) * 16, 8, 8);
      rect("#160d26", 0, GROUND, W, H - GROUND);
      for (let x = 0; x < W; x += 80) rect(hue((x + t * 120) % 360, 90, 45, .5 + beat * .5), x, GROUND, 78, 10);
    },
    jazz(t, beat) {
      rect("#2a0a0e", 0, 0, W, H);
      for (let x = 0; x < W; x += 48) { const g = c.createLinearGradient(x, 0, x + 48, 0); g.addColorStop(0, "#5c0d17"); g.addColorStop(.5, "#8a1424"); g.addColorStop(1, "#5c0d17"); c.fillStyle = g; c.fillRect(x, 0, 48, GROUND); }
      fill("rgba(255,240,190,.13)", () => { c.moveTo(W / 2 - 40, 0); c.lineTo(W / 2 + 40, 0); c.lineTo(W / 2 + 420, GROUND); c.lineTo(W / 2 - 420, GROUND); });
      rect("#3a2414", 0, GROUND, W, H - GROUND);
    },
    hall(t, beat) {
      rect("#2a1f14", 0, 0, W, H);
      for (let x = 40; x < W; x += 120) { rect("#c9a352", x, 0, 24, GROUND); rect("#e3c477", x + 4, 0, 6, GROUND); }
      for (let i = 0; i < 3; i++) { circle("rgba(255,230,160,.25)", 180 + i * 300, 50, 40); circle("#ffe9a8", 180 + i * 300, 50, 10); }
      rect("#5a3a20", 0, GROUND, W, H - GROUND);
    },
    night(t, beat) {
      const g = c.createLinearGradient(0, 0, 0, GROUND); g.addColorStop(0, "#020418"); g.addColorStop(1, "#1a2350"); c.fillStyle = g; c.fillRect(0, 0, W, GROUND);
      for (let i = 0; i < 70; i++) circle(`rgba(255,255,255,${.4 + .4 * Math.sin(t * 1.5 + i)})`, (i * 137) % W, (i * 71) % 330, 1.6);
      circle("#f4f1d0", 820, 90, 40); circle("#1a2350", 838, 80, 36);
      rect("#10162e", 0, GROUND, W, H - GROUND);
    },
    beach(t, beat) {
      const g = c.createLinearGradient(0, 0, 0, 330); g.addColorStop(0, "#ff7e5f"); g.addColorStop(1, "#feb47b"); c.fillStyle = g; c.fillRect(0, 0, W, 330);
      circle("#ffe36e", 480, 300, 80); rect("#1f7fa6", 0, 330, W, 80);
      for (let k = 0; k < 4; k++) stroke("rgba(255,255,255,.5)", 3, () => { for (let x = 0; x <= W; x += 20) c.lineTo(x, 345 + k * 16 + Math.sin(x / 40 + t * 2 + k) * 4); });
      rect("#f0d28c", 0, 410, W, H - 410);
      for (const x of [70, 890]) { stroke("#6b4a2a", 14, () => { c.moveTo(x, 470); c.quadraticCurveTo(x + 20, 300, x - 10, 180); }); for (let i = 0; i < 5; i++) stroke("#2f8a3a", 10, () => { c.moveTo(x - 10, 180); c.quadraticCurveTo(x - 10 + Math.cos(i * 1.3) * 60, 150, x - 10 + Math.cos(i * 1.3) * 100, 200 + Math.sin(t + i) * 6); }); }
    },
    barn(t, beat) {
      rect("#8fc9ef", 0, 0, W, H);
      rect("#a2302a", 180, 90, 600, 380); fill("#7d211d", () => { c.moveTo(160, 100); c.lineTo(480, 10); c.lineTo(800, 100); });
      for (let x = 180; x < 780; x += 30) line("#8a2722", 3, x, 100, x, GROUND);
      rect("#c9a54a", 0, GROUND, W, H - GROUND);
      for (const x of [40, 840]) { rect("#d9b64c", x, GROUND - 60, 90, 60); line("#a8862c", 3, x, GROUND - 30, x + 90, GROUND - 30); }
    },
    pop(t, beat) {
      rect("#1a0636", 0, 0, W, H);
      for (let i = 0; i < 7; i++) fill(hue(i * 50 + t * 50, 90, 60, .22 + beat * .3), () => { const x = 70 + i * 135; c.moveTo(x - 12, 0); c.lineTo(x + 12, 0); c.lineTo(x + 90, GROUND); c.lineTo(x - 90, GROUND); });
      rect("#2c1a4a", 0, GROUND, W, H - GROUND);
      for (let x = 0; x < W; x += 40) circle(hue(x + t * 200, 90, 65), x + 20, GROUND + 14, 6);
    },
  };

  // ---------- one raisin ----------
  function raisin(m, cx, t, beat, theme, i) {
    const calm = theme.calm || 0, wild = theme.wild || 0;
    const groove = Math.sin(t * (calm ? 2.2 : 4.4) + i * 1.7);
    const bob = beat * (calm ? 6 : 16 + wild * 8) + groove * (calm ? 3 : 4);
    const tilt = (m.act === "nod" || m.act === "point" || m.act === "djear" ? beat * .22 : 0) + groove * (calm ? .04 : .07) + (wild && m.act !== "drums" ? beat * .15 * (i % 2 ? 1 : -1) : 0);
    const cy = GROUND - 96 - bob, glove = m.glove ? "#fff" : "#3d1c33";
    const sx = 40, sy = cy + 4;                  // shoulders, either side
    const hands = pose(m.act, t, beat, i, calm);
    // legs and feet
    const step = m.act === "dance" ? Math.sin(t * 8) * 10 : groove * 3;
    line("#2e1427", 7, cx - 16, cy + 48, cx - 22 - step, GROUND - 6); line("#2e1427", 7, cx + 16, cy + 48, cx + 22 + step, GROUND - 6);
    ellipse("#1a0b16", cx - 28 - step, GROUND - 4, 16, 8); ellipse("#1a0b16", cx + 28 + step, GROUND - 4, 16, 8);
    behind(m.act, cx, cy, t, beat);
    c.save(); c.translate(cx, cy); c.rotate(tilt);
    // the raisin itself: wrinkled and purple-brown
    const g = c.createRadialGradient(-14, -22, 6, 0, 0, 64); g.addColorStop(0, "#8a4a73"); g.addColorStop(.6, "#5a2848"); g.addColorStop(1, "#371530"); c.fillStyle = g;
    c.beginPath(); for (let k = 0; k <= 40; k++) { const a = k / 40 * TAU, r = 1 + .05 * Math.sin(a * 7 + i) ; c.lineTo(Math.cos(a) * 44 * r, Math.sin(a) * 58 * r); } c.fill();
    for (let k = 0; k < 5; k++) stroke("rgba(30,8,24,.55)", 2.5, () => c.arc(-6 + k * 4, -30 + k * 17, 26 - Math.abs(k - 2) * 4, .2 + k * .1, 2.4 - k * .1));
    stroke("rgba(190,120,170,.35)", 2, () => c.arc(-14, -26, 18, 3.6, 4.6));
    clothes(m.acc, t, beat);
    // face
    const look = Math.sin(t * .7 + i) * 2;
    const shades = m.acc.includes("vipers") || m.acc.includes("round") || m.acc.includes("visor");
    if (!shades || m.acc.includes("round")) {
      ellipse("#fff", -14, -22, 9, 11); ellipse("#fff", 14, -22, 9, 11);
      circle("#111", -13 + look, -20, 4.5); circle("#111", 15 + look, -20, 4.5);
      if (m.act === "sway" && theme.id === "ambient") { rect("#5a2848", -24, -34, 48, 13); line("#111", 2, -22, -22, -6, -22); line("#111", 2, 6, -22, 22, -22); }
    }
    if (m.act === "sing" || m.act === "mic") ellipse("#1a0510", 0, 8, 8, 6 + beat * 8);
    else stroke("#1a0510", 3, () => c.arc(0, 2, 13, .25, Math.PI - .25));
    face(m.acc, t, beat);
    hats(m.acc, t, beat);
    c.restore();
    // arms and hands, then what they hold
    const L = [cx + hands.L[0], cy + hands.L[1]], R = [cx + hands.R[0], cy + hands.R[1]];
    const arm = (x0, y0, [x1, y1], side) => stroke("#2e1427", 6, () => { c.moveTo(x0, y0); c.quadraticCurveTo((x0 + x1) / 2 + side * 14, Math.max(y0, y1) + 12, x1, y1); });
    held(m.act, cx, cy, L, R, t, beat, "back");
    arm(cx - sx, sy, L, -1); arm(cx + sx, sy, R, 1);
    circle(glove, L[0], L[1], 8); circle(glove, R[0], R[1], 8);
    if (m.glove) { circle("#ddd", L[0], L[1], 3); circle("#ddd", R[0], R[1], 3); }
    if (m.act === "point") { line(glove, 5, R[0], R[1], R[0] + 2, R[1] - 18); }
    held(m.act, cx, cy, L, R, t, beat, "front");
  }

  // where the hands go, from the body's centre
  function pose(act, t, beat, i, calm) {
    const s = Math.sin(t * 8 + i), q = Math.sin(t * 4 + i);
    switch (act) {
      case "djear": return { L: [-46, -24], R: [40, 36 + s * 4] };
      case "point": return { L: [-40, 40], R: [56, -110 - beat * 18] };
      case "decks": case "scratch": return { L: [-38, 50 + s * 3], R: [34 + q * 12, 52] };
      case "hype": return { L: [-60, -70 - beat * 30], R: [60, -70 - beat * 30] };
      case "guitar": case "lute": case "banjo": case "bass": return { L: [-58, 26], R: [16, 44 + s * 10] };
      case "keytar": return { L: [-50, 34], R: [24 + q * 6, 40 + s * 3] };
      case "keys": case "pads": case "laptop": return { L: [-30 + q * 6, 56 - Math.abs(s) * 6], R: [30 - q * 6, 56 - Math.abs(Math.cos(t * 8)) * 6] };
      case "drums": return { L: [-46, 40 - Math.max(0, s) * 26], R: [46, 40 - Math.max(0, -s) * 26] };
      case "vibes": return { L: [-36 + q * 12, 52 - Math.abs(s) * 10], R: [36 + q * 12, 52 - Math.abs(Math.cos(t * 8)) * 10] };
      case "upright": return { L: [-46, -10], R: [-10, 30 + s * 6] };
      case "sax": return { L: [-14, 14], R: [12, 34] };
      case "violin": case "fiddle": return { L: [-46, -16], R: [38 + q * 24, -2 + q * 6] };
      case "conduct": return { L: [-40, 20], R: [52 + Math.cos(t * 5) * 20, -54 + Math.sin(t * 10) * 18] };
      case "mic": case "sing": return { L: [-12, 4], R: [56, -30 - beat * 20] };
      case "staff": return { L: [-52, 0], R: [44, 30] };
      case "watch": return { L: [-18, -2], R: [44, 40] };
      case "maracas": return { L: [-58, -10 - s * 18], R: [58, -10 + s * 18] };
      case "steeldrum": return { L: [-26 + q * 8, 50 - Math.abs(s) * 10], R: [26 - q * 8, 50 - Math.abs(Math.cos(t * 8)) * 10] };
      case "chimes": return { L: [-40, 30], R: [50 + q * 8, -20] };
      case "dance": return { L: [-60 + s * 6, -40 + s * 30], R: [60 - s * 6, -40 - s * 30] };
      default: return { L: [-48, 40 + s * 3], R: [48, 40 - s * 3] };
    }
  }

  // things that stand behind the raisin
  function behind(act, cx, cy, t, beat) {
    if (act === "upright") { ellipse("#7a3f17", cx - 34, cy + 40, 26, 46); ellipse("#7a3f17", cx - 34, cy - 2, 20, 30); line("#2b1608", 4, cx - 30, cy - 120, cx - 34, cy + 80); }
    if (act === "chimes") { line("#888", 3, cx + 30, cy - 60, cx + 90, cy - 60); for (let k = 0; k < 5; k++) line(hue(40, 60, 70 + k * 4), 4, cx + 36 + k * 12, cy - 60, cx + 36 + k * 12, cy - 10 - k * 6 + Math.sin(t * 3 + k) * 3); }
  }

  // things held or played, drawn behind ("back") or in front of the arms
  function held(act, cx, cy, [lx, ly], [rx, ry], t, beat, layer) {
    if (layer === "back") {
      if (act === "guitar" || act === "bass") { line("#3a2410", 7, cx + 10, cy + 38, lx - 10, ly - 8); ellipse(act === "bass" ? "#1d5fa8" : "#c0262b", cx + 14, cy + 44, 24, 18, -.4); circle("#111", cx + 14, cy + 44, 6); }
      if (act === "lute") { line("#5a3a1a", 6, cx + 10, cy + 40, lx - 6, ly - 10); ellipse("#b07b3c", cx + 14, cy + 46, 22, 18, -.4); circle("#3a2410", cx + 14, cy + 44, 5); }
      if (act === "banjo") { line("#5a3a1a", 5, cx + 10, cy + 40, lx - 8, ly - 10); circle("#e9e3d0", cx + 14, cy + 44, 20); stroke("#9a8a5a", 3, () => c.arc(cx + 14, cy + 44, 20, 0, TAU)); }
      if (act === "keytar") { c.save(); c.translate(cx - 6, cy + 40); c.rotate(-.3); rect("#ff4fd8", -50, -10, 100, 22); for (let k = 0; k < 9; k++) rect("#fff", -44 + k * 10, -6, 8, 14); rect("#38f2ff", -80, -6, 32, 8); c.restore(); }
      if (act === "violin" || act === "fiddle") { c.save(); c.translate(cx - 30, cy - 4); c.rotate(-.6); ellipse("#9a4a16", 0, 0, 12, 22); line("#2b1608", 3, 0, -20, 0, -44); c.restore(); }
      if (act === "sax") { stroke("#e2b53a", 9, () => { c.moveTo(cx - 4, cy + 6); c.lineTo(cx + 2, cy + 44); c.quadraticCurveTo(cx + 8, cy + 64, cx + 26, cy + 50); c.lineTo(cx + 30, cy + 36); }); circle("#e2b53a", cx + 31, cy + 33, 9); }
      return;
    }
    if (act === "djear" || act === "decks" || act === "scratch") {   // the booth stands in front
      rect("#1d1d24", cx - 70, cy + 54, 140, 70); rect(act === "scratch" ? "#333" : "#26263a", cx - 70, cy + 50, 140, 10);
      for (const dx of [-36, 36]) { circle("#0b0b0b", cx + dx, cy + 54, 22); circle(hue(t * 200 % 360, 90, 60), cx + dx, cy + 54, 5); line("#999", 2, cx + dx, cy + 54, cx + dx + Math.cos(t * 7 + dx) * 20, cy + 54 + Math.sin(t * 7 + dx) * 6); }
      for (let k = 0; k < 6; k++) rect(hue(k * 60, 100, 50 + beat * 30), cx - 60 + k * 22, cy + 90, 14, 6);
    }
    if (act === "keys" || act === "pads") { rect("#222", cx - 60, cy + 58, 120, 16); rect("#555", cx - 50, cy + 74, 6, 70); rect("#555", cx + 44, cy + 74, 6, 70);
      for (let k = 0; k < 12; k++) rect(act === "pads" ? hue(k * 30, 90, 40 + beat * 30) : "#f5f5f5", cx - 57 + k * 9.6, cy + 60, 8, 10); }
    if (act === "laptop") { rect("#5b4636", cx - 70, cy + 64, 140, 12); rect("#4b3626", cx - 60, cy + 76, 8, 60); rect("#4b3626", cx + 52, cy + 76, 8, 60);
      fill("#9aa0a8", () => { c.moveTo(cx - 34, cy + 64); c.lineTo(cx - 26, cy + 26); c.lineTo(cx + 30, cy + 26); c.lineTo(cx + 34, cy + 64); }); circle("#fff", cx + 2, cy + 44, 4); }
    if (act === "drums") { ellipse("#ddd", cx - 46, cy + 58, 24, 8); ellipse("#ddd", cx + 46, cy + 58, 24, 8); circle("#b3262d", cx, cy + 92, 36); circle("#eee", cx, cy + 92, 28); ellipse("#e2c23a", cx + 74, cy + 22 - beat * 6, 26, 5);
      line("#e8d3a8", 4, lx, ly, lx + 12, ly + 18); line("#e8d3a8", 4, rx, ry, rx - 12, ry + 18); }
    if (act === "vibes") { for (let k = 0; k < 8; k++) rect("#c9c9d6", cx - 64 + k * 16, cy + 58, 13, 30 - k * 2); rect("#444", cx - 66, cy + 92, 132, 6);
      line("#8a5a2a", 3, lx, ly, lx + 6, ly + 12); line("#8a5a2a", 3, rx, ry, rx - 6, ry + 12); circle("#fff3c4", lx + 6, ly + 12, 4); circle("#fff3c4", rx - 6, ry + 12, 4); }
    if (act === "steeldrum") { ellipse("#bfc6cf", cx, cy + 66, 50, 16); rect("#9aa1aa", cx - 50, cy + 66, 100, 40); ellipse("#d9dee4", cx, cy + 64, 42, 11); }
    if (act === "mic" || act === "sing") { line("#222", 5, rx, ry, rx - 14, ry - 10); circle("#555", rx - 18, ry - 13, 7); }
    if (act === "violin" || act === "fiddle") line("#e8d3a8", 2, rx - 30, ry - 20, rx + 30, ry + 16);
    if (act === "conduct") line("#fff", 3, rx, ry, rx + 26, ry - 20);
    if (act === "staff") { line("#6b4a2a", 6, rx, ry - 140, rx, ry + 70); circle(`rgba(120,200,255,${.4 + beat * .6})`, rx, ry - 146, 14 + beat * 10); circle("#e8f6ff", rx, ry - 146, 6); }
    if (act === "watch") { rect("#e2b53a", lx - 8, ly - 3, 16, 7); circle("#fff", lx, ly, 5); }
    if (act === "maracas") for (const [x, y] of [[lx, ly], [rx, ry]]) { ellipse("#e05a2a", x, y - 14, 10, 14); line("#7a4a2a", 4, x, y, x, y - 4); }
    if (act === "steeldrum") { line("#ddd", 3, lx, ly, lx + 4, ly + 10); line("#ddd", 3, rx, ry, rx - 4, ry + 10); }
  }

  // clothes on the body (drawn in the raisin's own turned frame)
  function clothes(acc, t, beat) {
    if (acc.includes("tux")) { fill("#111", () => { c.moveTo(-44, 10); c.lineTo(-8, 10); c.lineTo(0, 56); c.lineTo(-30, 50); }); fill("#111", () => { c.moveTo(44, 10); c.lineTo(8, 10); c.lineTo(0, 56); c.lineTo(30, 50); }); fill("#fff", () => { c.moveTo(-8, 10); c.lineTo(8, 10); c.lineTo(0, 40); }); }
    if (acc.includes("leather")) { fill("#1b1b1b", () => { c.moveTo(-44, 12); c.lineTo(-10, 16); c.lineTo(-14, 56); c.lineTo(-36, 46); }); fill("#1b1b1b", () => { c.moveTo(44, 12); c.lineTo(10, 16); c.lineTo(14, 56); c.lineTo(36, 46); }); circle("#bbb", -24, 30, 2.5); circle("#bbb", 24, 30, 2.5); }
    if (acc.includes("hoodie")) { fill("#5a6b7a", () => { c.ellipse(0, 30, 44, 28, 0, 0, Math.PI); }); line("#ddd", 2, -8, 8, -10, 26); line("#ddd", 2, 8, 8, 10, 26); }
    if (acc.includes("knight")) { fill("#9aa3ad", () => c.ellipse(0, 26, 44, 32, 0, 0, Math.PI)); rect("#c0262b", -8, 10, 16, 40); rect("#c0262b", -20, 20, 40, 10); }
    if (acc.includes("bowtie")) { fill("#c0262b", () => { c.moveTo(0, 22); c.lineTo(-14, 14); c.lineTo(-14, 30); }); fill("#c0262b", () => { c.moveTo(0, 22); c.lineTo(14, 14); c.lineTo(14, 30); }); circle("#8a1a1f", 0, 22, 4); }
    if (acc.includes("chain")) { stroke("#f2c94c", 4, () => c.arc(0, 4, 26, .5, Math.PI - .5)); circle("#f2c94c", 0, 30 + beat * 3, 8); }
    if (acc.includes("flower")) for (let k = 0; k < 5; k++) circle(hue(k * 70, 80, 60), -30 + k * 14, 18 + (k % 2) * 6, 6);
    if (acc.includes("star")) fill("#ffd23f", () => { for (let k = 0; k < 10; k++) { const r = k % 2 ? 5 : 12, a = k * Math.PI / 5 - Math.PI / 2; c.lineTo(-26 + Math.cos(a) * r, 28 + Math.sin(a) * r); } });
  }

  // things on the face
  function face(acc, t, beat) {
    if (acc.includes("vipers")) {     // wraparound neon shades
      const g = c.createLinearGradient(-36, 0, 36, 0); g.addColorStop(0, "#ff4fd8"); g.addColorStop(.5, "#ffd23f"); g.addColorStop(1, "#38f2ff");
      fill(g, () => { c.moveTo(-40, -30); c.quadraticCurveTo(0, -38, 40, -30); c.lineTo(36, -14); c.quadraticCurveTo(0, -10, -36, -14); }); rect("rgba(255,255,255,.6)", -26, -28, 14, 3);
      line("#ff4fd8", 3, -40, -28, -46, -24); line("#38f2ff", 3, 40, -28, 46, -24);
    }
    if (acc.includes("round")) { stroke("#222", 3, () => { c.arc(-14, -22, 11, 0, TAU); }); stroke("#222", 3, () => { c.arc(14, -22, 11, 0, TAU); }); line("#222", 3, -3, -22, 3, -22); }
    if (acc.includes("visor")) { fill("rgba(56,242,255,.75)", () => { c.moveTo(-40, -32); c.lineTo(40, -32); c.lineTo(36, -14); c.lineTo(-36, -14); }); }
    if (acc.includes("beard")) fill(acc.includes("wizard") ? "#e8e8e8" : "#b5651d", () => { c.moveTo(-22, 8); c.quadraticCurveTo(0, 70, 22, 8); c.quadraticCurveTo(0, 20, -22, 8); });
    if (acc.includes("elf")) { fill("#5a2848", () => { c.moveTo(-40, -20); c.lineTo(-64, -40); c.lineTo(-42, -6); }); fill("#5a2848", () => { c.moveTo(40, -20); c.lineTo(64, -40); c.lineTo(42, -6); }); }
    if (acc.includes("headset")) { line("#222", 2, -40, -14, -20, 8); circle("#222", -18, 9, 3); }
  }

  // hats, hair and headphones
  function hats(acc, t, beat) {
    if (acc.includes("headphones")) { stroke("#222", 6, () => c.arc(0, -40, 40, Math.PI * 1.08, Math.PI * 1.92)); ellipse("#222", -40, -26, 9, 15); ellipse("#222", 40, -26, 9, 15); }
    if (acc.includes("bellhop")) { rect("#c0262b", -20, -76, 40, 22); ellipse("#8a1a1f", 0, -54, 24, 5); rect("#e2b53a", -20, -62, 40, 4); }
    if (acc.includes("combover")) stroke("#1a0b16", 3, () => { c.moveTo(-30, -48); c.quadraticCurveTo(0, -66, 30, -50); });
    if (acc.includes("wizard")) { fill("#2b3fa0", () => { c.moveTo(-40, -48); c.lineTo(10, -150); c.lineTo(40, -48); }); ellipse("#2b3fa0", 0, -48, 50, 9); for (const [x, y] of [[-6, -80], [10, -108], [-14, -60]]) circle("#ffd23f", x, y, 3); }
    if (acc.includes("horned")) { fill("#9aa3ad", () => c.arc(0, -46, 34, Math.PI, 0)); fill("#f0e6c8", () => { c.moveTo(-30, -56); c.quadraticCurveTo(-60, -70, -54, -100); c.lineTo(-24, -66); }); fill("#f0e6c8", () => { c.moveTo(30, -56); c.quadraticCurveTo(60, -70, 54, -100); c.lineTo(24, -66); }); }
    if (acc.includes("knight")) { fill("#9aa3ad", () => c.arc(0, -40, 40, Math.PI, 0)); fill("#c0262b", () => { c.moveTo(0, -80); c.quadraticCurveTo(30, -110, 40, -76); c.quadraticCurveTo(20, -90, 0, -80); }); }
    if (acc.includes("mohawk")) fill("#38f22f", () => { for (let k = 0; k <= 6; k++) { c.lineTo(-24 + k * 8, -54); c.lineTo(-20 + k * 8, -92 - (k % 2) * 8 - beat * 8); } c.lineTo(28, -54); });
    if (acc.includes("longhair")) { const flip = Math.sin(t * 9) * 10 * (1 + beat); fill("#1a0b16", () => { c.moveTo(-40, -40); c.quadraticCurveTo(-60 + flip, 20, -50 + flip, 50); c.lineTo(-30, 0); }); fill("#1a0b16", () => { c.moveTo(40, -40); c.quadraticCurveTo(60 + flip, 20, 50 + flip, 50); c.lineTo(30, 0); }); fill("#1a0b16", () => c.arc(0, -40, 38, Math.PI, 0)); }
    if (acc.includes("bandana")) { fill("#c0262b", () => c.ellipse(0, -46, 42, 12, 0, Math.PI, 0)); fill("#c0262b", () => { c.moveTo(38, -46); c.lineTo(58, -40 + Math.sin(t * 8) * 4); c.lineTo(52, -30); }); }
    if (acc.includes("mullet")) { fill("#d98a2a", () => c.arc(0, -42, 38, Math.PI, 0)); fill("#d98a2a", () => { c.moveTo(-34, -30); c.quadraticCurveTo(-56, 20, -40, 30); c.lineTo(-30, -10); }); }
    if (acc.includes("headband")) rect("#ff4fd8", -42, -44, 84, 8);
    if (acc.includes("hoodie")) stroke("#5a6b7a", 10, () => c.arc(0, -10, 50, Math.PI * .9, Math.PI * 2.1));
    if (acc.includes("beanie")) { fill("#2f6f4f", () => c.arc(0, -44, 38, Math.PI, 0)); rect("#24563d", -40, -50, 80, 10); circle("#e8e8e8", 0, -84, 8); }
    if (acc.includes("capback")) { fill("#1d5fa8", () => c.arc(0, -46, 36, Math.PI, 0)); rect("#174a85", -48, -50, 22, 7); }
    if (acc.includes("beret")) ellipse("#222", 6, -52, 38, 12, .15);
    if (acc.includes("fedora")) { ellipse("#3a3a3a", 0, -52, 54, 8); fill("#3a3a3a", () => { c.moveTo(-30, -52); c.lineTo(-26, -84); c.quadraticCurveTo(0, -74, 26, -84); c.lineTo(30, -52); }); rect("#8a1a1f", -30, -60, 60, 7); }
    if (acc.includes("wildhair")) for (let k = 0; k < 9; k++) stroke("#eee", 4, () => { c.moveTo(-30 + k * 7.5, -50); c.lineTo(-40 + k * 10 + Math.sin(t * 6 + k) * 5, -82 - (k % 3) * 6); });
    if (acc.includes("nightcap")) { fill("#3f6fd8", () => { c.moveTo(-36, -46); c.quadraticCurveTo(10, -120, 60, -60 + Math.sin(t) * 6); c.lineTo(36, -46); }); circle("#fff", 60, -60 + Math.sin(t) * 6, 8); rect("#fff", -38, -50, 76, 8); }
    if (acc.includes("straw")) { ellipse("#e8c66a", 0, -50, 58, 10); fill("#e8c66a", () => c.ellipse(0, -54, 28, 22, 0, Math.PI, 0)); rect("#c0262b", -28, -58, 56, 5); }
    if (acc.includes("cowboy")) { fill("#8a5a2a", () => { c.moveTo(-62, -54); c.quadraticCurveTo(0, -36, 62, -54); c.quadraticCurveTo(0, -44, -62, -54); }); fill("#8a5a2a", () => { c.moveTo(-28, -50); c.lineTo(-24, -88); c.quadraticCurveTo(0, -76, 24, -88); c.lineTo(28, -50); }); }
  }

  // ---------- the stage ----------
  let canvas, low, theme = THEMES[0], name = "", playing = null, raf = 0, last = 0, clock = 0;
  let bare = false, fixed = null;    // bare: just the band, no backdrop (on top of a game's own scene). fixed: one band, not taking turns
  let ctx, analyser, bins, avg = 0, pulse = 0;
  const sources = new WeakMap();

  function listenTo(audio) {
    try {
      ctx = ctx || new (window.AudioContext || window.webkitAudioContext)();
      if (!analyser) { analyser = ctx.createAnalyser(); analyser.fftSize = 1024; analyser.smoothingTimeConstant = .6; analyser.connect(ctx.destination); bins = new Uint8Array(analyser.frequencyBinCount); }
      if (!sources.has(audio)) { const s = ctx.createMediaElementSource(audio); s.connect(analyser); sources.set(audio, s); }
      if (ctx.state === "suspended") ctx.resume();
    } catch (e) { analyser = null; }    // the band still plays, just to its own beat
  }

  function beatNow(dt) {
    const an = playing && playing.getByteFrequencyData ? playing : analyser;    // a page's own analyser, or ours on a song
    if (playing && an && !playing.paused) {
      if (!bins || bins.length !== an.frequencyBinCount) bins = new Uint8Array(an.frequencyBinCount);
      an.getByteFrequencyData(bins);
      let bass = 0; for (let k = 1; k < 10; k++) bass += bins[k]; bass /= 9 * 255;
      avg = avg * .95 + bass * .05;
      if (bass > avg * 1.12 + .02) pulse = Math.min(1, pulse + (bass - avg) * 4);
    } else {
      const bpm = theme.calm ? 70 : 112, ph = (clock * bpm / 60) % 1;
      if (ph < dt * bpm / 60) pulse = theme.calm ? .4 : .8;
    }
    pulse *= Math.pow(.02, dt);
    return pulse;
  }

  // one picture of the band: drawn on out (a 16:9 canvas), through the small canvas low for the pixel themes
  function scene(out, low, th, t, beat, noBack) {
    const target = th.pixel ? low : out;
    c = target.getContext("2d");
    if (noBack) { c.clearRect(0, 0, target.width, target.height); if (th.pixel) out.getContext("2d").clearRect(0, 0, out.width, out.height); }
    c.save(); c.scale(target.width / W, target.height / H);
    if (!noBack) BG[th.bg](t, beat);
    const xs = [150, 370, 590, 810];
    th.band.forEach((m, i) => { c.save(); c.translate(xs[i], GROUND); c.scale(1.3, 1.3); c.translate(-xs[i], -GROUND); raisin(m, xs[i], t, beat, th, i); c.restore(); });
    c.restore();
    if (th.pixel) { const o = out.getContext("2d"); o.imageSmoothingEnabled = false; o.drawImage(low, 0, 0, out.width, out.height); }
  }

  // cover art for a song: the band dressed for its genre, the song's name above, the Jukebox below. A square JPEG, as a data link.
  function cover(genre, title, by) {
    const th = themeFor(genre), S = 1000;
    const pic = document.createElement("canvas"); pic.width = W; pic.height = H;
    const small = document.createElement("canvas"); small.width = W / 6; small.height = H / 6;
    scene(pic, small, th, 2.1, .7);
    const art = document.createElement("canvas"); art.width = art.height = S;
    const a = art.getContext("2d");
    const g = a.createLinearGradient(0, 0, 0, S); g.addColorStop(0, "#3b1408"); g.addColorStop(1, "#7a2a12"); a.fillStyle = g; a.fillRect(0, 0, S, S);
    a.drawImage(pic, 0, 0, W, H, 0, 230, S, S * H / W);
    a.strokeStyle = "#c98a2e"; a.lineWidth = 10; a.strokeRect(5, 230, S - 10, S * H / W);
    a.textAlign = "center"; a.fillStyle = "#ffd23f"; a.shadowColor = "#ff9a2e"; a.shadowBlur = 18;
    let size = 96; a.font = `900 ${size}px "Trebuchet MS", sans-serif`;
    while (a.measureText(title).width > S - 80 && size > 40) { size -= 4; a.font = `900 ${size}px "Trebuchet MS", sans-serif`; }
    a.fillText(title, S / 2, 150);
    a.shadowBlur = 0; a.fillStyle = "#38f2ff"; a.font = "700 34px 'Courier New', monospace";
    a.fillText(`${by} · ${genre}`, S / 2, 205);
    a.fillStyle = "#fff8e6"; a.font = "700 30px 'Courier New', monospace";
    a.fillText("starring " + th.name, S / 2, 860);
    a.fillStyle = "#ffd23f"; a.font = "900 40px 'Courier New', monospace";
    a.fillText("RANDIS SHOP JUKEBOX", S / 2, 930); a.fillStyle = "#fff8e6"; a.font = "700 26px 'Courier New', monospace"; a.fillText("royalty-free music", S / 2, 968);
    return art.toDataURL("image/jpeg", .9);
  }

  function frame(now) {
    if (!canvas || !canvas.isConnected) { raf = 0; return; }
    raf = requestAnimationFrame(frame);
    const dt = Math.min(.1, last ? (now - last) / 1000 : .016); last = now; clock += dt;
    if (!playing && fixed) theme = fixed;
    else if (!playing) { const k = Math.floor(clock / 7) % THEMES.length; if (THEMES[k] !== theme) theme = THEMES[k]; }
    scene(canvas, low, theme, clock, beatNow(dt), bare);
    const cap = canvas.parentNode && canvas.parentNode.querySelector(".band-cap");
    const text = playing ? `Now playing: ${name}, by ${theme.name}` : `Rehearsing: ${theme.name}. Press play on a song.`;
    if (cap && cap.textContent !== text) cap.textContent = text;
  }

  return {
    themeFor, THEMES, cover,
    get theme() { return theme.id; },
    // the stage: a canvas and its caption. stage({bare: true}) is just the band, no backdrop or caption, to stand in a game's scene.
    stage(opts) {
      bare = !!(opts && opts.bare);
      canvas = document.createElement("canvas"); canvas.width = W; canvas.height = H; canvas.className = "band-stage";
      canvas.setAttribute("role", "img"); canvas.setAttribute("aria-label", "The Raisin Band playing along");
      low = document.createElement("canvas"); low.width = W / 6; low.height = H / 6;
      const box = document.createElement("div"); box.className = "band";
      const cap = document.createElement("div"); cap.className = "band-cap";
      box.append(canvas);
      if (!bare) box.append(cap);
      if (!raf) raf = requestAnimationFrame(frame);
      return box;
    },
    // source: an <audio> element, or an AnalyserNode the page already has on its own sound (Randis Sound Forge)
    play(source, genre, title) { if (!source.getByteFrequencyData) listenTo(source); if (playing !== source) avg = 0; playing = source; theme = themeFor(genre); name = title; },
    stop(audio) { if (playing === audio) playing = null; },
    // one band for when nothing is playing, instead of taking turns: dress("Calypso")
    dress(genre) { fixed = themeFor(genre); if (!playing) theme = fixed; },
  };
})();
