// The Lab's skin in its address (?skin=), which the car and the UV map room open, and the way back
// to the viewer.

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
