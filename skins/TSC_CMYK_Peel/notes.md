# TSC_CMYK_Peel

Checkpoint 7's comparison round, on Opus 5.5 (2026-09-24). The user: "You know the cmyk car I
made? I wonder if you can make the body of the car as if the skin is peeling off and it reveals
cmyk color. Does that make sense?"

- Read as: TSC_Stealth_CMYK_Bold (installed) with its matte black body as a wrap coming off.
  Underneath, glossy cyan > magenta > yellow along the car (the black on top is the K). Torn
  patches drawn in 3D, and a few strips folded back showing the wrap's pale back
  (tool/peel.py, new: `Skin.keep()` and `Skin.peel()`).
- Rounds before showing (Claude's own, not shown): the first tears were fractal noise and read
  as spray paint, and the first flaps as two-tone capsules. Now: faceted noise for torn edges
  (straight runs, sharp corners, no specks); flaps placed by the tool on the tears' edges,
  folded along a slanted straight fold with a curl, only where the whole flap lies on open
  bodywork; tears thin out near the number and name panels instead of being cut along them;
  the colour underneath is satin (gloss flashed white in the light).
- Shown 2026-09-24 as two takes: this one (about a fifth torn, 5 flaps) and
  TSC_CMYK_Peel_More (about 40 % torn, bigger tears and flaps). Picture:
  build/TSC_CMYK_Peel_compare.png.
- Change 1 (user, from the viewer): "the large paper fold does not work in this case because you
  can tell it's not as 3d... it just looks flat. Also the edges of the torn paper are not
  crisp, they are actually soft... I would remove the paper fold, at least in large, and make
  the edges of the torn sharper." The folds are gone, and so are the shadow inside each tear
  and the light bevel on the wrap's edge, which were what made the edges look soft. The cut is
  now a hard one-texel step (checked on the texture). tool/peel.py cut down to the tears.
- Change 2 (user): "Can you remove the black tape. Also, you could add a bit of 3d so it looks
  like a slight layer on top, just try to make it crispier. But it looks good." "Black tape"
  read as the glossy black seam lines inherited from the stealth base (the user's word for
  them since TSC_Seams_Black): gone (`stealth_base(s, seams=False)`). The layer: a hard-edged
  shadow 0.5 cm wide inside each tear on the side away from a painted light (above, ahead,
  left), and a 1 mm lit hairline on the wrap's opposite edges; no fades. Picture:
  build/TSC_CMYK_Peel_round3b.png.
- Change 3 (user): "I would shorten the shadow... also the angle of the shadow I think it might
  need to be a bit more neutral because when the camera is on rear it doesn't look 3d." The
  shadow is now the same width all round every tear (a light from straight above), 2.5 mm
  instead of 5, still hard-edged; the lit hairline went with the directional light. Picture:
  build/TSC_CMYK_Peel_round4.png.
- Change 4 (user): "maybe the sidepod frame needs to be black no?" Yes: the ring round each
  sidepod inlet (and its strip along the sidepod's foot) is now matte black like the wrap, so
  the colour comes only through the tears; the glowing grille keeps its colours. Picture:
  build/TSC_CMYK_Peel_round5.png.
