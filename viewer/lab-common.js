// What the Lab's rooms share: the page's elements, the skin in the address (?skin=, which the car
// and the UV map room open), the page's own car (viewer.js's window.viewer) and the one the UV map
// room embeds, the skin Claude painted last, and a few words.

export const $ = (id) => document.getElementById(id);

export const titleOf = (name) => name.replace(/^TSC_/, '').replaceAll('_', ' ').replace(/([a-z])(?=[A-Z])/g, '$1 ');

export const ago = (t) => {
  const s = Math.max(0, Date.now() / 1000 - t);
  return s < 60 ? 'just now' : s < 3600 ? `${Math.round(s / 60)} min ago` : s < 86400 ? `${Math.round(s / 3600)} h ago` : `${Math.round(s / 86400)} days ago`;
};

// A new note, or a change to one, for the viewer's server (tool/server.py, /api/notes). With the
// server off, the answer is a failed one that says so, never an error the page swallows.
export async function post(body) {
  try {
    return await fetch('api/notes', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
  } catch {
    offline(true);
    return { ok: false, status: 0, json: async () => ({ error: OFF }) };
  }
}

// The banner when Claude's server is off (index.html, #offline): a heartbeat asks the server every
// 2 s (its /api/health); three misses in a row show it, one answer hides it. The rooms' own polls
// handle their errors as they like. Claude starts the server back (tool/doctor.py).
export const OFF = "Claude's server is off";
let misses = 0;
export function offline(down) {
  const el = document.getElementById('offline');
  if (el) el.hidden = !down;
}
async function heartbeat() {
  if (document.hidden) return;
  try {
    const r = await fetch('api/health', { cache: 'no-store' });
    if (!r.ok) throw new Error(String(r.status));
    misses = 0;
    offline(false);
  } catch {
    if (++misses >= 3) offline(true);
  }
}
setInterval(heartbeat, 2000);

// The skin the address names.
export const wanted = () => new URLSearchParams(location.search).get('skin');

// Put the skin in the address.
export function note(name) {
  const u = new URL(location.href);
  u.searchParams.set('skin', name);
  history.replaceState(null, '', u);
}

// The page's own car (viewer.js loads these modules once it's up): its window.viewer, or null if it failed.
export function viewer() {
  return new Promise((resolve) => {
    const wait = setInterval(() => {
      const v = window.viewer;
      if (!(v && (v.ready || v.error))) return;
      clearInterval(wait);
      resolve(v.error ? null : v);
    }, 50);
  });
}

// The car in an iframe (index.html?embed=1, no skin: no car until its first dress), once it
// says it's ready: its window.viewer, or null if it failed or said nothing within 20 s. Its credit
// line goes into `credit`: the car model's licence asks for it.
export function embedViewer(frame, credit) {
  return new Promise((resolve) => {
    frame.addEventListener('load', () => {
      const since = Date.now();
      const wait = setInterval(() => {
        const v = frame.contentWindow && frame.contentWindow.viewer;
        if (!(v && (v.ready || v.error))) {
          if (Date.now() - since < 20000) return;
          clearInterval(wait);
          resolve(null);
          return;
        }
        clearInterval(wait);
        const line = !v.error && frame.contentDocument.getElementById('credit');
        if (line && credit) { credit.innerHTML = line.innerHTML; credit.hidden = false; }
        resolve(v.error ? null : v);
      }, 150);
    }, { once: true });
    frame.src = './index.html?embed=1';
  });
}

// fn every `ms` while the page is in view, one at a time: a slow answer never stacks up behind
// the next ask, and a tab in the background asks nothing.
export function every(ms, fn) {
  let busy = false;
  setInterval(async () => {
    if (busy || document.hidden) return;
    busy = true;
    try { await fn(); } catch (err) { console.error(err); } finally { busy = false; }
  }, ms);
}

// The skin Claude painted last (tool/view.py's studio.json): { skin, stamp }, or {} before any.
export async function followed() {
  try {
    const r = await fetch('data/studio.json', { cache: 'no-store' });
    if (r.ok) return await r.json();
  } catch { /* none yet */ }
  return {};
}
