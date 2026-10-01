// What the Lab's rooms share: the page's elements, the skin in the address (?skin=, which the car
// and the UV map room open) and the way back to the viewer, the car in each room (the viewer
// itself, embedded), the skin Claude painted last, and a few words.

export const $ = (id) => document.getElementById(id);

export const titleOf = (name) => name.replace(/^TSC_/, '').replaceAll('_', ' ').replace(/([a-z])(?=[A-Z])/g, '$1 ');

export const ago = (t) => {
  const s = Math.max(0, Date.now() / 1000 - t);
  return s < 60 ? 'just now' : s < 3600 ? `${Math.round(s / 60)} min ago` : s < 86400 ? `${Math.round(s / 3600)} h ago` : `${Math.round(s / 86400)} days ago`;
};

// A new note, or a change to one, for the viewer's server (tool/server.py, /api/notes).
export const post = (body) => fetch('api/notes', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });

// The skin the address names.
export const wanted = () => new URLSearchParams(location.search).get('skin');

// Put the skin in the address, and point the way back to the viewer at it.
export function note(name) {
  const u = new URL(location.href);
  u.searchParams.set('skin', name);
  history.replaceState(null, '', u);
  const back = document.getElementById('back');
  if (back) back.href = `./index.html?skin=${encodeURIComponent(name)}`;
}

// The viewer in an iframe (index.html?embed=1, no skin: no car until its first dress), once it
// says it's ready: its window.viewer, or null if it failed. Its credit line goes into `credit`:
// the car model's licence asks for it.
export function embedViewer(frame, credit) {
  return new Promise((resolve) => {
    frame.addEventListener('load', () => {
      const wait = setInterval(() => {
        const v = frame.contentWindow && frame.contentWindow.viewer;
        if (!v || !(v.ready || v.error)) return;
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
