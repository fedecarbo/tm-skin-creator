// The switch between a round's concepts (the user's pick, 2026-09-26: "A · Switch in the title").
// When the Lab's skin is a take in a round of concepts (skins/rounds.json, which tool/gallery.py
// puts on each take's entry in gallery.json), the Studio and every painting room show a button per
// take, A, B, C. Picking one shows that take in the whole Lab: the address's ?skin= changes, and
// the Studio and the rooms (each keeps its own car) open it on the 'lab:skin' event.

let entries = null;

async function gallery() {
  entries = await (await fetch('data/gallery.json', { cache: 'no-store' })).json();
  return entries;
}

// The skin the Lab shows: the address's, which a pick changes.
export const wanted = () => new URLSearchParams(location.search).get('skin');

// The round the skin is a take in ({ title, words, key, takes: [{ key, name, title }] }), or null.
export async function roundOf(name) {
  const e = name && (await gallery()).find((s) => s.name === name);
  return (e && e.round) || null;
}

// Fill a .show box with the round's takes, the skin's pressed; hidden when it's in no round.
export async function render(box, name) {
  const r = await roundOf(name);
  box.replaceChildren();
  box.hidden = !r;
  if (!r) return null;
  for (const t of r.takes) {
    const b = document.createElement('button');
    b.className = 'sk';
    b.setAttribute('aria-pressed', String(t.name === name));
    b.title = t.name;
    b.innerHTML = '<span></span>';
    b.querySelector('span').textContent = `${t.key} · ${t.title}`;
    b.addEventListener('click', () => { if (t.name !== name) pick(t.name); });
    box.append(b);
  }
  return r;
}

// The Lab's skin in the address and the way back to the viewer. keepStep: a take picked on the
// switch opens at the step the Studio was showing (the same stage of each take, to compare); a skin
// Claude starts painting opens at its newest step.
export function note(name, keepStep = false) {
  const u = new URL(location.href);
  u.searchParams.set('skin', name);
  if (!keepStep) u.searchParams.delete('step');
  history.replaceState(null, '', u);
  const back = document.getElementById('back');
  if (back) back.href = `./index.html?skin=${encodeURIComponent(name)}`;
}

export function pick(name) {
  note(name, true);
  dispatchEvent(new CustomEvent('lab:skin', { detail: name }));
}
