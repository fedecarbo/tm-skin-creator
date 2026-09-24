# TSC_IceCreamSweet

Checkpoint 7, the user's first skin (2026-09-24, on Fable 5.1). The user: "How about an ice cream truck theme?"

- Read as: the sweets rather than the truck. Pastel mint body with cones, lollies and three-scoop
  cones sprinkled over it as whole stickers, a candy-stripe nose, pink wheels.
- Shown together with TSC_IceCreamTruck as two takes.
- Change 1 (user): "the items are not scattered equally... clusters of the same ice cream in an
  area... certain areas have a vast amount of space with no ice cream. It happens in past cars
  as well." Fixed in the sprinkling itself (tool/paintbox.py scatter): each copy takes the
  picture least used among its neighbours, a copy that doesn't fit is nudged, turned and shrunk
  before it's given up, and a second pass fills bare patches with smaller copies. Spacing 18.
- The user chose this one over TSC_IceCreamTruck ("TSC_IceCreamSweet", 2026-09-24). Installed
  in the game the same evening for an in-game look; not yet judged in the game.
- Change 2 (user, from F12 screenshots in the game's skin editor, close up): "Definitely
  pixelated." Two causes, both in the tool: stickers and lettering were sampled one pixel per
  texel (aliased outlines: fixed in tool/paint.py, the picture is filtered to the texel pitch
  and sampled bilinearly), and Pillow's BC1 encoder put fringes round every edge (fixed in
  tool/dds.py with our own refined encoder, 5 dB better). Reinstalled.
- Change 3 (user, screenshot of the nose): "the stripes are soft on the edges, as in not
  sharp." The paint box feathered every shape's edge over 1.5 cm (15 texels); now 0.2 cm
  (tool/shapes.py SOFT). Reinstalled.
