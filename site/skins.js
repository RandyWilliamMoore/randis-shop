// The Randis Shop's skins, theme music, Commander Randis (StarCraft II skin) and fake ads. Randis UDS™ by Randy Moore. Original: https://github.com/RandyWilliamMoore/randis-uds · Support: https://ko-fi.com/moorescombinatoricsmatrix
// Made from the Randis UDS Shop tab (ui/shop.js, shopaudio.js, shopfx.js, shopads.js). Music is made live in code, no recordings;
// Randis's six lines are Randy's own recordings, loaded from site/randis_lines.js the first time he speaks. Nothing is tracked:
// the skin, the sound settings and the ads switch are kept in this browser only.
"use strict";
(function () {
const mk = (tag, props = {}, text = "") => { const e = Object.assign(document.createElement(tag), props); if (text) e.textContent = text; return e; };
const SHOP_RANDIS_LINES = {"help": {"text": "How can I help you?"}, "nottoday": {"text": "Not today, sir."}, "scared": {"text": "AH! You scared me!"}, "confirmed": {"text": "Confirmed."}, "hello": {"text": "Hello there!"}, "yes": {"text": "Yes?"}};
let wavs = null;
const skWavs = () => wavs || (wavs = new Promise((ok, no) => { const s = document.createElement("script"); s.src = "site/randis_lines.js"; s.onload = ok; s.onerror = no; document.head.appendChild(s); }));
"use strict";
const SFX = (function () { const SFX = {};
SFX.FX={
  eq:{l:'Equalizer',p:{low:[0,-18,18,.5,'Low (250 Hz)','dB'],mid:[0,-18,18,.5,'Mid','dB'],midF:[1500,300,6000,10,'Mid frequency','Hz'],high:[0,-18,18,.5,'High (5 kHz)','dB']}},
  filter:{l:'Filter',p:{mode:[['lowpass','highpass','bandpass','notch'],'Type'],freq:[3000,50,12000,10,'Frequency','Hz'],q:[.7,.1,20,.1,'Resonance']}},
  pitch:{l:'Pitch shifter',p:{semi:[0,-24,24,.1,'Shift','st'],mix:[1,0,1,.01,'Mix']}},
  ring:{l:'Robot (ring mod)',p:{freq:[60,1,2000,1,'Frequency','Hz'],mix:[.6,0,1,.01,'Mix']}},
  crush:{l:'Bit crusher',p:{bits:[8,1,16,1,'Bits'],down:[2,1,32,1,'Downsample'],mix:[1,0,1,.01,'Mix']}},
  drive:{l:'Distortion',p:{amount:[.3,0,1,.01,'Drive'],mix:[1,0,1,.01,'Mix']}},
  chorus:{l:'Chorus',p:{rate:[.8,.05,8,.01,'Rate','Hz'],depth:[6,.5,25,.1,'Depth','ms'],mix:[.5,0,1,.01,'Mix']}},
  flanger:{l:'Flanger',p:{rate:[.3,.05,5,.01,'Rate','Hz'],depth:[3,.2,10,.1,'Depth','ms'],fb:[.6,0,.95,.01,'Feedback'],mix:[.5,0,1,.01,'Mix']}},
  tremolo:{l:'Tremolo',p:{rate:[6,.1,30,.1,'Rate','Hz'],depth:[.5,0,1,.01,'Depth']}},
  echo:{l:'Echo',p:{time:[250,10,1500,1,'Time','ms'],fb:[.35,0,.95,.01,'Repeats'],mix:[.3,0,1,.01,'Level']}},
  reverb:{l:'Reverb',p:{size:[.6,0,1,.01,'Room size'],damp:[.4,0,1,.01,'Damping'],mix:[.25,0,1,.01,'Mix']}},
  radio:{l:'Radio / phone',p:{low:[300,50,2000,10,'Low cut','Hz'],high:[3400,800,8000,10,'High cut','Hz'],grit:[.3,0,1,.01,'Grit'],noise:[.02,0,.2,.001,'Static']}},
  comp:{l:'Compressor',p:{thresh:[-18,-60,0,.5,'Threshold','dB'],ratio:[4,1,20,.1,'Ratio'],makeup:[6,0,24,.5,'Makeup','dB']}},
  gain:{l:'Gain',p:{db:[0,-24,24,.5,'Gain','dB']}}
};
SFX.fxDefaults=function(type){var d={type:type,on:true},p=(SFX.FX[type]||{p:{}}).p;for(var k in p){var v=p[k][0];d[k]=Array.isArray(v)?v[0]:v}return d};
function biq(type,f,q,g,sr){var A=Math.pow(10,g/40),w=2*Math.PI*Math.min(Math.max(f,10),sr*.49)/sr,cs=Math.cos(w),sn=Math.sin(w),al=sn/(2*q),b0,b1,b2,a0,a1,a2,s;
  switch(type){case 'lowpass':b0=(1-cs)/2;b1=1-cs;b2=b0;a0=1+al;a1=-2*cs;a2=1-al;break;case 'highpass':b0=(1+cs)/2;b1=-(1+cs);b2=b0;a0=1+al;a1=-2*cs;a2=1-al;break;
    case 'bandpass':b0=al;b1=0;b2=-al;a0=1+al;a1=-2*cs;a2=1-al;break;case 'notch':b0=1;b1=-2*cs;b2=1;a0=1+al;a1=-2*cs;a2=1-al;break;
    case 'peak':b0=1+al*A;b1=-2*cs;b2=1-al*A;a0=1+al/A;a1=-2*cs;a2=1-al/A;break;
    case 'lowshelf':s=2*Math.sqrt(A)*al;b0=A*((A+1)-(A-1)*cs+s);b1=2*A*((A-1)-(A+1)*cs);b2=A*((A+1)-(A-1)*cs-s);a0=(A+1)+(A-1)*cs+s;a1=-2*((A-1)+(A+1)*cs);a2=(A+1)+(A-1)*cs-s;break;
    default:s=2*Math.sqrt(A)*al;b0=A*((A+1)+(A-1)*cs+s);b1=-2*A*((A-1)+(A+1)*cs);b2=A*((A+1)+(A-1)*cs-s);a0=(A+1)-(A-1)*cs+s;a1=2*((A-1)-(A+1)*cs);a2=(A+1)-(A-1)*cs-s}
  b0/=a0;b1/=a0;b2/=a0;a1/=a0;a2/=a0;var x1=0,x2=0,z1=0,z2=0;
  return function(x){var y=b0*x+b1*x1+b2*x2-a1*z1-a2*z2;x2=x1;x1=x;z2=z1;z1=y;return y}}
function dline(n){var L=n+4,b=new Float32Array(L),w=0;return{push:function(x){b[w]=x;w=(w+1)%L},read:function(d){var r=w-1-d;while(r<0)r+=L;var i=Math.floor(r),f=r-i;return b[i%L]*(1-f)+b[(i+1)%L]*f}}}
SFX.fxProc=function(fx,sr){var q=Object.assign(SFX.fxDefaults(fx.type),fx),mx=function(a,b,m){return a*(1-m)+b*m},t=0,w;
  switch(fx.type){
    case 'eq':{var e1=biq('lowshelf',250,.707,q.low,sr),e2=biq('peak',q.midF,1,q.mid,sr),e3=biq('highshelf',5000,.707,q.high,sr);return function(x){return e3(e2(e1(x)))}}
    case 'filter':return biq(q.mode,q.freq,q.q,0,sr);
    case 'pitch':{var ratio=Math.pow(2,q.semi/12),W=Math.round(sr*.06),L=dline(W*2),ph=0;return function(x){L.push(x);ph+=(1-ratio)/W;ph-=Math.floor(ph);var p2=(ph+.5)%1;
      return mx(x,L.read(ph*W)*(.5-.5*Math.cos(2*Math.PI*ph))+L.read(p2*W)*(.5-.5*Math.cos(2*Math.PI*p2)),q.mix)}}
    case 'ring':w=2*Math.PI*q.freq/sr;return function(x){t+=w;if(t>6.283185307)t-=6.283185307;return mx(x,x*Math.sin(t)*1.4,q.mix)};
    case 'crush':{var lv=Math.pow(2,q.bits-1),c=0,hold=0,dn=Math.max(1,Math.round(q.down));return function(x){if(c++%dn===0)hold=Math.round(x*lv)/lv;return mx(x,hold,q.mix)}}
    case 'drive':{var kk=1+q.amount*30,nn=Math.tanh(kk)*Math.sqrt(kk);return function(x){return mx(x,Math.tanh(x*kk)/nn,q.mix)}}
    case 'chorus':{var L2=dline(Math.ceil(sr*.07)),bs=sr*.015,dp=sr*q.depth/2000;w=2*Math.PI*q.rate/sr;return function(x){L2.push(x);t+=w;
      return mx(x,.5*L2.read(bs+dp*(1+Math.sin(t)))+.5*L2.read(bs+dp*(1+Math.sin(t+2.1))),q.mix)}}
    case 'flanger':{var L3=dline(Math.ceil(sr*.03)),dp3=sr*q.depth/1000,fbk=0;w=2*Math.PI*q.rate/sr;return function(x){L3.push(x+fbk*q.fb);t+=w;var y=L3.read(1+dp3*(.5+.5*Math.sin(t)));fbk=y;return x*(1-q.mix*.5)+y*q.mix*.5}}
    case 'tremolo':w=2*Math.PI*q.rate/sr;return function(x){t+=w;return x*(1-q.depth*(.5+.5*Math.sin(t)))};
    case 'echo':{var ne=Math.max(1,Math.round(sr*q.time/1000)),L4=dline(ne+2);return function(x){var d=L4.read(ne-1);L4.push(x+d*q.fb);return x+d*q.mix}}
    case 'reverb':{var s=sr/44100,fk=.7+.27*q.size,dm=q.damp*.45;
      var combs=[1116,1188,1277,1356,1422,1491,1557,1617].map(function(l){return{b:new Float32Array(Math.max(8,Math.round(l*s*(.45+q.size*.75)))),i:0,f:0}});
      var aps=[556,441,341,225].map(function(l){return{b:new Float32Array(Math.max(4,Math.round(l*s))),i:0}});
      return function(x){var o=0,inp=x*.12;for(var j=0;j<8;j++){var cb=combs[j],y=cb.b[cb.i];cb.f=y*(1-dm)+cb.f*dm;cb.b[cb.i]=inp+cb.f*fk;cb.i=(cb.i+1)%cb.b.length;o+=y}
        for(j=0;j<4;j++){var a=aps[j],bo=a.b[a.i];a.b[a.i]=o+bo*.5;o=bo-o;a.i=(a.i+1)%a.b.length}return x*(1-q.mix*.5)+o*q.mix*1.2}}
    case 'radio':{var h1=biq('highpass',q.low,.8,0,sr),h2=biq('highpass',q.low,.8,0,sr),l1=biq('lowpass',q.high,.8,0,sr),l2=biq('lowpass',q.high,.8,0,sr),kr=1+q.grit*8,nr=Math.tanh(kr),seed=12345;
      return function(x){seed=(Math.imul(seed,1103515245)+12345)>>>0;var nz=(seed/4294967296*2-1)*q.noise;return l2(l1(h2(h1(Math.tanh(x*kr)/nr+nz))))}}
    case 'comp':{var env=0,at=Math.exp(-1/(sr*.005)),rl=Math.exp(-1/(sr*.12)),mk=Math.pow(10,q.makeup/20);return function(x){var a=Math.abs(x);env=a>env?at*env+(1-at)*a:rl*env+(1-rl)*a;
      var db=20*Math.log(env+1e-9)/Math.LN10,g=db>q.thresh?Math.pow(10,(q.thresh-db)*(1-1/q.ratio)/20):1;return x*g*mk}}
    case 'gain':{var gg=Math.pow(10,q.db/20);return function(x){return x*gg}}}
  return function(x){return x}};
function fxTail(list){var t=0;(list||[]).forEach(function(f){if(f.on===false)return;var q=Object.assign(SFX.fxDefaults(f.type),f);
  if(f.type==='echo')t+=q.time/1000*Math.min(12,Math.log(.01)/Math.log(Math.max(.05,q.fb))+1);if(f.type==='reverb')t+=.4+2.2*q.size});return Math.min(t,15)}
SFX.applyFx=function(x,list,sr){list=(list||[]).filter(function(f){return f&&f.on!==false&&SFX.FX[f.type]});if(!list.length)return x;
  var tail=Math.round(fxTail(list)*sr),out=new Float32Array(x.length+tail),procs=list.map(function(f){return SFX.fxProc(f,sr)});
  for(var i=0;i<out.length;i++){var v=i<x.length?x[i]:0;for(var j=0;j<procs.length;j++)v=procs[j](v);out[i]=isFinite(v)?v:0}
  var e=out.length;while(e>x.length&&Math.abs(out[e-1])<2e-4)e--;return e<out.length?out.slice(0,e):out};
return SFX; })();

"use strict";

const SHOP_SOUND = (function () {
  // ---------- settings ----------
  const PRESETS = {
    holo: { name: "Hologram (digitized)", chain: [{ type: "radio", low: 220, high: 5200, grit: .25, noise: .008 }, { type: "crush", bits: 9, down: 3, mix: .45 }, { type: "flanger", rate: .25, depth: 1.2, fb: .4, mix: .22 }, { type: "ring", freq: 55, mix: .12 }, { type: "comp", thresh: -22, ratio: 4, makeup: 7 }] },
    comms: { name: "Comms radio", chain: [{ type: "radio", low: 330, high: 3300, grit: .38, noise: .014 }, { type: "crush", bits: 12, down: 2, mix: .3 }, { type: "comp", thresh: -22, ratio: 4, makeup: 7 }] },
    android: { name: "Android", chain: [{ type: "ring", freq: 110, mix: .42 }, { type: "crush", bits: 8, down: 2, mix: .5 }, { type: "chorus", rate: .5, depth: 4, mix: .35 }, { type: "comp", thresh: -20, ratio: 4, makeup: 6 }] },
    relay: { name: "Deep-space relay", chain: [{ type: "radio", low: 400, high: 2800, grit: .5, noise: .035 }, { type: "crush", bits: 7, down: 4, mix: .35 }, { type: "echo", time: 140, fb: .25, mix: .2 }, { type: "comp", thresh: -22, ratio: 5, makeup: 8 }] },
    glitch: { name: "Glitchy AI", chain: [{ type: "crush", bits: 6, down: 5, mix: .4 }, { type: "tremolo", rate: 14, depth: .25 }, { type: "ring", freq: 200, mix: .2 }, { type: "radio", low: 180, high: 6000, grit: .2, noise: .006 }, { type: "comp", thresh: -20, ratio: 4, makeup: 6 }] },
    clean: { name: "Clean (no effects)", chain: [] },
  };
  const full = c => c.map(f => Object.assign(SFX.fxDefaults(f.type), f));
  const DEF = { music: false, mvol: .5, tempo: 1, bright: .75, echo: .25, verb: .3, randis: true, voice: true, vgain: 1.2, fxOn: true, squelch: true, preset: "holo", chain: full(PRESETS.holo.chain) };
  let S;
  try { S = Object.assign({}, DEF, JSON.parse(localStorage.getItem("udsShopSound") || "{}")); } catch (e) { S = Object.assign({}, DEF); }
  if (!Array.isArray(S.chain)) S.chain = full(PRESETS.holo.chain);
  const save = () => localStorage.setItem("udsShopSound", JSON.stringify(S));

  let AC = null;
  const ctx = () => { AC = AC || new (window.AudioContext || window.webkitAudioContext)(); if (AC.state === "suspended") AC.resume(); return AC; };

  // ---------- theme music: one original loop per skin, made live ----------
  const SC = { maj: [0, 2, 4, 5, 7, 9, 11], min: [0, 2, 3, 5, 7, 8, 10], dor: [0, 2, 3, 5, 7, 9, 10], phr: [0, 1, 3, 5, 7, 8, 10], lyd: [0, 2, 4, 6, 7, 9, 11], hmin: [0, 2, 3, 5, 7, 8, 11] };
  const DR = {
    none: ["", "", ""],
    lofi: ["x.....x...x.....", "....x.......x...", "x.x.x.x.x.x.x.x."],
    four: ["x...x...x...x...", "....x.......x...", "..x...x...x...x."],
    pop: ["x...x...x...x...", "....x.......x...", "xxxxxxxxxxxxxxxx"],
    brk: ["x.x.......xx....", "....x..x.x..x..x", "x.x.x.x.x.x.x.x."],
    march: ["x.......x.......", "....x.......x.xx", "x...x...x...x..."],
    swing: ["x.......x.......", "....x.......x...", "x..xx..xx..xx..x"],
    boom: ["x.........x.....", "........x.......", ""],
    metal: ["xxxxxxxxxxxxxxxx", "....x.......x...", "x.x.x.x.x.x.x.x."],
    bossa: ["x..x....x..x....", "..x..x....x..x..", "x.x.x.x.x.x.x.x."],
    light: ["x.......x.......", "....x.......x...", "..x...x...x...x."],
    shuffle: ["x.....x.x.......", "....x.......x...", "x.xx.xx.xx.xx.xx"],
    pulse: ["x.......x.......", "", ""],
  };
  // bpm, root (MIDI), scale, chords (scale steps), lead {w: wave, p: pattern, o: octave}, pad wave, bass, drums, extra, track name
  const MUSIC = {
    default: { bpm: 84, root: 57, sc: "maj", prog: [0, 5, 3, 4], lead: { w: "sine", p: "sparse", o: 2 }, pad: "triangle", bass: "root4", dr: "none", name: "Blank Canvas" },
    steam: { bpm: 78, root: 50, sc: "dor", prog: [0, 3, 6, 4], lead: { w: "epiano", p: "melody", o: 2 }, pad: "triangle", bass: "root8", dr: "lofi", vinyl: 1, swing: .18, name: "Library Sale Lo-Fi" },
    sc2: { bpm: 72, root: 45, sc: "phr", prog: [0, 0, 5, 6], lead: { w: "brass", p: "sparse", o: 1 }, pad: "sawdark", bass: "pulse16", dr: "boom", name: "Orbital Command" },
    halo: { bpm: 60, root: 50, sc: "min", prog: [0, 5, 2, 6], lead: { w: "choir", p: "chant", o: 2 }, pad: "choir", bass: "none", dr: "none", verbBoost: .4, name: "Monastery Ring" },
    hl: { bpm: 132, root: 40, sc: "min", prog: [0, 0, 5, 6], lead: { w: "square", p: "stabs", o: 2 }, pad: "none", bass: "syncop", dr: "brk", dist: .4, name: "Resonance Cascade Breaks" },
    temple: { bpm: 104, root: 60, sc: "maj", prog: [0, 3, 4, 0], lead: { w: "square", p: "hymn", o: 1 }, pad: "none", bass: "none", dr: "none", dry: 1, name: "PC Speaker Hymn No. 7" },
    win95: { bpm: 100, root: 60, sc: "maj", prog: [0, 5, 3, 4], lead: { w: "triangle", p: "melody", o: 1 }, pad: "none", bass: "oompah", bassW: "square", dr: "light", name: "CANYON_NOT.MID" },
    xp: { bpm: 74, root: 53, sc: "lyd", prog: [0, 1, 0, 4], lead: { w: "bell", p: "sparse", o: 2 }, pad: "lush", bass: "root4", dr: "none", name: "Rolling Hills Screensaver" },
    mac9: { bpm: 116, root: 53, sc: "dor", prog: [1, 4, 0, 5], seventh: 1, lead: { w: "vibes", p: "melody", o: 2 }, pad: "none", bass: "walk", bassW: "triangle", dr: "swing", swing: .3, name: "Platinum Lounge" },
    macos: { bpm: 88, root: 55, sc: "maj", prog: [0, 3, 5, 4], seventh: 1, lead: { w: "bell", p: "sparse", o: 2 }, pad: "lush", bass: "root4", dr: "lofi", swing: .12, name: "Frosted Glass" },
    material: { bpm: 100, root: 60, sc: "maj", prog: [0, 4, 5, 3], lead: { w: "marimba", p: "melody", o: 1 }, pad: "none", bass: "root8", bassW: "triangle", dr: "light", name: "Elevation 2dp" },
    matrix: { bpm: 128, root: 45, sc: "phr", prog: [0, 0, 1, 0], lead: { w: "saw", p: "sparse", o: 2 }, pad: "sawdark", bass: "acid", dr: "four", name: "Follow the White Rabbit (Not That One)" },
    lcars: { bpm: 60, root: 48, sc: "lyd", prog: [0, 1, 0, 6], lead: { w: "beep", p: "beep", o: 3 }, pad: "hum", bass: "none", dr: "none", name: "Bridge Ambience, Deck 1" },
    pipboy: { bpm: 96, root: 55, sc: "maj", prog: [0, 5, 1, 4], seventh: 1, lead: { w: "triangle", p: "melody", o: 2 }, pad: "none", bass: "walk", bassW: "triangle", dr: "swing", swing: .3, vinyl: 2, radio: 1, name: "Atomic Sweetheart Swing" },
    tron: { bpm: 120, root: 45, sc: "min", prog: [0, 5, 3, 4], lead: { w: "saw", p: "arp", o: 2 }, pad: "saw", bass: "pulse16", dr: "four", name: "End of Line Arpeggio" },
    jarvis: { bpm: 86, root: 50, sc: "lyd", prog: [0, 4, 1, 4], lead: { w: "sine", p: "arp", o: 3 }, pad: "lush", bass: "root4", dr: "pulse", name: "Systems Nominal" },
    cyber: { bpm: 100, root: 38, sc: "phr", prog: [0, 0, 5, 1], lead: { w: "saw", p: "stabs", o: 2 }, pad: "sawdark", bass: "pulse16", dr: "four", dist: .5, name: "Night City Overdrive" },
    comic: { bpm: 140, root: 60, sc: "maj", prog: [0, 3, 4, 0], lead: { w: "square", p: "melody", o: 1 }, pad: "none", bass: "oompah", bassW: "triangle", dr: "march", name: "Meanwhile, Back at the Shop!" },
    geocities: { bpm: 126, root: 62, sc: "maj", prog: [0, 4, 5, 3], lead: { w: "square", p: "arp", o: 1 }, pad: "none", bass: "root8", bassW: "square", dr: "four", name: "under_construction.mid" },
    vaporwave: { bpm: 64, root: 52, sc: "maj", prog: [3, 2, 1, 4], seventh: 1, lead: { w: "epiano", p: "sparse", o: 2 }, pad: "lush", bass: "root4", dr: "lofi", swing: .2, slow: 1, name: "Ｍａｌｌ Ｓｏｆｔ Ｐｌａｙ" },
    bloomberg: { bpm: 96, root: 55, sc: "maj", prog: [0, 1, 3, 4], seventh: 1, lead: { w: "epiano", p: "melody", o: 2 }, pad: "none", bass: "root4", bassW: "triangle", dr: "bossa", name: "Hold Music (Your Call Is Important)" },
    bios: { bpm: 90, root: 72, sc: "maj", prog: [0, 0, 0, 0], lead: { w: "square", p: "beep", o: 0 }, pad: "none", bass: "none", dr: "none", dry: 1, name: "POST Beeps" },
    doom: { bpm: 152, root: 40, sc: "phr", prog: [0, 0, 1, 5], lead: { w: "saw", p: "stabs", o: 2 }, pad: "none", bass: "chug", dr: "metal", dist: .9, name: "Rip and Shop" },
    minecraft: { bpm: 68, root: 55, sc: "maj", prog: [0, 3, 0, 4], lead: { w: "piano", p: "sparse", o: 2 }, pad: "none", bass: "none", dr: "none", verbBoost: .3, name: "Quiet Biome" },
    wii: { bpm: 118, root: 60, sc: "maj", prog: [0, 5, 1, 4], seventh: 1, lead: { w: "marimba", p: "melody", o: 1 }, pad: "none", bass: "walk", bassW: "triangle", dr: "shuffle", swing: .25, name: "Menu Channel Shuffle" },
    xmb: { bpm: 60, root: 50, sc: "maj", prog: [0, 4, 5, 3], lead: { w: "bell", p: "sparse", o: 3 }, pad: "lush", bass: "none", dr: "none", verbBoost: .3, name: "Wave Background" },
    netflix: { bpm: 70, root: 41, sc: "min", prog: [0, 5, 3, 6], lead: { w: "piano", p: "sparse", o: 2 }, pad: "sawdark", bass: "root4", dr: "boom", name: "Are You Still Shopping?" },
    barbie: { bpm: 122, root: 62, sc: "maj", prog: [0, 4, 5, 3], lead: { w: "square", p: "melody", o: 1 }, pad: "saw", bass: "root8", dr: "pop", name: "Pink Convertible" },
  };
  const hz = m => 440 * Math.pow(2, (m - 69) / 12);
  function rng(seed) { let s = seed >>> 0; return () => { s = (Math.imul(s, 1664525) + 1013904223) >>> 0; return s / 4294967296; }; }
  const seedOf = t => [...t].reduce((h, c) => (Math.imul(h, 31) + c.charCodeAt(0)) >>> 0, 7);

  // a song: 4 bars of 16 steps, lead notes as [step, scale degree, length in steps]
  function compose(id, M) {
    const r = rng(seedOf(id)), notes = [];
    const chord = b => M.prog[b % M.prog.length];
    if (M.lead.p === "melody" || M.lead.p === "hymn" || M.lead.p === "chant") {
      const rhythms = M.lead.p === "hymn" ? [[0, 4, 8, 12]] : M.lead.p === "chant" ? [[0, 8], [0, 4, 8]] : [[0, 3, 6, 8, 12], [0, 2, 4, 6, 8, 12, 14], [0, 4, 6, 8, 10, 12], [0, 3, 6, 10, 12, 14]];
      const motif = rhythms[Math.floor(r() * rhythms.length)];
      let deg = chord(0) + 7;
      for (let b = 0; b < 4; b++) {
        const rh = b === 2 ? motif : (b === 3 ? rhythms[Math.floor(r() * rhythms.length)] : motif);
        rh.forEach((st, k) => {
          const toChord = st % 8 === 0;
          if (toChord) { let c = chord(b) + 7 + [0, 2, 4][Math.floor(r() * 3)]; while (c - deg > 3) c -= 7; while (deg - c > 3) c += 7; deg = c; }
          else deg += [-2, -1, -1, 1, 1, 2][Math.floor(r() * 6)];
          deg = Math.max(3, Math.min(14, deg));
          if (b === 3 && k === rh.length - 1) deg = 7;
          const next = rh[k + 1] != null ? rh[k + 1] : 16;
          notes.push([b * 16 + st, deg, next - st]);
        });
      }
    } else if (M.lead.p === "sparse") {
      for (let b = 0; b < 4; b++) { const n = 2 + Math.floor(r() * 2), used = new Set(); for (let i = 0; i < n; i++) { let st = [0, 4, 6, 8, 10, 12][Math.floor(r() * 6)]; if (used.has(st)) continue; used.add(st); notes.push([b * 16 + st, chord(b) + 7 + [0, 2, 4, 7][Math.floor(r() * 4)], 6]); } }
    } else if (M.lead.p === "arp") {
      const shape = [0, 2, 4, 7, 9, 7, 4, 2];
      for (let b = 0; b < 64; b++) notes.push([b, chord(Math.floor(b / 16)) + shape[b % 8], 1]);
    } else if (M.lead.p === "stabs") {
      const pat = [[2, 6, 10, 14], [3, 6, 11, 14], [0, 3, 10]][Math.floor(r() * 3)];
      for (let b = 0; b < 4; b++) pat.forEach(st => notes.push([b * 16 + st, chord(b) + 7, 1, 1]));
    } else if (M.lead.p === "beep") {
      for (let b = 0; b < 4; b++) for (let i = 0; i < 3; i++) if (r() < .7) notes.push([b * 16 + Math.floor(r() * 16), 7 + Math.floor(r() * 8), 1]);
    }
    return notes;
  }

  let M = null, song = [], step = 0, nextT = 0, timer = 0, bus = null, curId = "", alive = () => false;
  let noise = null;
  function noiseBuf(c) { if (noise) return noise; noise = c.createBuffer(1, c.sampleRate, c.sampleRate); const d = noise.getChannelData(0); for (let i = 0; i < d.length; i++) d[i] = Math.random() * 2 - 1; return noise; }
  function impulse(c, secs) { const n = Math.round(c.sampleRate * secs), b = c.createBuffer(2, n, c.sampleRate); for (let ch = 0; ch < 2; ch++) { const d = b.getChannelData(ch); for (let i = 0; i < n; i++) d[i] = (Math.random() * 2 - 1) * Math.pow(1 - i / n, 3); } return b; }
  function curve(k) { const n = 1024, c = new Float32Array(n); for (let i = 0; i < n; i++) { const x = i / n * 2 - 1; c[i] = Math.tanh(x * (1 + k * 20)) / Math.tanh(1 + k * 20); } return c; }

  function makeBus() {
    const c = ctx(), b = {};
    b.in = c.createGain(); b.dist = c.createWaveShaper(); b.tone = c.createBiquadFilter(); b.out = c.createGain();
    b.tone.type = "lowpass"; b.dly = c.createDelay(2); b.fb = c.createGain(); b.dlyOut = c.createGain(); b.rev = c.createConvolver(); b.revOut = c.createGain();
    b.rev.buffer = impulse(c, 2.8);
    b.in.connect(b.dist); b.dist.connect(b.tone); b.tone.connect(b.out);
    b.tone.connect(b.dly); b.dly.connect(b.fb); b.fb.connect(b.dly); b.dly.connect(b.dlyOut); b.dlyOut.connect(b.out);
    b.tone.connect(b.rev); b.rev.connect(b.revOut); b.revOut.connect(b.out);
    b.drums = c.createGain(); b.drums.connect(b.out);
    b.out.connect(c.destination);
    return b;
  }
  function busSet() {
    if (!bus || !M) return;
    const c = ctx(), t = c.currentTime;
    bus.out.gain.setTargetAtTime(S.music ? S.mvol * .55 : 0, t, .1);
    const radio = M.radio ? 2600 : 18000;
    bus.tone.frequency.setTargetAtTime(Math.min(radio, 400 * Math.pow(45, S.bright)), t, .05);
    bus.dist.curve = M.dist ? curve(M.dist) : null;
    bus.dly.delayTime.setTargetAtTime(Math.min(1.9, 60 / bpm() * .75), t, .05);
    bus.fb.gain.setTargetAtTime(S.echo * .6, t, .05);
    bus.dlyOut.gain.setTargetAtTime(M.dry ? 0 : S.echo * .6, t, .05);
    bus.revOut.gain.setTargetAtTime(M.dry ? S.verb * .2 : Math.min(1.2, S.verb + (M.verbBoost || 0)), t, .05);
  }
  const bpm = () => M.bpm * S.tempo;

  // ---------- instruments ----------
  function tone(f, t, dur, kind, vol, dest) {
    const c = ctx(), g = c.createGain(); g.connect(dest || bus.in);
    const osc = (type, fr, det) => { const o = c.createOscillator(); o.type = type; o.frequency.value = fr; if (det) o.detune.value = det; o.start(t); o.stop(t + dur + 1.6); return o; };
    let a = .005, rel = .08, sus = 1, peak = vol, srcs = [];
    switch (kind) {
      case "epiano": srcs = [osc("sine", f), osc("triangle", f * 2, 4)]; a = .005; rel = .6; sus = .5; break;
      case "piano": srcs = [osc("triangle", f), osc("sine", f * 2)]; rel = 1.4; sus = .2; break;
      case "bell": srcs = [osc("sine", f), osc("sine", f * 2.76), osc("sine", f * 5.4)]; rel = 1.8; sus = .15; peak *= .7; break;
      case "vibes": srcs = [osc("sine", f), osc("sine", f * 4)]; rel = 1; sus = .3; break;
      case "marimba": srcs = [osc("sine", f), osc("sine", f * 3.9)]; rel = .25; sus = 0; break;
      case "brass": { const o = osc("sawtooth", f), lp = c.createBiquadFilter(); lp.type = "lowpass"; lp.frequency.setValueAtTime(300, t); lp.frequency.linearRampToValueAtTime(1800, t + .25); o.connect(lp); srcs = [lp]; a = .12; rel = .5; break; }
      case "choir": { srcs = [osc("sine", f, -6), osc("sine", f, 7), osc("triangle", f * 2, 3)]; const lfo = c.createOscillator(), lg = c.createGain(); lfo.frequency.value = 5; lg.gain.value = 4; lfo.connect(lg); srcs.forEach(s => s.detune && lg.connect(s.detune)); lfo.start(t); lfo.stop(t + dur + 1.6); a = .5; rel = 1.2; peak *= .6; break; }
      case "beep": srcs = [osc("sine", f)]; rel = .05; break;
      case "pluck": srcs = [osc("triangle", f)]; rel = .2; sus = .3; break;
      default: srcs = [osc(kind === "saw" ? "sawtooth" : kind, f)]; if (kind === "square" || kind === "saw") peak *= .45; rel = .06;
    }
    srcs.forEach(s => s.connect(g));
    g.gain.setValueAtTime(0, t); g.gain.linearRampToValueAtTime(peak, t + a);
    g.gain.setTargetAtTime(peak * sus, t + a, Math.max(.05, dur * .3));
    g.gain.setTargetAtTime(0, t + Math.max(a, dur), rel / 3);
  }
  function pad(freqs, t, dur, kind) {
    if (kind === "none") return;
    const c = ctx(), g = c.createGain(), lp = c.createBiquadFilter(); lp.type = "lowpass";
    lp.frequency.value = kind === "sawdark" ? 700 : kind === "hum" ? 400 : kind === "saw" ? 1800 : 2400;
    lp.connect(g); g.connect(bus.in);
    const type = kind === "sawdark" || kind === "saw" ? "sawtooth" : kind === "hum" ? "sine" : kind === "choir" ? "sine" : "triangle";
    freqs.forEach((f, i) => [-7, 7].forEach(det => { const o = c.createOscillator(); o.type = type; o.frequency.value = f; o.detune.value = det + (kind === "lush" ? i * 2 : 0); o.connect(lp); o.start(t); o.stop(t + dur + 2); }));
    const v = (type === "sawtooth" ? .028 : .05) / Math.sqrt(freqs.length);
    g.gain.setValueAtTime(0, t); g.gain.linearRampToValueAtTime(v, t + Math.min(1.2, dur * .4)); g.gain.setTargetAtTime(0, t + dur, .4);
  }
  function drum(kind, t, vol) {
    const c = ctx(), g = c.createGain(); g.connect(bus.drums);
    if (kind === "k") { const o = c.createOscillator(); o.frequency.setValueAtTime(150, t); o.frequency.exponentialRampToValueAtTime(42, t + .12); o.connect(g); g.gain.setValueAtTime(vol, t); g.gain.exponentialRampToValueAtTime(.001, t + .3); o.start(t); o.stop(t + .32); return; }
    const n = c.createBufferSource(), f = c.createBiquadFilter(); n.buffer = noiseBuf(c); n.connect(f); f.connect(g);
    if (kind === "s") { f.type = "bandpass"; f.frequency.value = 1800; f.Q.value = .7; g.gain.setValueAtTime(vol * .7, t); g.gain.exponentialRampToValueAtTime(.001, t + .18); n.start(t, Math.random() * .5, .2); }
    else if (kind === "h") { f.type = "highpass"; f.frequency.value = 7000; g.gain.setValueAtTime(vol * .25, t); g.gain.exponentialRampToValueAtTime(.001, t + .05); n.start(t, Math.random() * .5, .06); }
    else { f.type = "bandpass"; f.frequency.value = 2500 + Math.random() * 3000; f.Q.value = 3; g.gain.setValueAtTime(vol * Math.random() * .25, t); g.gain.exponentialRampToValueAtTime(.001, t + .012); n.start(t, Math.random() * .5, .015); }
  }

  function chordNotes(b) { const sc = SC[M.sc], d = M.prog[b % 4], deg = k => M.root + 12 * Math.floor((d + k) / sc.length) + sc[(d + k) % sc.length]; return [deg(0), deg(2), deg(4)].concat(M.seventh ? [deg(6)] : []); }
  function degNote(d) { const sc = SC[M.sc]; return M.root + 12 * Math.floor(d / sc.length) + sc[((d % sc.length) + sc.length) % sc.length]; }

  function playStep(i, t, s16) {
    const bar = Math.floor(i / 16) % 4, st = i % 16, ch = chordNotes(bar);
    if (st === 0) pad(ch.map(m => hz(m + 12)), t, s16 * 16, M.pad);
    // bass
    const root = hz(ch[0] - 12), bw = M.bassW || "triangle";
    const b = M.bass, bv = .22;
    if (b === "root4" && st % 4 === 0) tone(root, t, s16 * 3, bw, bv);
    else if (b === "root8" && st % 2 === 0) tone(root, t, s16 * 1.6, bw, bv * .9);
    else if (b === "pulse16") tone(root, t, s16 * .7, "saw", bv * .8);
    else if (b === "oompah" && st % 4 === 0) tone(st % 8 === 0 ? root : hz(ch[2] - 12), t, s16 * 1.5, bw, bv);
    else if (b === "syncop" && [0, 3, 6, 10, 12].includes(st)) tone(root, t, s16 * 1.5, "saw", bv);
    else if (b === "walk" && st % 4 === 0) { const nxt = chordNotes(bar + 1)[0]; const w = [ch[0], ch[1], ch[2], nxt + (nxt > ch[0] ? -1 : 1)][st / 4]; tone(hz(w - 12), t, s16 * 3.5, bw, bv); }
    else if (b === "acid") { const on = "x.xx.x.xx.x.x.xx"[st] === "x"; if (on) { const c = ctx(), o = c.createOscillator(), lp = c.createBiquadFilter(), g = c.createGain(); o.type = "sawtooth"; o.frequency.value = root * (st % 7 === 3 ? 2 : 1); lp.type = "lowpass"; lp.Q.value = 12; lp.frequency.setValueAtTime(1800 + 1200 * Math.sin(i / 9), t); lp.frequency.exponentialRampToValueAtTime(200, t + s16); o.connect(lp); lp.connect(g); g.connect(bus.in); g.gain.setValueAtTime(.12, t); g.gain.setTargetAtTime(0, t + s16 * .8, .02); o.start(t); o.stop(t + s16 * 1.5); } }
    else if (b === "chug" && "xxx.xx.xxxx.x.xx"[st] === "x") { tone(root, t, s16 * .6, "saw", .25); tone(root * 1.5, t, s16 * .6, "saw", .18); }
    // lead
    for (const n of song) if (n[0] === i % 64) {
      const m = degNote(n[1]) + 12 * (M.lead.o - 1);
      if (n[3]) ch.forEach((cm, k) => k < 3 && tone(hz(cm + 12 * M.lead.o), t, s16 * .8, M.lead.w, .06));
      else tone(hz(m), t, s16 * n[2] * (M.lead.p === "arp" ? .9 : .95), M.lead.w, M.lead.p === "arp" ? .07 : .12);
    }
    // drums
    const d = DR[M.dr], vel = M.dr === "lofi" || M.dr === "light" ? .5 : .8;
    if (d[0][st] === "x") drum("k", t, vel);
    if (d[1][st] === "x") drum("s", t, vel);
    if (d[2][st] === "x") drum("h", t, vel * (st % 4 === 0 ? 1 : .6));
    if (M.vinyl && Math.random() < .25 * M.vinyl) drum("c", t + Math.random() * s16, 1);
  }
  function tick() {
    if (!alive() || !S.music) return stopMusic();
    const c = ctx();
    if (!M) return;
    while (nextT < c.currentTime + .15) {
      const s16 = 60 / bpm() / 4, sw = step % 2 ? (M.swing || 0) * s16 : 0;
      playStep(step, nextT + sw, s16);
      nextT += s16; step++;
    }
  }
  function startMusic() {
    if (timer || !S.music || !M) return;
    const c = ctx(); bus = bus || makeBus(); busSet();
    nextT = c.currentTime + .1; step = 0;
    timer = setInterval(tick, 40);
  }
  function stopMusic() { clearInterval(timer); timer = 0; if (bus) bus.out.gain.setTargetAtTime(0, ctx().currentTime, .08); }
  function setTrack(id) {
    curId = id; M = MUSIC[id] || MUSIC.default; song = compose(id, M);
    if (timer) { stopMusic(); startMusic(); }
  }

  // ---------- Commander Randis (StarCraft II skin) ----------
  const decoded = {};
  async function lineBuf(k) {
    if (decoded[k]) return decoded[k];
    await skWavs(); const c = ctx(), b64 = window.SHOP_RANDIS_WAVS[k].split(",")[1], bin = atob(b64), u = new Uint8Array(bin.length);
    for (let i = 0; i < bin.length; i++) u[i] = bin.charCodeAt(i);
    decoded[k] = await c.decodeAudioData(u.buffer);
    return decoded[k];
  }
  function squelch(sr, end) {   // the radio click, same idea as his comms in Intelligence Hijacking
    const n = Math.round(sr * (end ? .07 : .09)), x = new Float32Array(n);
    for (let i = 0; i < n; i++) { const t = i / sr, env = Math.exp(-t * 40); x[i] = (Math.random() * 2 - 1) * .18 * env + (end ? 0 : Math.sin(2 * Math.PI * 1250 * t) * .12 * (t < .045 ? 1 : 0)); }
    return x;
  }
  let speaking = null;
  async function say(k, ui) {
    if (!S.voice || !SHOP_RANDIS_LINES[k]) return;
    const c = ctx(), buf = await lineBuf(k), sr = buf.sampleRate;
    let x = buf.getChannelData(0).slice();
    if (S.fxOn && S.chain.length) x = SFX.applyFx(x, full(S.chain.filter(f => f.on !== false)), sr);
    if (S.squelch) { const a = squelch(sr), z = squelch(sr, true), y = new Float32Array(a.length + x.length + z.length); y.set(a); y.set(x, a.length); y.set(z, a.length + x.length); x = y; }
    if (speaking) try { speaking.stop(); } catch (e) {}
    const b = c.createBuffer(1, x.length, sr); b.getChannelData(0).set(x);
    const src = c.createBufferSource(), g = c.createGain(), lim = c.createDynamicsCompressor();
    src.buffer = b; g.gain.value = Math.max(0, Math.min(3, S.vgain));
    lim.threshold.value = -3; lim.knee.value = 2; lim.ratio.value = 20; lim.attack.value = .003; lim.release.value = .15;
    src.connect(g); g.connect(lim); lim.connect(c.destination);
    speaking = src;
    if (ui) ui(SHOP_RANDIS_LINES[k].text, x.length / sr);
    src.start();
  }

  // ---------- the panel ----------
  function slider(label, min, max, stepv, val, fmt, on) {
    const wrap = mk("label", { className: "ss-sl" }), v = mk("b", {}, fmt(val));
    const r = mk("input", { type: "range", min, max, step: stepv, value: val });
    r.addEventListener("input", () => { v.textContent = fmt(+r.value); on(+r.value); });
    wrap.append(mk("span", {}, label), r, v);
    return wrap;
  }
  function check(label, val, on) {
    const l = mk("label", { className: "ss-ck" }), c = mk("input", { type: "checkbox", checked: !!val });
    c.addEventListener("change", () => on(c.checked)); l.append(c, " " + label); return l;
  }
  const pct = v => Math.round(v * 100) + "%";

  function attach(pane, stage, bar, spot) {
    alive = () => pane.isConnected;
    const btn = mk("button", { className: "pill shop-snd-btn", title: "Theme music and Commander Randis" }, "♪ Sound");
    bar.insertBefore(btn, spot);
    const panel = mk("div", { className: "shop-snd", hidden: true });
    stage.appendChild(panel);
    btn.addEventListener("click", () => { panel.hidden = !panel.hidden; if (!panel.hidden) draw(); });

    // Randis's portrait, bottom right, in the StarCraft II skin only
    const port = mk("div", { className: "shop-randis", title: "Commander Randis. Click him." });
    const face = mk("img", { src: "site/randis.jpg", alt: "Commander Randis" });
    const sub = mk("div", { className: "shop-randis-sub" });
    port.append(mk("div", { className: "shop-randis-frame" }, ""), sub, mk("div", { className: "shop-randis-name" }, "CMDR. RANDIS"));
    port.firstChild.appendChild(face);
    stage.appendChild(port);
    let subT = 0;
    const show = (text, secs) => { sub.textContent = text; port.classList.add("talking"); clearTimeout(subT); subT = setTimeout(() => port.classList.remove("talking"), Math.max(1200, secs * 1000 + 600)); };
    let clicks = [], lastTouch = Date.now(), cycle = 0;
    pane.addEventListener("pointerdown", e => { if (!port.contains(e.target)) lastTouch = Date.now(); }, true);
    port.addEventListener("click", () => {
      const now = Date.now();
      clicks = clicks.filter(t => now - t < 4000); clicks.push(now);
      let k;
      if (now - lastTouch > 60000) k = "scared";
      else if (clicks.length >= 5) { k = "nottoday"; clicks = []; }
      else k = ["yes", "help", "yes", "help", "hello"][cycle++ % 5];
      lastTouch = now;
      if (!S.voice) return show(SHOP_RANDIS_LINES[k].text, 1.5);
      say(k, show);
    });
    const randisOn = () => (pane.dataset.skin === "sc2" || pane.dataset.randis === "1") && S.randis;
    const place = () => { port.hidden = !randisOn(); };
    pane.addEventListener("shopskin", e => {
      setTrack(pane.dataset.music || e.detail); place(); if (!panel.hidden) draw();
      if (randisOn()) { lastTouch = Date.now(); if (S.voice) say("hello", show); else show(SHOP_RANDIS_LINES.hello.text, 1.5); }
    });
    pane.addEventListener("shopopen", () => { if (randisOn()) { lastTouch = Date.now(); if (S.voice) say("confirmed", show); else show(SHOP_RANDIS_LINES.confirmed.text, 1.2); } });
    setTrack(pane.dataset.music || pane.dataset.skin || "default"); place();

    function draw() {
      panel.textContent = "";
      const head = mk("div", { className: "ss-head" }); const x = mk("button", { className: "pill", title: "Close" }, "✕");
      x.addEventListener("click", () => panel.hidden = true);
      head.append(mk("b", {}, "Sound"), x); panel.appendChild(head);
      // music
      const mu = mk("div", { className: "ss-sec" });
      mu.append(mk("h5", {}, "Theme music"),
        check("Play this skin's music", S.music, v => { S.music = v; save(); if (v) startMusic(); else stopMusic(); }),
        mk("div", { className: "ss-track" }, "♫ " + (MUSIC[curId] || MUSIC.default).name),
        slider("Music volume", 0, 1, .01, S.mvol, pct, v => { S.mvol = v; save(); busSet(); }),
        slider("Tempo", .6, 1.4, .01, S.tempo, pct, v => { S.tempo = v; save(); busSet(); }),
        slider("Brightness", 0, 1, .01, S.bright, pct, v => { S.bright = v; save(); busSet(); }),
        slider("Echo", 0, 1, .01, S.echo, pct, v => { S.echo = v; save(); busSet(); }),
        slider("Reverb", 0, 1, .01, S.verb, pct, v => { S.verb = v; save(); busSet(); }));
      panel.appendChild(mu);
      // Randis
      const rv = mk("div", { className: "ss-sec" });
      rv.append(mk("h5", {}, "Commander Randis (StarCraft II skin)"),
        check("Show him", S.randis, v => { S.randis = v; save(); place(); }),
        check("He talks (his own recorded lines)", S.voice, v => { S.voice = v; save(); }),
        slider("His voice volume", 0, 3, .05, S.vgain, pct, v => { S.vgain = v; save(); }));
      const lines = mk("div", { className: "ss-lines" });
      for (const k of Object.keys(SHOP_RANDIS_LINES)) { const b = mk("button", { className: "pill" }, "▶ " + SHOP_RANDIS_LINES[k].text); b.addEventListener("click", () => say(k, show)); lines.appendChild(b); }
      rv.appendChild(lines);
      // voice effects: the same presets and rack as Intelligence Hijacking
      const fx = mk("div", { className: "ss-sec" });
      const pre = mk("select", {});
      for (const [id, p] of Object.entries(PRESETS)) pre.appendChild(mk("option", { value: id }, p.name));
      pre.appendChild(mk("option", { value: "custom" }, "Custom"));
      pre.value = S.preset in PRESETS ? S.preset : "custom";
      pre.addEventListener("change", () => { if (pre.value === "custom") return; S.preset = pre.value; S.chain = full(PRESETS[pre.value].chain); save(); draw(); });
      const pl = mk("label", { className: "ss-sl" }); pl.append(mk("span", {}, "Preset"), pre);
      fx.append(mk("h5", {}, "His voice effects"),
        check("Effects on", S.fxOn, v => { S.fxOn = v; save(); }),
        check("Radio squelch (click before and after)", S.squelch, v => { S.squelch = v; save(); }), pl);
      S.chain.forEach((f, i) => {
        const D = SFX.FX[f.type]; if (!D) return;
        const box = mk("div", { className: "ss-fx" }), top = mk("div", { className: "ss-fx-top" });
        const rm = mk("button", { className: "pill", title: "Take this effect out" }, "✕");
        rm.addEventListener("click", () => { S.chain.splice(i, 1); S.preset = "custom"; save(); draw(); });
        top.append(check(D.l, f.on !== false, v => { f.on = v; S.preset = "custom"; save(); }), rm);
        box.appendChild(top);
        for (const [k, d] of Object.entries(D.p)) {
          if (Array.isArray(d[0])) {
            const s = mk("select", {}); d[0].forEach(o => s.appendChild(mk("option", { value: o }, o))); s.value = f[k];
            s.addEventListener("change", () => { f[k] = s.value; S.preset = "custom"; save(); });
            const l = mk("label", { className: "ss-sl" }); l.append(mk("span", {}, d[1]), s); box.appendChild(l);
          } else box.appendChild(slider(d[4], d[1], d[2], d[3], f[k], v => (+v.toFixed(3)) + (d[5] ? " " + d[5] : ""), v => { f[k] = v; S.preset = "custom"; pre.value = "custom"; save(); }));
        }
        fx.appendChild(box);
      });
      const add = mk("select", {}); add.appendChild(mk("option", { value: "" }, "+ Add an effect…"));
      for (const [t, d] of Object.entries(SFX.FX)) add.appendChild(mk("option", { value: t }, d.l));
      add.addEventListener("change", () => { if (!add.value) return; S.chain.push(SFX.fxDefaults(add.value)); S.preset = "custom"; save(); draw(); });
      fx.appendChild(add);
      const test = mk("button", { className: "pill primary" }, "▶ Hear him with these effects");
      test.addEventListener("click", () => say(["hello", "help", "yes", "confirmed"][Math.floor(Math.random() * 4)], show));
      fx.appendChild(test);
      panel.append(rv, fx);
    }
    // music pauses while the tab isn't on screen and comes back when it is
    const watch = setInterval(() => {
      if (!pane.isConnected) { clearInterval(watch); return stopMusic(); }
      const vis = document.visibilityState === "visible";
      if (!vis && timer) stopMusic(); else if (vis && !timer && S.music) startMusic();
    }, 700);
  }
  return { attach };
})();

"use strict";

// [headline, small print, button]. Keyed by the item's slug; anything new in a shop gets a joke from SHOP_AD_ANY.
const SHOP_AD_COPY = {
  "atelier-fashion-suite": ["Sew what? Sew THIS.", "Atelier takes a garment from napkin doodle to shop shelf. Pattern-making not included in your personality, but it is in the app.", "Get stitched up"],
  "aura-assistant": ["Your desktop called. It's lonely.", "Aura gives it a living, animated assistant with feelings*. *Simulated. Probably.", "Meet Aura"],
  "club-wiki": ["Your club has lore. Write it down before Dave forgets it.", "Club Wiki: a ready-made wiki for clubs, teams and makerspaces.", "Start the lore"],
  "code-editor": ["Ctrl+S your way to greatness.", "Code Editor: HTML, CSS and JS in one small, fast tab. Semicolons sold separately.", "Write some code"],
  "codex-academy": ["Learn to code before the robots learn to you.", "Codex Academy takes you from 'what's a variable' to 'why is prod down'.", "Enroll for $0"],
  "discord-bot-design-suite": ["Build a bot that says 'pong' when you say 'ping'. And more.", "Discord Bot Design Suite: no PhD in YAML required.", "Beep boop"],
  "forge-rd-suite": ["Got an idea in the shower? Bring it to the Forge.", "R&D from wild idea to real product. Towel not included.", "Forge ahead"],
  "free-money-finder": ["FREE MONEY. No, really. This is not that kind of ad.", "Free Money Finder looks for money you might actually be owed. We know. We were suspicious too.", "Find my money"],
  "game-emulator-suite": ["Blow on the cartridge. Emotionally.", "Game Emulator Suite plays the retro games you already own. 13 systems. Zero dust.", "Press Start"],
  "heirloom-boxes": ["Build a box your great-grandkids will fight over.", "Heirloom Boxes: curio boxes and toy chests meant to outlive the Wi-Fi.", "Box it up"],
  "heirloom-design-lab": ["Things they don't make anymore? Make them anymore.", "Heirloom Design Lab: design stuff that lasts longer than your phone contract.", "Design forever"],
  "heritage": ["Find out if you're secretly royalty. (You're not. But still.)", "Heritage: your family tree, with sources, stories and the uncle nobody talks about.", "Climb the tree"],
  "intelligence-hijacking": ["Commander Randis wants YOU... to do your brain push-ups.", "Intelligence Hijacking: brain training led by a hologram who believes in you more than your gym teacher did.", "Report for duty"],
  "life-tree": ["Your to-do list has a to-do list now.", "Life Tree: one giant tree for planning your whole life. Branches go all the way down.", "Get organized-ish"],
  "media-network": ["Run a news network from your bedroom. Pants optional.", "Randis Media Network: your own AI-powered media control room.", "Go on air"],
  "mintworks-exchange": ["To the moon! (Play money. The moon is also fake.)", "Mintworks Exchange: trade crypto and collectibles with zero real dollars lost.", "Lose fake money"],
  "money-lab": ["Make terrible stock picks with ZERO consequences!", "Money Lab: 170 simulated markets and a money school. Your real wallet stays safe.", "Paper trade now"],
  "music-studio": ["Your shower concerts deserve a studio.", "Music Studio: tracks, synths, drums and a piano teacher who never sighs at you.", "Lay down a track"],
  "notepad": ["Introducing: Notepad. It's a notepad.", "No AI. No cloud. No 'smart' anything. Just you and your thoughts. Terrifying.", "Write stuff"],
  "omnisight-xint-suite": ["Open-source intelligence. Closed-source snacks.", "Omnisight xINT Suite: a lawful OSINT workbench for cases, leads and timelines. Trench coat optional.", "Investigate"],
  "pdf-maker": ["Make a PDF. Feel like an accountant. Live the dream.", "PDF Maker turns your words and pictures into a clean PDF in seconds.", "Make it official"],
  "publishing-suite": ["Write one book. Or 4,000. We don't judge.", "Publishing Suite: the whole book factory, from template to series.", "Be an author"],
  "quak-quak": ["Talk to the duck. The duck knows.", "Quak Quak: a rubber duck for debugging out loud. It has never once interrupted anybody.", "Quak"],
  "randis-antivirus": ["Viruses hate this one weird app!", "Randis Antivirus tells you in normal words what it found. No scary pop-ups selling you more antivirus.", "Scan me"],
  "randis-bench-lab": ["Is your AI smart? Let's find out. Gently.", "Randis Bench Lab: design and run benchmarks without crying into a spreadsheet.", "Run the test"],
  "randis-office": ["A whole office. No coworker microwaving fish.", "Randis Office: documents, spreadsheets, slides and more, all in one page.", "Clock in"],
  "randis-paint": ["Bob Ross energy, now on your desktop.", "Randis Paint: happy little pixels. Made entirely by chatting with Randis UDS.", "Paint something"],
  "randis-sound-forge": ["Elevator music? We've got elevator music.", "Randis Sound Forge: royalty-free songs in any genre. Even the genre you just made up.", "Press Make"],
  "repo-scout": ["Someone already built it. Repo Scout knows where.", "It searches GitHub, GitLab, Codeberg and more so you don't have to open 47 tabs.", "Go scouting"],
  "service-member-helper": ["Paperwork, but at ease.", "Service Member Helper: a plain-language toolkit for service members, veterans and families.", "Fall in"],
  "shop-studio": ["Like this shop? Make your own. We won't be jealous. Much.", "Shop Studio: build and run your own online shop, just like this one.", "Open a shop"],
  "sing-in-my-voice": ["Finally, a singer who sounds exactly like you.", "Sing in My Voice: Sound Forge songs sung in your own voice. Your mom will cry. Good tears, probably.", "Start singing"],
  "templeos": ["Experience a legend. 640x480. 16 colors. Zero compromises.", "Run the real TempleOS 5.03 in a safe sandbox. Hymns included.", "Boot it"],
  "the-dispatch": ["Extra! Extra! Your club made the news!", "The Dispatch: a modern newsletter page. Paperboy sold separately.", "Read all about it"],
  "vm-suite": ["Computers inside your computer. Computer-ception.", "VM Suite runs real operating systems inside a tab. Yo dawg.", "Go deeper"],
  "voice-forge": ["Sound like a wizard. Or a giant. Or a toaster.", "Voice Forge: a voice studio where every voice is built from numbers.", "Find your voice"],
  "vr-avatar-designer": ["Be taller in VR. We won't tell.", "VR Avatar Designer: a fully rigged 3D you, with better hair.", "Build my avatar"],
  "vtuber-studio": ["Become an anime. Legally.", "VTuber Studio: design, rig and stream your own original VTuber.", "Go live"],
  "weather": ["It's going to be weather today.", "Weather: the forecast, minus the dramatic music.", "Look outside"],
  "wiki-suite": ["Your own Wikipedia. Citation needed? Never again.", "Wiki Suite: linked pages, templates and categories, all yours.", "Start editing"],
  "battle-tanks-royale": ["Honk honk. That's tank for 'move'.", "Battle Tanks Royale: defend your base from waves of tanks. Parking is still a nightmare.", "Roll out"],
  "bindy-and-louis": ["A binder clip that fixes things. And an arcade game. Yes, both.", "Bindy & Louis: the repair helper you didn't know you needed.", "Clip in"],
  "blockwild": ["Punch trees. Build castles. Repeat until sunrise.", "Blockwild: an endless voxel world, and none of it needs mowing.", "Start digging"],
  "card-master": ["57 card games and none of them is Go Fish. Wait, it is.", "Card Master: 57 classics with rules, 27 you can play right now.", "Deal me in"],
  "castle-mnemosyne": ["Remember everything. In a castle. Like a wizard.", "Castle Mnemosyne: a pixel-art memory palace. Your grocery list has never been so majestic.", "Enter the castle"],
  "coin-flipper": ["Can't decide? Let physics decide.", "Coin Flipper: six ways to flip, with stats for every flip. Heads, you play. Tails, you also play.", "Flip it"],
  "dice-master": ["Roll a d100 for no reason. Feel powerful.", "Dice Master: every die from d4 to d100, plus classic dice games against the computer.", "Roll 'em"],
  "diesel-gen-mechanic-simulator": ["Grease monkey wanted. Must love noise.", "Diesel Gen Mechanic Simulator: fix generators under a scruffy old boss. Smell not simulated.", "Grab a wrench"],
  "fossil-collector": ["Dig up a T. rex. Name it Kevin.", "Fossil Collector: a whole paleontology career. Bones not included. Wait, they are.", "Start digging"],
  "gem-collector": ["Shine bright like a gem you cut yourself.", "Gem Collector: mine rough stones and cut them on a virtual lapping machine.", "Get sparkly"],
  "gilded-hands": ["Chips times Mult equals JOY.", "Gilded Hands: an original poker-hand roguelike. Your poker face is optional.", "Shuffle up"],
  "hotdog-tycoon": ["Hot dogs in YOUR area want to meet you!", "Hotdog Tycoon: start with one stand for Big Sal, end up a wiener empire.", "Relish it"],
  "lanternfall": ["Build a deck. Light the dark. Lose sleep.", "Lanternfall: an original deck-building roguelike. 'One more run' guaranteed.", "Light it up"],
  "lhc-simulator": ["Smash particles. Don't make a black hole. (Probably fine.)", "LHC Simulator: run the Large Hadron Collider from 2012 to High-Luminosity.", "Collide"],
  "mail-sorter": ["You've got mail. SO MUCH mail.", "Mail Sorter: sort it before the pile buries you. Then sort it again.", "Sort it out"],
  "marble-collector": ["You haven't lost your marbles. They're right here.", "Marble Collector: Ringer, Battle, Bullseye and a collection to brag about.", "Knuckle down"],
  "matching-master": ["Your memory called. It forgot why.", "Matching Master: flip cards and match pairs. It keeps getting bigger. Like your brain.", "Flip a pair"],
  "milk-cap-champ": ["POGS ARE BACK. Your 1995 self is screaming.", "Milk Cap Champ: stack 'em, slam 'em, flip 'em.", "SLAM!"],
  "pachinko-player": ["Tokyo pachinko parlor. No smoke. No commute.", "Pachinko Player: rent balls, shoot them in and hit START. Lights included. LOTS of lights.", "Pachinko!"],
  "pong": ["It's Pong. You know what to do.", "Classic Pong, clean and simple. Bloop. Bloop. Bloop.", "Bloop"],
  "rev-the-frog": ["A frog. Rocket boots. The fate of the world.", "REV! The Frog Who Saved the World: an original 3D platformer. Ribbit responsibly.", "Hop to it"],
  "sandwich-master": ["Bread. Stuff. Bread. You're a genius.", "Sandwich Master: build every order bread first. No soggy bottoms.", "Make a sammich"],
  "skateboard-collector": ["Kickflip into your collecting era.", "Skateboard Collector: 60-second sessions, tricks and decks to collect. Zero scraped knees.", "Drop in"],
  "slot-player": ["Win big! (Nothing. You win nothing. It's free.)", "Slot Player: four machines of ding-ding-ding with none of the real-money regret.", "Pull the lever"],
  "topiary-master": ["Shape a hedge like a dolphin. Live your truth.", "Topiary Master: get hired to trim hedges into whatever the client dreams up.", "Get snippy"],
  "randis-uds": ["The app that made every app in this shop. It's apps all the way down.", "Randis UDS: a blank desktop app you change just by asking.", "Learn more"],
};
const SHOP_AD_ANY = [
  ["Doctors HATE this one weird {kind}!", "{name}: {blurb}", "Find out why"],
  ["You won't BELIEVE what {name} does next.", "Number 7 will shock you. There is no number 7.", "See for yourself"],
  ["Congratulations! You're the 1,000,000th visitor!", "Your prize: {name}. It was free anyway.", "Claim my prize"],
  ["Hot new {kind} in your area!", "{name} is just one click away. And it's single.", "Say hi"],
];
const SHOP_AD_QUOTES = [
  "I opened {name} and my houseplants started respecting me.",
  "{name} changed my life. Mostly my Tuesday afternoons.",
  "Five stars. Would click again.",
  "I told my therapist about {name}. Now she uses it too.",
  "My cat walked across the keyboard and opened {name}. Smart cat.",
  "I was skeptical. Then I wasn't. Then I had a snack.",
];
const SHOP_AD_FEET = ["*Free. It's always free. We just like asterisks.", "*Results may vary. Results may also be awesome.", "*No pop-ups were harmed in the making of this ad.",
  "*Ad paid for with exposure.", "*This ad is fake. The item is real. Life is strange.", "*Side effects may include fun."];
const SHOP_AD_PEOPLE = ["Gary, probably real", "Linda, verified human", "A guy named Steve", "Your neighbor (allegedly)", "Dr. Pixel, not a doctor", "Commander Randis, hologram"];

function shopAdsOn() { return localStorage.getItem("udsShopAds") !== "off"; }

// Makes the ads for one shop's items and puts them in the list: a banner on top, one between sections, one at the end.
function shopAddAds(list, items, onPick) {
  if (!shopAdsOn() || !items.length) return;
  const pick = a => a[Math.floor(Math.random() * a.length)];
  const fill = (s, it) => s.replace(/\{name\}/g, it.name).replace(/\{kind\}/g, it.kind === "games" ? "game" : "app").replace(/\{blurb\}/g, (it.blurb || "").split(/(?<=[.!?])\s/)[0]);
  const ads = items.map(it => {
    const slug = it.item.split("/").pop(), c = SHOP_AD_COPY[slug] || pick(SHOP_AD_ANY);
    return { it, head: fill(c[0], it), sub: fill(c[1], it), cta: fill(c[2], it), quote: fill(pick(SHOP_AD_QUOTES), it), who: pick(SHOP_AD_PEOPLE), foot: pick(SHOP_AD_FEET) };
  }).sort(() => Math.random() - .5);
  let n = 0;
  const slot = () => {
    const box = mk("div", { className: "shop-ad-slot" });
    let ad = null, timer = 0, i = n++ % ads.length, hold = false;
    const show = () => {
      const a = ads[i % ads.length]; i += 3;
      const next = shopAdBanner(a, onPick, () => { clearInterval(timer); box.remove(); });
      if (ad) ad.replaceWith(next); else box.appendChild(next);
      ad = next;
    };
    box.addEventListener("mouseenter", () => hold = true);
    box.addEventListener("mouseleave", () => hold = false);
    show();
    timer = setInterval(() => { if (!box.isConnected) return clearInterval(timer); if (!hold && box.offsetParent) show(); }, 9000);
    return box;
  };
  list.insertBefore(slot(), list.firstChild);
  const heads = [...list.querySelectorAll(":scope > h3")];
  if (heads.length > 2) list.insertBefore(slot(), heads[2]);
  else if (heads.length > 1) list.insertBefore(slot(), heads[1]);
  list.appendChild(slot());
}

function shopAdBanner(a, onPick, onClose) {
  const style = Math.floor(Math.random() * 6);
  const ad = mk("div", { className: "shop-ad shop-ad-" + style, title: "A fake ad for " + a.it.name + ". Click to see it in the shop." });
  const tag = mk("span", { className: "shop-ad-tag" }, "AD");
  const x = mk("button", { className: "shop-ad-x", title: "Hide this ad" }, "✕");
  x.addEventListener("click", e => { e.stopPropagation(); onClose(); });
  const body = mk("div", { className: "shop-ad-body" });
  if (a.it.logo) { const img = mk("img", { className: "shop-ad-logo", src: a.it.logo, alt: "" }); img.onerror = () => img.remove(); ad.appendChild(img); }
  if (style === 0) ad.appendChild(mk("div", { className: "shop-ad-burst" }, Math.random() < .5 ? "NEW!" : "FREE!*"));
  if (style === 1) body.appendChild(mk("div", { className: "shop-ad-kicker" }, "BUT WAIT, THERE'S MORE!"));
  body.appendChild(mk("div", { className: "shop-ad-head" }, a.head));
  if (style === 3) body.appendChild(mk("div", { className: "shop-ad-quote" }, `“${a.quote}” — ${a.who}`));
  else body.appendChild(mk("div", { className: "shop-ad-sub" }, a.sub));
  if (style === 1) { const pr = mk("div", { className: "shop-ad-price" }); pr.append("Was ", mk("s", {}, "$49.99"), " now $0.00!"); body.appendChild(pr); }
  if (style === 4) { const t = mk("div", { className: "shop-ad-timer" }); let s = 299; const tick = () => { t.textContent = `Offer ends in 00:0${Math.floor(s / 60)}:${String(s % 60).padStart(2, "0")} (it never ends)`; s = s > 0 ? s - 1 : 299; }; tick(); const id = setInterval(() => ad.isConnected ? tick() : clearInterval(id), 1000); body.appendChild(t); }
  body.appendChild(mk("div", { className: "shop-ad-foot" }, a.foot));
  const go = mk("span", { className: "shop-ad-cta" }, style === 2 ? "▶ CLICK HERE ◀" : a.cta);
  ad.append(tag, body, go, x);
  ad.addEventListener("click", () => onPick(a.it));
  return ad;
}

const SHOP_SKINS_LIST = [
  ["default", "Randis (normal)", "#1e1f22", "#4f8cff"],
  ["steam", "Steam Store", "#1b2838", "#66c0f4"],
  ["sc2", "StarCraft II", "#02070f", "#4fa3ff"],
  ["halo", "Xbox 360 / Halo 3", "#123a52", "#107c10"],
  ["hl", "Half-Life HEV", "#000000", "#ffa000"],
  ["temple", "TempleOS", "#ffffff", "#0000aa"],
  ["win95", "Windows 95", "#008080", "#c0c0c0"],
  ["xp", "Windows XP", "#3a6ea5", "#3c9b3c"],
  ["mac9", "Mac OS 9", "#dddddd", "#5a5a9a"],
  ["macos", "macOS Glass", "#8a6cf0", "#0a84ff"],
  ["material", "Material (Google)", "#f6f8fc", "#1a73e8"],
  ["matrix", "The Matrix", "#000000", "#00ff41"],
  ["lcars", "Star Trek LCARS", "#000000", "#ff9c00"],
  ["pipboy", "Fallout Pip-Boy", "#061206", "#1aff80"],
  ["tron", "Tron Grid", "#000000", "#00e5ff"],
  ["jarvis", "Iron Man JARVIS", "#04121e", "#8fe9ff"],
  ["cyber", "Cyberpunk 2077", "#0b0b10", "#fcee0a"],
  ["comic", "Comic Book", "#ffe14d", "#e3262f"],
  ["geocities", "GeoCities '98", "#000080", "#ff00ff"],
  ["vaporwave", "Vaporwave", "#b967ff", "#01cdfe"],
  ["bloomberg", "Bloomberg Terminal", "#000000", "#ffa028"],
  ["bios", "BIOS Setup", "#0000aa", "#aa0000"],
  ["doom", "Doom", "#2b0d00", "#ff2a00"],
  ["minecraft", "Minecraft", "#866043", "#c6c6c6"],
  ["wii", "Wii Menu", "#f4f4f4", "#34bfee"],
  ["xmb", "PlayStation XMB", "#1b4a8c", "#ffffff"],
  ["netflix", "Netflix", "#141414", "#e50914"],
  ["barbie", "Barbie Dreamhouse", "#ff8fcf", "#e0218a"],
];

// ---------- the skins rail on the shop page ----------
const SK_SKINS = [["classic", "Classic shop", "#0f7f7f", "#ffd23f"]].concat(SHOP_SKINS_LIST.filter(s => s[0] !== "default"));
function skRail() {
  const body = document.body;
  const rail = mk("div", { className: "sk-rail sk-fx-vars" });
  const head = mk("div", { className: "sk-head" });
  const fold = mk("button", { title: "Hide or show the skins" }, "«");
  head.append(mk("span", {}, "Skins"));
  const list = mk("div", { className: "sk-list" });
  const foot = mk("label", { className: "sk-foot", title: "Joke ads for things in this shop. Nothing is tracked or sold." });
  const adsBox = mk("input", { type: "checkbox", checked: shopAdsOn() });
  adsBox.addEventListener("change", () => { localStorage.setItem("udsShopAds", adsBox.checked ? "on" : "off"); skAds(); });
  foot.append(adsBox, mk("span", { className: "nm" }, " Show fake ads"));
  rail.append(head, list, foot);
  const fx = mk("div", { className: "sk-fx" });
  const rain = mk("canvas", { className: "sk-matrix" });
  document.body.append(rain, rail, fx);
  let timer = 0;
  function set(id, click) {
    if (!SK_SKINS.some(s => s[0] === id)) id = "classic";
    body.dataset.skin = id;
    if (id === "classic") body.dataset.music = "geocities"; else delete body.dataset.music;
    try { localStorage.setItem("shopSkin", id); } catch (e) {}
    list.querySelectorAll("button").forEach(b => b.classList.toggle("on", b.dataset.skin === id));
    clearInterval(timer); timer = 0;
    if (id === "matrix") timer = skRain(rain);
    if (click) body.dispatchEvent(new CustomEvent("shopskin", { detail: id }));
  }
  for (const [id, label, bg, ac] of SK_SKINS) {
    const b = mk("button", { title: label });
    b.dataset.skin = id;
    const sw = mk("span", { className: "sw" });
    sw.style.background = `linear-gradient(135deg, ${bg} 55%, ${ac} 55%)`;
    b.append(sw, mk("span", { className: "nm" }, label));
    b.addEventListener("click", () => set(id, true));
    list.appendChild(b);
  }
  function folded(on) {
    rail.classList.toggle("folded", on); fold.textContent = on ? "»" : "«";
    body.classList.toggle("sk-open", !on); body.classList.toggle("sk-folded", on);
    try { localStorage.setItem("shopSkinsFolded", on ? "1" : "0"); } catch (e) {}
  }
  fold.addEventListener("click", () => folded(!rail.classList.contains("folded")));
  const saved = localStorage.getItem("shopSkinsFolded");
  folded(saved ? saved === "1" : window.innerWidth < 1100);
  set(localStorage.getItem("shopSkin") || "classic");
  SHOP_SOUND.attach(body, fx, head, null);
  head.appendChild(fold);
  // opening something from the shop: Randis says "Confirmed."
  window.addEventListener("hashchange", () => { if (/\/play$/.test(location.hash)) body.dispatchEvent(new Event("shopopen")); });
}

function skRain(cv) {
  const ctx = cv.getContext("2d"), chars = "アイウエオカキクケコサシスセソ0123456789RANDIS";
  let drops = [], w = 0, h = 0;
  return setInterval(() => {
    if (document.visibilityState !== "visible") return;
    if (cv.clientWidth !== w || cv.clientHeight !== h) {
      w = cv.width = cv.clientWidth; h = cv.height = cv.clientHeight;
      drops = Array.from({ length: Math.ceil(w / 16) }, () => Math.random() * -50);
      ctx.fillStyle = "#000"; ctx.fillRect(0, 0, w, h);
    }
    ctx.fillStyle = "rgba(0,0,0,0.08)"; ctx.fillRect(0, 0, w, h);
    ctx.font = "15px Consolas, monospace";
    drops.forEach((y, i) => {
      ctx.fillStyle = Math.random() < 0.05 ? "#d8ffd8" : "#00ff41";
      ctx.fillText(chars[Math.floor(Math.random() * chars.length)], i * 16, y * 16);
      drops[i] = y * 16 > h && Math.random() > 0.975 ? 0 : y + 1;
    });
  }, 55);
}

// ---------- the fake ads on the shop page: under the header, in the middle, above the footer ----------
function skAds() {
  document.querySelectorAll(".shop-ad-slot").forEach(s => s.remove());
  const page = document.querySelector("#app > .page");
  if (!page || !shopAdsOn() || /\/play$/.test(location.hash)) return;
  const items = (window.ITEMS || []).filter(i => i.status !== "flagged").map(i => ({ item: i.kind + "/" + i.slug, kind: i.kind, name: i.name, blurb: i.blurb, logo: i.logo }));
  if (!items.length) return;
  const holder = mk("div");
  holder.append(mk("h3"), mk("h3"));
  shopAddAds(holder, items, it => { location.hash = "#/" + it.item; });
  const slots = [...holder.querySelectorAll(".shop-ad-slot")];
  const kids = [...page.children];
  if (kids.length < 2) return;
  page.insertBefore(slots[0], kids[1]);
  if (kids.length > 3) page.insertBefore(slots[1], kids[Math.min(3, kids.length - 1)]);
  page.insertBefore(slots[2], page.lastElementChild);
}

skRail();
skAds();
new MutationObserver(() => { if (!document.querySelector("#app > .page .shop-ad-slot") && shopAdsOn()) skAds(); })
  .observe(document.getElementById("app"), { childList: true });

})();
