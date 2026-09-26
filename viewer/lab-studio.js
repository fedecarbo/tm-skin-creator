// The Lab's Studio: the car a design builds, step by step from clay, while Claude works on it.
// The car at the picked step, big; a filmstrip of the car at every step under it; the step's words
// and a line to copy for Claude beside it. Layout B of the mockups the user chose on 2026-09-26
// (CHECKLIST.md, "The Lab", step 5).
//   /lab.html                          the skin Claude painted last
//   /lab.html?skin=<name>              that skin (the viewer's "The Lab" link)
// Either way, when Claude starts painting a skin, the Studio follows it.
// Everything comes from the tool: tool.skin show paints a design step by step (paintbox.Skin.step)
// and writes each step's frame and skins/<name>/steps.json (tool/view.py, export_steps), and
// studio.json, the skin it painted last. The page asks for both every 1.5 s, so the filmstrip
// fills in while a design is being painted. Both cars are the viewer itself (?embed=1): one big,
// one hidden behind it that draws the filmstrip's pictures.

const $ = (id) => document.getElementById(id);
const params = new URLSearchParams(location.search);
const POLL = 1500;

let copyLine = null;
let skin = null;          // { name, title }
let doc = null;           // steps.json
let picked = -1;
let stage = null, thumbs = null;  // the two viewers' window.viewer
let seen = {};            // step -> frame, when this browser last saw the skin: newer ones are New
let changed = new Set();
const pics = new Map();   // frame -> picture URL
let queue = Promise.resolve();
let stageLook = '';
let following = null;     // studio.json's stamp when last read: a new one means Claude started a skin

const lookOf = (step) => {
  const words = (step.look || '').split(/\s+/);
  return { view: ['front', 'rear', 'left', 'right', 'top'].find((w) => words.includes(w)) || 'front', night: words.includes('night') };
};
const titleOf = (name) => name.replace(/^TSC_/, '').replaceAll('_', ' ').replace(/([a-z])(?=[A-Z])/g, '$1 ');
const ago = (t) => {
  const s = Math.max(0, Date.now() / 1000 - t);
  return s < 60 ? 'just now' : s < 3600 ? `${Math.round(s / 60)} min ago` : s < 86400 ? `${Math.round(s / 3600)} h ago` : `${Math.round(s / 86400)} days ago`;
};

// ---- the two viewers ----

function viewer(frame) {
  return new Promise((resolve) => {
    frame.addEventListener('load', () => {
      const wait = setInterval(() => {
        const v = frame.contentWindow && frame.contentWindow.viewer;
        if (!v || !(v.ready || v.error)) return;
        clearInterval(wait);
        resolve(v.error ? null : v);
      }, 150);
    }, { once: true });
    frame.src = './index.html?embed=1';  // no skin: the stock car, dressed step by step
  });
}

function picture(step) {  // the filmstrip's picture of a step, drawn once per frame
  if (pics.has(step.frame)) return Promise.resolve(pics.get(step.frame));
  const job = queue.then(async () => {
    if (pics.has(step.frame)) return pics.get(step.frame);
    const look = lookOf(step);
    await thumbs.dress(step.textures);
    await thumbs.show(look.view, look.night);
    const url = await thumbs.picture();
    pics.set(step.frame, url);
    return url;
  });
  queue = job.catch(() => {});
  return job;
}

async function showOnStage(step) {
  if (!stage || !step.textures) return;
  await stage.dress(step.textures);
  const look = step.look || '';
  if (look !== stageLook) {  // a step with its own look turns the car; back to the front after it
    const l = lookOf(step);
    await stage.show(l.view, l.night);
    stageLook = look;
  }
}

// ---- the page ----

function strip() {
  const box = $('stStrip');
  box.textContent = '';
  doc.steps.forEach((step, k) => {
    const b = document.createElement('button');
    b.className = 'still' + (step.textures ? '' : ' wip');
    b.setAttribute('aria-current', String(k === picked));
    b.innerHTML = `<img alt=""><span class="k teko">${k}</span><div class="fn teko"><span></span></div>`;
    b.querySelector('.fn span').textContent = step.name;
    if (!step.textures) b.querySelector('.fn').insertAdjacentHTML('beforeend', ' <small>painting…</small>');
    else if (changed.has(k)) b.querySelector('.fn').insertAdjacentHTML('beforeend', ' <em class="newTag">New</em>');
    if (step.textures) {
      b.addEventListener('click', () => pick(k));
      if (thumbs) picture(step).then((url) => { b.querySelector('img').src = url; }).catch((e) => console.error(e));
    }
    box.append(b);
  });
}

function pick(k) {
  picked = k;
  const step = doc.steps[k], n = doc.steps.length;
  for (const [i, b] of [...$('stStrip').children].entries()) b.setAttribute('aria-current', String(i === k));
  $('stName').innerHTML = '<span></span> <small></small>';
  $('stName').querySelector('span').textContent = step.name;
  $('stName').querySelector('small').textContent = `step ${k} of ${n - 1}`;
  $('stAt').innerHTML = '<span></span><small></small>';
  $('stAt').querySelector('span').textContent = step.name;
  $('stAt').querySelector('small').textContent = `step ${k}`;
  $('stDoes').textContent = step.does || '—';
  $('stWordsRow').hidden = !step.words;
  $('stWords').textContent = step.words ? `“${step.words}”` : '';
  $('stPaints').textContent = step.paints.length ? step.paints.join(', ') : '—';
  const later = doc.steps.slice(k + 1).map((s) => s.name);
  $('stAfter').textContent = later.length ? `${later.join(', ')}: they stay on top if this step changes` : 'Nothing yet: this is the car now';
  $('stLine').textContent = step.line;
  if (params.has('skin') || params.has('step')) {
    const u = new URL(location.href);
    u.searchParams.set('step', k);
    history.replaceState(null, '', u);
  }
  showOnStage(step).catch((e) => console.error(e));
}

function live() {
  const box = $('stLive'), text = $('stLiveText');
  const open = doc.steps.find((s) => !s.textures);
  box.classList.toggle('on', !!doc.painting);
  if (doc.painting) {
    text.textContent = open ? `Claude is painting · ${open.name}` : 'Claude is painting';
    return;
  }
  if (!doc.stamp) { text.textContent = 'Made before the Studio'; return; }
  const names = [...changed].map((k) => doc.steps[k] && doc.steps[k].name).filter(Boolean);
  text.textContent = `Painted ${ago(doc.stamp)}` + (names.length && names.length < doc.steps.length ? ` · changed ${names.join(', ')}` : '');
}

function apply(next) {
  const before = doc;
  doc = next;
  const was = before ? Object.fromEntries(before.steps.map((s, k) => [k, s.frame])) : seen;
  if (Object.keys(was).length) {
    changed = new Set(doc.steps.map((s, k) => (s.frame && s.frame !== was[k] ? k : -1)).filter((k) => k >= 0));
  }
  const wantStep = Number(params.get('step'));
  const done = doc.steps.filter((s) => s.textures).length;
  if (!before && params.has('step') && doc.steps[wantStep] && doc.steps[wantStep].textures) picked = wantStep;
  else if (picked < 0 || picked >= done || (before && before.painting)) picked = Math.max(0, done - 1);
  strip();
  live();
  if (done) pick(picked);
  if (!doc.painting) {
    try { localStorage.setItem(`tsc-studio-${skin.name}`, JSON.stringify(Object.fromEntries(doc.steps.map((s, k) => [k, s.frame])))); } catch {}
  }
}

async function load(name) {
  const res = await fetch(`data/skins/${encodeURIComponent(name)}/steps.json`, { cache: 'no-store' });
  if (res.ok) return res.json();
  // painted before the Studio: the whole design is one step
  const s = await fetch(`data/skins/${encodeURIComponent(name)}/skin.json`);
  if (!s.ok) return null;
  const sk = await s.json();
  return { name, stamp: 0, painting: false, steps: [{ name: 'The design', does: 'Made before the Studio, so its steps weren\'t kept. The next time Claude paints it, they show here.', words: '', look: '', paints: [], line: `${name}: the design`, frame: `skin:${name}`, textures: sk.textures }] };
}

async function openSkin(name) {
  const list = await (await fetch('data/gallery.json')).json();
  const entry = list.find((s) => s.name === name);
  skin = { name, title: entry ? entry.title : titleOf(name) };
  $('stTitle').textContent = skin.title;
  try { seen = JSON.parse(localStorage.getItem(`tsc-studio-${name}`) || '{}'); } catch { seen = {}; }
  doc = null; picked = -1; changed = new Set(); stageLook = '';
  if (!stage) [stage, thumbs] = await Promise.all([viewer($('stCar')), viewer($('stThumbs'))]);
  const first = await load(name);
  if (first) apply(first);
  else $('stLiveText').textContent = 'Not shown in the viewer yet';
}

async function followed() {  // the skin Claude painted last: { skin, stamp }
  try {
    const r = await fetch('data/studio.json', { cache: 'no-store' });
    if (r.ok) return await r.json();
  } catch { /* none yet */ }
  return {};
}

async function poll() {
  try {
    const now = await followed();
    if (now.stamp && now.stamp !== following) {
      following = now.stamp;
      if (skin && now.skin !== skin.name) { await openSkin(now.skin); return; }
    }
    const res = await fetch(`data/skins/${encodeURIComponent(skin.name)}/steps.json`, { cache: 'no-store' });
    if (res.ok) {
      const next = await res.json();
      if (!doc || next.stamp !== doc.stamp) apply(next);
      else live();
    }
  } catch (e) { console.error(e); }
}

let opened = false;
export async function open(helpers) {
  if (opened) return;
  opened = true;
  copyLine = helpers.copy;
  $('stCopy').addEventListener('click', (e) => doc && picked >= 0 && copyLine({ line: doc.steps[picked].line }, e.currentTarget));
  const now = await followed();
  following = now.stamp;
  let name = params.get('skin') || now.skin;
  try { name ||= localStorage.getItem('tsc-viewer-skin'); } catch { /* no storage */ }
  if (!name) { $('stLiveText').textContent = 'No skin yet: ask Claude for one'; return; }
  await openSkin(name);
  setInterval(poll, POLL);
  window.lab.studioReady = true;
}
