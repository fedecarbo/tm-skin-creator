// The stand's tags (viewer/lab-studio.js; the user's pick, B, 2026-09-27: CHECKLIST.md, "The Lab",
// step 9). Each tag hangs beside the car in one of two gutters, the car framed between them
// (viewer.inset), and a line joins it to a dot on its point on the car. The viewer reports where the
// points are at the end of every frame it moves them (viewer.track), and the dots and lines are drawn
// from that in the same frame. The tags themselves stay put while the car turns, and settle into
// order (by their points' heights, each on its point's side) once it stops. One tag is open at a
// time; the others are one-line chips. Under 1000 px wide there are no gutters: the tags are a list
// under the car, and the dots stay on it.
//
//   const t = createTags({ stage, lines, dots, tags, list, gutter, onOpen });
//   t.set([{ key, dot, dotClass, sig, render(el, open), open? }])   what hangs on the car
//   viewer.track(points, t.place)                                   where their points are
//   t.close()                                                       the open one shut (one at a time)

const SVG = 'http://www.w3.org/2000/svg';
const SETTLE = 160;  // ms without a move before the tags re-order
const SWAP = 48;     // px a point must cross past the middle before its tag changes side
const GAP = 8;       // px between two tags
const TOP = 12, FOOT = 40;  // px kept clear above the tags and under them (the credit)
const narrowQuery = matchMedia('(max-width: 1000px)');

export function createTags({ stage, lines, dots, tags, list, gutter, onOpen }) {
  const items = new Map();  // key -> { key, entry, tag, dot, line, side, top, drawn }
  const where = new Map();  // key -> { x, y, shown, away }, the viewer's last word
  let openKey = null;
  let timer = null;
  let narrow = narrowQuery.matches;

  function draw(it) {
    const open = it.key === openKey;
    const sig = `${it.entry.sig}|${open}`;
    if (it.drawn === sig) return;
    it.drawn = sig;
    it.tag.classList.toggle('open', open);
    it.tag.textContent = '';
    it.entry.render(it.tag, open);
  }

  function set(entries) {
    const keys = new Set(entries.map((e) => e.key));
    for (const [k, it] of items) {
      if (keys.has(k)) continue;
      it.tag.remove(); it.dot.remove(); it.line.remove();
      items.delete(k);
      where.delete(k);
      if (openKey === k) openKey = null;
    }
    for (const e of entries) {
      let it = items.get(e.key);
      if (!it) {
        it = { key: e.key, side: null, top: null, drawn: null };
        it.tag = document.createElement('div');
        it.tag.className = 'tag';
        it.tag.addEventListener('click', (ev) => {
          if (it.key !== openKey && !ev.target.closest('button, textarea, a')) open(it.key, true);
        });
        it.dot = document.createElement('button');
        it.dot.addEventListener('click', () => open(it.key, true));
        it.dot.hidden = true;
        it.line = document.createElementNS(SVG, 'line');
        it.line.style.display = 'none';
        lines.append(it.line);
        dots.append(it.dot);
        items.set(e.key, it);
        if (e.open) openKey = e.key;
      }
      it.entry = e;
      it.dot.className = `pinDot tagDot ${e.dotClass || ''}`;
      it.dot.textContent = e.dot;
      it.dot.title = e.title || '';
      (narrow ? list : tags).append(it.tag);
      draw(it);
    }
    restack();
  }

  function open(key, go = false) {
    openKey = key;
    for (const it of items.values()) draw(it);
    restack();
    if (go && onOpen) onOpen(key);
  }
  function close() {
    openKey = null;
    for (const it of items.values()) draw(it);
    restack();
  }

  // The viewer's word on where the points are, at the end of the frame that moved them.
  function place(points) {
    for (const p of points) where.set(p.key, p);
    for (const it of items.values()) {
      const p = where.get(it.key);
      it.dot.hidden = !(p && p.shown);
      if (p && p.shown) {
        it.dot.style.transform = `translate(${p.x}px, ${p.y}px)`;
        it.dot.classList.toggle('away', p.away);
      }
    }
    drawLines();
    clearTimeout(timer);
    timer = setTimeout(restack, SETTLE);
  }

  function drawLines() {
    const w = stage.clientWidth, g = gutter();
    for (const it of items.values()) {
      const p = where.get(it.key);
      const on = !narrow && p && p.shown && it.top !== null;
      it.line.style.display = on ? '' : 'none';
      if (!on) continue;
      const x2 = it.side === 'left' ? g - 6 : w - g + 6;
      it.line.setAttribute('x1', p.x); it.line.setAttribute('y1', p.y);
      it.line.setAttribute('x2', x2); it.line.setAttribute('y2', it.top + 16);
      it.line.classList.toggle('away', p.away);
    }
  }

  // Each tag on its point's side, in order of its point's height, clear of the others.
  function restack() {
    if (narrow) { drawLines(); return; }
    const w = stage.clientWidth, h = stage.clientHeight, g = gutter(), mid = w / 2;
    const sides = { left: [], right: [] };
    for (const it of items.values()) {
      const p = where.get(it.key);
      const x = p && p.shown ? p.x : mid - 1;
      if (!it.side) it.side = x < mid ? 'left' : 'right';
      else if (it.side === 'left' && x > mid + SWAP) it.side = 'right';
      else if (it.side === 'right' && x < mid - SWAP) it.side = 'left';
      sides[it.side].push({ it, y: p && p.shown ? p.y : (it.top ?? h) + 16 });
    }
    for (const [side, stack] of Object.entries(sides)) {
      stack.sort((a, b) => a.y - b.y);
      for (const s of stack) {
        s.it.tag.style.width = `${g - 18}px`;
        s.h = s.it.tag.offsetHeight;
      }
      let y = TOP;
      for (const s of stack) {
        s.top = Math.max(y, s.y - 16);
        y = s.top + s.h + GAP;
      }
      let bottom = h - FOOT;  // pushed up from the bottom when they run past it
      for (let k = stack.length - 1; k >= 0; k--) {
        const s = stack[k];
        if (s.top + s.h > bottom) s.top = Math.max(TOP, bottom - s.h);
        bottom = s.top - GAP;
      }
      for (const s of stack) {
        s.it.top = s.top;
        s.it.tag.style.transform = `translate(${side === 'left' ? 10 : w - g + 8}px, ${s.top}px)`;
      }
    }
    drawLines();
  }

  narrowQuery.addEventListener('change', () => {
    narrow = narrowQuery.matches;
    for (const it of items.values()) (narrow ? list : tags).append(it.tag);
    restack();
  });

  return { set, place, close, restack, get openKey() { return openKey; } };
}
