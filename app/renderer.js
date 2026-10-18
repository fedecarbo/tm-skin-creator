// The page: the Lab in an iframe once its server answers; Claude in an xterm wired to the pty.
const left = document.getElementById("left");
const right = document.getElementById("right");
const divider = document.getElementById("divider");
const shade = document.getElementById("shade");

const t = new Terminal({
  cursorBlink: true, fontSize: 13, fontFamily: "Menlo, SF Mono, Monaco, monospace", scrollback: 5000,
  allowProposedApi: true, macOptionIsMeta: true,
  theme: { background: "#111214", foreground: "#dcdcdc", cursor: "#dcdcdc", selectionBackground: "#3a4a6a" },
});
const fit = new FitAddon.FitAddon();
t.loadAddon(fit);
t.open(document.getElementById("term"));
fit.fit();

let running = false;
function start() {
  running = true;
  window.term.start({ cols: t.cols, rows: t.rows });
}
window.term.onData((d) => t.write(d));
window.term.onExit((code) => {
  running = false;
  t.write(`\r\n\x1b[90mClaude ended (${code}). Press Enter to start it again.\x1b[0m\r\n`);
});
t.onData((d) => { if (running) window.term.write(d); else if (d === "\r") { t.clear(); start(); } });
t.onResize(({ cols, rows }) => window.term.resize({ cols, rows }));
new ResizeObserver(() => fit.fit()).observe(right);
start();
t.focus();

// The divider: drag it; the shade keeps the iframe from eating the pointer while dragging.
let dragging = false;
divider.addEventListener("pointerdown", (e) => { dragging = true; divider.classList.add("on"); shade.style.display = "block"; divider.setPointerCapture(e.pointerId); });
divider.addEventListener("pointermove", (e) => {
  if (!dragging) return;
  const w = Math.min(Math.max(e.clientX, 380), window.innerWidth - 380);
  left.style.flexBasis = `${w}px`;
});
divider.addEventListener("pointerup", () => { dragging = false; divider.classList.remove("on"); shade.style.display = "none"; fit.fit(); });

// The Lab, once its server is up.
(async () => {
  const ok = await window.lab.ready();
  const waiting = document.getElementById("waiting");
  if (!ok) { waiting.textContent = "The Lab's server didn't start. See server.log in the work folder, or ask Claude on the right."; return; }
  const f = document.createElement("iframe");
  f.src = await window.lab.url();
  f.allow = "clipboard-read; clipboard-write";
  left.insertBefore(f, shade);
  waiting.remove();
})();
